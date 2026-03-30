"""
EMA Scalping Strategy (9 & 15 EMA Crossover)
Based on the video strategy by Mayank Singh.

Strategy Rules:
- Uses two EMAs: 9-period and 15-period on a 5-minute chart
- Only trade when EMAs are sloping > 30 degrees (trending market)
- BUY: EMA9 > EMA15, slope up, bullish entry candle touching/crossing EMA
- SELL: EMA9 < EMA15, slope down, bearish entry candle touching/crossing EMA
- Strike selection: ATM or 1-strike ITM options
- Stop Loss: Low of the entry candle (for buys) / High (for sells)
- Target: 1:2 Risk-Reward ratio
- Dual index confirmation: Check both Nifty and Bank Nifty
"""

import math
from dataclasses import dataclass, field
from typing import Literal

import numpy as np
import pandas as pd


# ─────────────────────────────────────────────
# Data Types
# ─────────────────────────────────────────────

@dataclass
class Candle:
    timestamp: pd.Timestamp
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


@dataclass
class TradeSignal:
    direction: Literal["BUY", "SELL", "NO_TRADE"]
    entry_price: float = 0.0
    stop_loss: float = 0.0
    target: float = 0.0
    risk: float = 0.0
    reward: float = 0.0
    reason: str = ""
    entry_candle_type: str = ""


@dataclass
class TradeResult:
    signal: TradeSignal
    outcome: Literal["TARGET_HIT", "SL_HIT", "OPEN"] = "OPEN"
    pnl: float = 0.0


# ─────────────────────────────────────────────
# EMA Calculation
# ─────────────────────────────────────────────

