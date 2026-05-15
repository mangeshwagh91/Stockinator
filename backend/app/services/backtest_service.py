"""Backtesting service: evaluates agent signals against historical data.

Usage:
    from app.services.backtest_service import BacktestService
    bt = BacktestService()
    result = bt.run("RELIANCE.NS", period="1y")
    print(result)  # BacktestResult(sharpe, win_rate, max_drawdown, equity_curve)
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Trade:
    entry_date: str
    exit_date: str
    direction: str        # BUY / SELL
    entry_price: float
    exit_price: float
    pnl_pct: float
    win: bool

@dataclass
class BacktestResult:
    symbol: str
    period: str
    sharpe: float
    win_rate: float          # 0-100 %
    max_drawdown: float      # % (negative)
    total_return: float      # %
    n_trades: int
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    daily_returns: List[float] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "period": self.period,
            "sharpe": round(self.sharpe, 3),
            "win_rate": round(self.win_rate, 2),
            "max_drawdown": round(self.max_drawdown, 2),
            "total_return": round(self.total_return, 2),
            "n_trades": self.n_trades,
            "equity_curve": [round(v, 4) for v in self.equity_curve],
            "trades": [
                {
                    "entry_date": t.entry_date, "exit_date": t.exit_date,
                    "direction": t.direction, "entry_price": t.entry_price,
                    "exit_price": t.exit_price, "pnl_pct": round(t.pnl_pct, 3),
                    "win": t.win,
                }
                for t in self.trades
            ],
            "error": self.error,
        }


# ─────────────────────────────────────────────────────────────────────────────

class BacktestService:
    """
    Signal-replay backtester.

    Strategy: Re-generates AlgoAgent + PredictionAgent signals on each
    historical bar, enters a position when success_score > threshold,
    holds for `hold_days`, exits at market open the next day.
    """

    def __init__(self, threshold: float = 60.0, hold_days: int = 5,
                 stop_loss_pct: float = 2.0, take_profit_pct: float = 4.0):
        self.threshold = threshold
        self.hold_days = hold_days
        self.sl_pct = stop_loss_pct
        self.tp_pct = take_profit_pct

    # ── Public API ────────────────────────────────────────────────────────────

    def run(self, symbol: str, period: str = "1y") -> BacktestResult:
        """Download data, replay signals, compute metrics."""
        df = self._download(symbol, period)
        if df is None or len(df) < 60:
            return BacktestResult(symbol=symbol, period=period,
                                  sharpe=0, win_rate=0, max_drawdown=0,
                                  total_return=0, n_trades=0,
                                  error="Insufficient data")
        try:
            signals = self._generate_signals(df)
            trades = self._simulate_trades(df, signals)
            return self._compute_metrics(symbol, period, df, trades)
        except Exception as exc:
            logger.exception(f"Backtest failed for {symbol}")
            return BacktestResult(symbol=symbol, period=period,
                                  sharpe=0, win_rate=0, max_drawdown=0,
                                  total_return=0, n_trades=0,
                                  error=str(exc))

    def run_portfolio(self, symbols: List[str], period: str = "1y") -> Dict[str, Any]:
        """Run backtest for multiple symbols and aggregate."""
        results = []
        for sym in symbols:
            r = self.run(sym, period)
            results.append(r.to_dict())

        valid = [r for r in results if r["error"] is None]
        if not valid:
            return {"results": results, "aggregate": {}}

        agg = {
            "avg_sharpe": round(np.mean([r["sharpe"] for r in valid]), 3),
            "avg_win_rate": round(np.mean([r["win_rate"] for r in valid]), 2),
            "avg_max_drawdown": round(np.mean([r["max_drawdown"] for r in valid]), 2),
            "avg_total_return": round(np.mean([r["total_return"] for r in valid]), 2),
            "total_trades": sum(r["n_trades"] for r in valid),
            "symbols_tested": len(valid),
        }
        return {"results": results, "aggregate": agg}

    # ── Download ──────────────────────────────────────────────────────────────

    def _download(self, symbol: str, period: str) -> Optional[pd.DataFrame]:
        try:
            # Normalize to Yahoo format
            if not symbol.endswith(".NS") and not symbol.endswith(".BO") and \
               "." not in symbol and "/" not in symbol:
                symbol = symbol + ".NS"

            df = yf.download(symbol, period=period, interval="1d",
                             auto_adjust=True, progress=False)
            if df.empty:
                return None
            df.columns = [c.lower() for c in df.columns]
            df = df[["open", "high", "low", "close", "volume"]].dropna()
            return df
        except Exception as exc:
            logger.warning(f"Download failed for {symbol}: {exc}")
            return None

    # ── Signal generation ─────────────────────────────────────────────────────

    def _generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        Compute a simplified success_score for each bar using rule-based
        indicators (mirrors PredictionAgent's fallback logic).
        Returns a Series of scores (0-100), index aligned to df.
        """
        c = df["close"]
        scores = pd.Series(50.0, index=df.index)

        # RSI
        delta = c.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rsi = 100 - 100 / (1 + gain / (loss + 1e-9))

        # MACD
        fast = c.ewm(span=12, adjust=False).mean()
        slow = c.ewm(span=26, adjust=False).mean()
        macd_line = fast - slow
        signal_line = macd_line.ewm(span=9, adjust=False).mean()

        # SMA
        sma20 = c.rolling(20).mean()
        sma50 = c.rolling(50).mean()

        # ADX (simplified)
        up = df["high"].diff()
        dn = -df["low"].diff()
        plus_dm = up.where((up > dn) & (up > 0), 0.0)
        minus_dm = dn.where((dn > up) & (dn > 0), 0.0)
        tr = pd.concat([
            df["high"] - df["low"],
            (df["high"] - c.shift()).abs(),
            (df["low"] - c.shift()).abs(),
        ], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        plus_di = 100 * plus_dm.rolling(14).mean() / (atr + 1e-9)
        minus_di = 100 * minus_dm.rolling(14).mean() / (atr + 1e-9)
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-9)
        adx = dx.rolling(14).mean()

        # Score components
        rsi_score = pd.Series(0.0, index=df.index)
        rsi_score[rsi < 30] = 15
        rsi_score[(rsi >= 30) & (rsi <= 50)] = 10
        rsi_score[rsi > 70] = -10

        macd_score = pd.Series(10.0, index=df.index)
        macd_score[macd_line <= signal_line] = -5

        trend_score = pd.Series(0.0, index=df.index)
        trend_score[c > sma20] = 8
        trend_score[c < sma20] = -8
        trend_score[sma20 > sma50] += 5

        adx_score = pd.Series(0.0, index=df.index)
        adx_score[adx > 25] = 7

        scores = (50 + rsi_score + macd_score + trend_score + adx_score).clip(0, 100)
        return scores.fillna(50)

    # ── Trade simulation ──────────────────────────────────────────────────────

    def _simulate_trades(self, df: pd.DataFrame, signals: pd.Series) -> List[Trade]:
        trades: List[Trade] = []
        in_trade = False
        entry_idx = 0
        entry_price = 0.0
        direction = "BUY"
        bars = df.reset_index()

        i = 50  # skip warmup
        while i < len(bars) - self.hold_days - 1:
            score = signals.iloc[i]

            if not in_trade and score >= self.threshold:
                entry_price = float(bars.iloc[i + 1]["open"])
                direction = "BUY" if score >= self.threshold else "SELL"
                entry_idx = i + 1
                in_trade = True
                i += 1
                continue

            if in_trade:
                bar = bars.iloc[i]
                high = float(bar["high"])
                low = float(bar["low"])

                # Stop loss / take profit check (intra-bar)
                sl_price = entry_price * (1 - self.sl_pct / 100)
                tp_price = entry_price * (1 + self.tp_pct / 100)
                exit_price = float(bar["close"])
                exited = False

                if direction == "BUY":
                    if low <= sl_price:
                        exit_price = sl_price
                        exited = True
                    elif high >= tp_price:
                        exit_price = tp_price
                        exited = True

                # Time-based exit
                if not exited and (i - entry_idx) >= self.hold_days:
                    exited = True

                if exited:
                    # Safe date resolution: yfinance reset_index gives 'Date' (daily)
                    # or 'Datetime' (intraday) depending on version. Fall back to int index.
                    _date_col = None
                    for _c in ("Date", "Datetime", "date", "datetime", "index"):
                        if _c in bars.columns:
                            _date_col = _c
                            break
                    entry_date = str(bars.iloc[entry_idx][_date_col]) if _date_col else str(entry_idx)
                    exit_date  = str(bar[_date_col]) if _date_col else str(i)
                    pnl = (exit_price / entry_price - 1) * 100
                    trades.append(Trade(
                        entry_date=entry_date,
                        exit_date=exit_date,
                        direction=direction,
                        entry_price=round(entry_price, 2),
                        exit_price=round(exit_price, 2),
                        pnl_pct=round(pnl, 3),
                        win=pnl > 0,
                    ))
                    in_trade = False
            i += 1

        return trades

    # ── Metrics ───────────────────────────────────────────────────────────────

    def _compute_metrics(self, symbol: str, period: str,
                         df: pd.DataFrame, trades: List[Trade]) -> BacktestResult:
        if not trades:
            return BacktestResult(symbol=symbol, period=period,
                                  sharpe=0, win_rate=0, max_drawdown=0,
                                  total_return=0, n_trades=0,
                                  error="No trades generated")

        pnls = np.array([t.pnl_pct for t in trades])
        win_rate = float((pnls > 0).mean() * 100)
        total_return = float(pnls.sum())

        # Equity curve (starting at 100)
        equity = [100.0]
        for p in pnls:
            equity.append(equity[-1] * (1 + p / 100))

        # Max drawdown
        eq = np.array(equity)
        peak = np.maximum.accumulate(eq)
        drawdown = (eq - peak) / peak * 100
        max_dd = float(drawdown.min())

        # Sharpe (annualized, assume ~52 trades/year approx)
        if pnls.std() > 0:
            sharpe = float((pnls.mean() / pnls.std()) * np.sqrt(252 / max(self.hold_days, 1)))
        else:
            sharpe = 0.0

        # Daily returns from equity curve (for extra analytics)
        daily_rets = list(np.diff(eq) / eq[:-1] * 100)

        return BacktestResult(
            symbol=symbol,
            period=period,
            sharpe=round(sharpe, 3),
            win_rate=round(win_rate, 2),
            max_drawdown=round(max_dd, 2),
            total_return=round(total_return, 2),
            n_trades=len(trades),
            trades=trades,
            equity_curve=equity,
            daily_returns=daily_rets,
        )


# ── Global singleton ──────────────────────────────────────────────────────────
backtest_service = BacktestService()


# ── Quick CLI test ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    symbols = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
    print("Running portfolio backtest…")
    bt = BacktestService(threshold=60.0, hold_days=5)
    report = bt.run_portfolio(symbols, period="1y")
    import json
    print(json.dumps(report["aggregate"], indent=2))
    for r in report["results"]:
        print(f"  {r['symbol']:20s}  Sharpe={r['sharpe']:6.3f}  WinRate={r['win_rate']:5.1f}%  "
              f"MaxDD={r['max_drawdown']:6.2f}%  Return={r['total_return']:6.2f}%  Trades={r['n_trades']}")