def compute_ema(prices: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average."""
    return prices.ewm(span=period, adjust=False).mean()


def compute_slope_degrees(series: pd.Series, lookback: int = 5) -> pd.Series:
    """
    Approximate slope of an EMA series in degrees.
    Uses the angle of linear regression over the last `lookback` candles.
    """
    slopes = pd.Series(index=series.index, dtype=float)
    for i in range(lookback, len(series)):
        y = series.iloc[i - lookback : i].values
        x = np.arange(lookback)
        # Linear regression slope
        slope = np.polyfit(x, y, 1)[0]
        # Normalize: assume each candle unit = 1 price unit on y, 1 bar on x
        angle = math.degrees(math.atan(slope / max(y.mean(), 1) * 100))
        slopes.iloc[i] = abs(angle)
    return slopes.fillna(0)


# ─────────────────────────────────────────────
# Entry Candle Detection
# ─────────────────────────────────────────────

def detect_pin_bar(candle: Candle) -> bool:
    """
    Pin bar / hammer: small body, long lower wick.
    Lower wick > 2x body size; body in upper third.
    """
    body = abs(candle.close - candle.open)
    lower_wick = min(candle.open, candle.close) - candle.low
    upper_wick = candle.high - max(candle.open, candle.close)
    total_range = candle.high - candle.low
    if total_range == 0:
        return False
    return (lower_wick > 2 * body) and (lower_wick > upper_wick) and (body / total_range < 0.35)


def detect_big_body_bullish(candle: Candle) -> bool:
    """Strong bullish candle: body is > 60% of total range, closes near high."""
    total_range = candle.high - candle.low
    if total_range == 0:
        return False
    body = candle.close - candle.open
    body_ratio = body / total_range
    return (body > 0) and (body_ratio >= 0.6)


def detect_bullish_engulfing(candle: Candle, prev_candle: Candle) -> bool:
    """Bullish engulfing: current bullish body engulfs previous bearish body."""
    prev_bearish = prev_candle.close < prev_candle.open
    curr_bullish = candle.close > candle.open
    engulfs = (candle.open <= prev_candle.close) and (candle.close >= prev_candle.open)
    return prev_bearish and curr_bullish and engulfs


def detect_bearish_pin_bar(candle: Candle) -> bool:
    """Shooting star / bearish pin: long upper wick, small body."""
    body = abs(candle.close - candle.open)
    upper_wick = candle.high - max(candle.open, candle.close)
    lower_wick = min(candle.open, candle.close) - candle.low
    total_range = candle.high - candle.low
    if total_range == 0:
        return False
    return (upper_wick > 2 * body) and (upper_wick > lower_wick) and (body / total_range < 0.35)


def detect_big_body_bearish(candle: Candle) -> bool:
    """Strong bearish candle: body > 60% of range, closes near low."""
    total_range = candle.high - candle.low
    if total_range == 0:
        return False
    body = candle.open - candle.close
    body_ratio = body / total_range
    return (body > 0) and (body_ratio >= 0.6)


def detect_bearish_engulfing(candle: Candle, prev_candle: Candle) -> bool:
    """Bearish engulfing: current bearish body engulfs previous bullish body."""
    prev_bullish = prev_candle.close > prev_candle.open
    curr_bearish = candle.close < candle.open
    engulfs = (candle.open >= prev_candle.close) and (candle.close <= prev_candle.open)
    return prev_bullish and curr_bearish and engulfs


# ─────────────────────────────────────────────
# EMA Touch / Cross Detection
# ─────────────────────────────────────────────

def candle_touches_ema(candle: Candle, ema_value: float) -> bool:
    """Check if the candle's range touches the EMA line."""
    return candle.low <= ema_value <= candle.high


def candle_crossed_ema_from_below(candle: Candle, prev_close: float, ema_value: float) -> bool:
    """Price was below EMA and current candle crossed above it."""
    return (prev_close < ema_value) and (candle.close > ema_value)


def candle_crossed_ema_from_above(candle: Candle, prev_close: float, ema_value: float) -> bool:
    """Price was above EMA and current candle crossed below it."""
    return (prev_close > ema_value) and (candle.close < ema_value)


# ─────────────────────────────────────────────
# Dual Index Confirmation
# ─────────────────────────────────────────────

def get_dual_index_confirmation(
    primary_signal: Literal["BUY", "SELL", "NO_TRADE"],
    secondary_ema9: float,
    secondary_ema15: float,
    secondary_slope: float,
    secondary_at_support: bool,
    secondary_at_resistance: bool,
    slope_threshold: float = 30.0,
) -> bool:
    """
    Per the strategy:
    Returns True if secondary index confirms the trade direction.
    """
    if primary_signal == "BUY":
        secondary_bearish = (
            secondary_ema9 < secondary_ema15 and
            secondary_slope >= slope_threshold and
            secondary_at_resistance
        )
        return not secondary_bearish

    elif primary_signal == "SELL":
        secondary_bouncing = (
            secondary_ema9 > secondary_ema15 and
            secondary_at_support
        )
        return not secondary_bouncing

    return False


# ─────────────────────────────────────────────
# Strike Price Selection
# ─────────────────────────────────────────────

def select_strike_price(
    spot_price: float,
    direction: Literal["BUY", "SELL"],
    strike_interval: float = 100.0,
    use_itm: bool = True,
) -> float:
    """
    Select strike price:
    - ATM: round spot to nearest strike interval
    - ITM (recommended): 1 strike below ATM for calls, 1 strike above ATM for puts
    """
    atm_strike = round(spot_price / strike_interval) * strike_interval
    if use_itm:
        if direction == "BUY":
            return atm_strike - strike_interval   # 1 ITM call
        else:
            return atm_strike + strike_interval   # 1 ITM put
    return atm_strike


# ─────────────────────────────────────────────
# Core Signal Generator
# ─────────────────────────────────────────────

def generate_signal(
    candles: list[Candle],
    ema9_series: pd.Series,
    ema15_series: pd.Series,
    slope_series: pd.Series,
    index: int,
    slope_threshold: float = 30.0,
    risk_reward: float = 2.0,
) -> TradeSignal:
    """
    Generate a BUY, SELL, or NO_TRADE signal for the candle at `index`.
    """
    if index < 2:
        return TradeSignal(direction="NO_TRADE", reason="Insufficient data")

    candle = candles[index]
    prev_candle = candles[index - 1]

    ema9 = ema9_series.iloc[index]
    ema15 = ema15_series.iloc[index]
    slope = slope_series.iloc[index]
    prev_close = candles[index - 1].close

    # ── Filter: Must be trending ──────────────────
    if slope < slope_threshold:
        return TradeSignal(direction="NO_TRADE", reason=f"Sideways market (slope={slope:.1f}° < {slope_threshold}°)")

    # ─────────────────────────────────────────────
    # BUY SETUP
    # ─────────────────────────────────────────────
    if ema9 > ema15:
        touches = candle_touches_ema(candle, ema9) or candle_touches_ema(candle, ema15)
        crosses = candle_crossed_ema_from_below(candle, prev_close, ema9)

        candle_type = None
        if detect_pin_bar(candle) and touches:
            candle_type = "pin_bar"
        elif detect_big_body_bullish(candle) and (touches or crosses):
            candle_type = "big_body_bullish"
        elif detect_bullish_engulfing(candle, prev_candle) and (touches or crosses):
            candle_type = "bullish_engulfing"

        if candle_type:
            entry = candle.high
            stop_loss = candle.low
            risk = entry - stop_loss
            target = entry + (risk * risk_reward)
            return TradeSignal(
                direction="BUY",
                entry_price=entry,
                stop_loss=stop_loss,
                target=target,
                risk=risk,
                reward=risk * risk_reward,
                reason="EMA9 > EMA15, trending up, bullish entry candle",
                entry_candle_type=candle_type,
            )

    # ─────────────────────────────────────────────
    # SELL SETUP
    # ─────────────────────────────────────────────
    elif ema9 < ema15:
        touches = candle_touches_ema(candle, ema9) or candle_touches_ema(candle, ema15)
        crosses = candle_crossed_ema_from_above(candle, prev_close, ema9)

        candle_type = None
        if detect_bearish_pin_bar(candle) and touches:
            candle_type = "bearish_pin_bar"
        elif detect_big_body_bearish(candle) and (touches or crosses):
            candle_type = "big_body_bearish"
        elif detect_bearish_engulfing(candle, prev_candle) and (touches or crosses):
            candle_type = "bearish_engulfing"

        if candle_type:
            entry = candle.low
            stop_loss = candle.high
            risk = stop_loss - entry
            target = entry - (risk * risk_reward)
            return TradeSignal(
                direction="SELL",
                entry_price=entry,
                stop_loss=stop_loss,
                target=target,
                risk=risk,
                reward=risk * risk_reward,
                reason="EMA9 < EMA15, trending down, bearish entry candle",
                entry_candle_type=candle_type,
            )

    return TradeSignal(direction="NO_TRADE", reason="No valid entry candle at EMA")


def evaluate_for_registry(features: dict, sentiment_score: float = 0.0):
    """
    Adapter to fit into the standard strategy registry.
    Ideally, `features` will contain last N candles, or pre-computed EMA slopes.
    For now, returns a base StrategyResult based on simple extracted stats if available.
    """
    from app.services.strategies.base import StrategyResult

    # Attempt to extract pre-computed ema9, ema15, and slope from features
    ema9 = features.get("ema9", 0.0)
    ema15 = features.get("ema15", 0.0)
    slope = features.get("ema_slope_deg", 0.0)
    
    score = 50.0
    direction = "HOLD"
    reason = "Insufficient EMA trending data"

    if slope >= 30.0:
        if ema9 > ema15:
            score += 25.0
            direction = "BUY"
            reason = f"EMA Uptrend (slope={slope:.1f}°)"
        elif ema9 < ema15:
            score += 25.0
            direction = "SELL"
            reason = f"EMA Downtrend (slope={slope:.1f}°)"
            
    # Adjust for sentiment
    score += max(-5.0, min(5.0, sentiment_score * 5.0))

    return StrategyResult(
        name="mayank_ema_scalping",
        score=score,
        direction=direction,
        reason=reason,
        metadata={
            "ema9": ema9,
            "ema15": ema15,
            "slope": slope,
        },
    )


# ─────────────────────────────────────────────
# Backtest Engine
# ─────────────────────────────────────────────

def backtest(
    df: pd.DataFrame,
    slope_threshold: float = 30.0,
    risk_reward: float = 2.0,
    use_itm: bool = True,
    strike_interval: float = 100.0,
) -> pd.DataFrame:
    df = df.copy().reset_index(drop=True)

    df["ema9"] = compute_ema(df["close"], 9)
    df["ema15"] = compute_ema(df["close"], 15)
    df["slope"] = compute_slope_degrees(df["ema9"])

    candles = [
        Candle(
            timestamp=row.timestamp,
            open=row.open,
            high=row.high,
            low=row.low,
            close=row.close,
            volume=row.get("volume", 0),
        )
        for row in df.itertuples()
    ]

    results = []
    for i in range(2, len(candles)):
        signal = generate_signal(
            candles, df["ema9"], df["ema15"], df["slope"], i,
            slope_threshold=slope_threshold,
            risk_reward=risk_reward,
        )

        if signal.direction == "NO_TRADE":
            continue

        strike = select_strike_price(
            spot_price=candles[i].close,
            direction=signal.direction,
            strike_interval=strike_interval,
            use_itm=use_itm,
        )

        outcome = "OPEN"
        pnl = 0.0
        for j in range(i + 1, min(i + 20, len(candles))):
            fut = candles[j]
            if signal.direction == "BUY":
                if fut.high >= signal.target:
                    outcome = "TARGET_HIT"
                    pnl = signal.reward
                    break
                elif fut.low <= signal.stop_loss:
                    outcome = "SL_HIT"
                    pnl = -signal.risk
                    break
            else:
                if fut.low <= signal.target:
                    outcome = "TARGET_HIT"
                    pnl = signal.reward
                    break
                elif fut.high >= signal.stop_loss:
                    outcome = "SL_HIT"
                    pnl = -signal.risk
                    break

        results.append({
            "timestamp": candles[i].timestamp,
            "direction": signal.direction,
            "entry_price": round(signal.entry_price, 2),
            "stop_loss": round(signal.stop_loss, 2),
            "target": round(signal.target, 2),
            "risk": round(signal.risk, 2),
            "reward": round(signal.reward, 2),
            "strike": strike,
            "entry_candle": signal.entry_candle_type,
            "reason": signal.reason,
            "outcome": outcome,
            "pnl": round(pnl, 2),
            "ema9": round(df["ema9"].iloc[i], 2),
            "ema15": round(df["ema15"].iloc[i], 2),
            "slope_deg": round(df["slope"].iloc[i], 1),
        })

    return pd.DataFrame(results)


def performance_summary(results_df: pd.DataFrame) -> dict:
    if results_df.empty:
        return {"error": "No trades found"}

    closed = results_df[results_df["outcome"] != "OPEN"]
    wins = closed[closed["outcome"] == "TARGET_HIT"]
    losses = closed[closed["outcome"] == "SL_HIT"]

    total = len(closed)
    win_count = len(wins)
    loss_count = len(losses)
    accuracy = win_count / total * 100 if total > 0 else 0
    total_pnl = closed["pnl"].sum()
    avg_win = wins["pnl"].mean() if not wins.empty else 0
    avg_loss = losses["pnl"].mean() if not losses.empty else 0

    summary = {
        "total_trades": total,
        "wins": win_count,
        "losses": loss_count,
        "accuracy_pct": round(accuracy, 1),
        "total_pnl": round(total_pnl, 2),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "profit_factor": round(wins["pnl"].sum() / abs(losses["pnl"].sum()), 2) if loss_count > 0 else float("inf"),
    }
    return summary


if __name__ == "__main__":
    def generate_sample_data(n: int = 200, seed: int = 42) -> pd.DataFrame:
        np.random.seed(seed)
        timestamps = pd.date_range("2024-01-01 09:15", periods=n, freq="5min")
        close = 44000 + np.cumsum(np.random.randn(n) * 20)
        rows = []
        for i, (ts, c) in enumerate(zip(timestamps, close)):
            spread = abs(np.random.randn() * 15) + 5
            o = c + np.random.randn() * 8
            h = max(o, c) + spread
            l = min(o, c) - spread
            rows.append({"timestamp": ts, "open": o, "high": h, "low": l, "close": c, "volume": np.random.randint(1000, 5000)})
        return pd.DataFrame(rows)

    print("Running EMA Scalping Strategy backtest on sample data...\n")
    df = generate_sample_data(n=300)
    results = backtest(df, slope_threshold=30, risk_reward=2.0, use_itm=True)

    print(f"Signals generated: {len(results)}")
    if not results.empty:
        print("\nFirst 5 signals:")
        print(results[["timestamp", "direction", "entry_price", "stop_loss",
                        "target", "strike", "entry_candle", "outcome", "pnl"]].head().to_string(index=False))

    summary = performance_summary(results)
    for k, v in summary.items():
        print(f"{k}: {v}")
