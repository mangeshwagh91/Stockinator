"""Algo agent: technical indicators + candlestick pattern detection.

Wires to indicator_service.py for the heavy calculations and adds
6 candlestick pattern detectors (manual implementation, no TA-Lib needed).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import numpy as np


@dataclass
class IndicatorConsensus:
    symbol: str
    score: float                     # 0-100 consensus score
    bullish_count: int
    bearish_count: int
    neutral_count: int
    indicators: Dict[str, Any] = field(default_factory=dict)
    patterns: List[str] = field(default_factory=list)


class AlgoAgent:
    """Computes indicator consensus + candlestick patterns from OHLCV candles."""

    name = "algo-agent"

    # ── Main entry point ─────────────────────────────────────────────────

    def compute_consensus(self, symbol: str, candles: List[Dict]) -> IndicatorConsensus:
        """Accept raw OHLCV candles, compute indicators and candlestick patterns,
        return a single consensus score."""
        if len(candles) < 26:
            return IndicatorConsensus(symbol=symbol, score=50, bullish_count=0,
                                     bearish_count=0, neutral_count=0)

        closes = np.array([c["close"] for c in candles], dtype=float)
        highs = np.array([c["high"] for c in candles], dtype=float)
        lows = np.array([c["low"] for c in candles], dtype=float)
        opens = np.array([c["open"] for c in candles], dtype=float)
        volumes = np.array([c.get("volume", 0) for c in candles], dtype=float)

        indicators = self._compute_indicators(closes, highs, lows, volumes)
        patterns = self._detect_patterns(opens, highs, lows, closes)

        bullish, bearish, neutral = self._classify_signals(indicators)
        # Add pattern counts
        bull_patterns = [p for p in patterns if "Bullish" in p]
        bear_patterns = [p for p in patterns if "Bearish" in p]
        bullish += len(bull_patterns)
        bearish += len(bear_patterns)

        total = max(1, bullish + bearish + neutral)
        score = max(0.0, min(100.0, (bullish / total) * 100.0))

        return IndicatorConsensus(
            symbol=symbol,
            score=round(score, 1),
            bullish_count=bullish,
            bearish_count=bearish,
            neutral_count=neutral,
            indicators=indicators,
            patterns=patterns,
        )

    # ── Technical Indicators ─────────────────────────────────────────────

    def _compute_indicators(self, closes, highs, lows, volumes) -> Dict[str, Any]:
        ind: Dict[str, Any] = {}

        # SMA
        ind["sma_20"] = round(float(np.mean(closes[-20:])), 2) if len(closes) >= 20 else None
        ind["sma_50"] = round(float(np.mean(closes[-50:])), 2) if len(closes) >= 50 else None

        # EMA
        ind["ema_12"] = round(float(self._ema(closes, 12)[-1]), 2)
        ind["ema_26"] = round(float(self._ema(closes, 26)[-1]), 2)

        # RSI
        ind["rsi"] = round(self._rsi(closes, 14), 2)

        # MACD
        ema12 = self._ema(closes, 12)
        ema26 = self._ema(closes, 26)
        macd_line = ema12 - ema26
        signal_line = self._ema(macd_line, 9)
        ind["macd"] = round(float(macd_line[-1]), 2)
        ind["macd_signal"] = round(float(signal_line[-1]), 2)
        ind["macd_hist"] = round(float(macd_line[-1] - signal_line[-1]), 2)

        # Bollinger Bands
        if len(closes) >= 20:
            sma20 = np.mean(closes[-20:])
            std20 = np.std(closes[-20:])
            ind["bb_upper"] = round(float(sma20 + 2 * std20), 2)
            ind["bb_lower"] = round(float(sma20 - 2 * std20), 2)
            ind["bb_width"] = round(float(4 * std20 / sma20 * 100), 2)

        # ATR
        ind["atr"] = round(self._atr(highs, lows, closes, 14), 2)

        # Stochastic
        if len(closes) >= 14:
            low14 = np.min(lows[-14:])
            high14 = np.max(highs[-14:])
            k = ((closes[-1] - low14) / (high14 - low14) * 100) if high14 != low14 else 50
            ind["stoch_k"] = round(float(k), 2)

        # Williams %R
        if len(closes) >= 14:
            highest = np.max(highs[-14:])
            lowest = np.min(lows[-14:])
            wr = ((highest - closes[-1]) / (highest - lowest) * -100) if highest != lowest else -50
            ind["williams_r"] = round(float(wr), 2)

        # CCI
        if len(closes) >= 20:
            tp = (highs[-20:] + lows[-20:] + closes[-20:]) / 3
            sma_tp = np.mean(tp)
            mean_dev = np.mean(np.abs(tp - sma_tp))
            cci = (tp[-1] - sma_tp) / (0.015 * mean_dev) if mean_dev != 0 else 0
            ind["cci"] = round(float(cci), 2)

        # OBV
        obv = 0
        for i in range(1, len(closes)):
            if closes[i] > closes[i - 1]:
                obv += volumes[i]
            elif closes[i] < closes[i - 1]:
                obv -= volumes[i]
        ind["obv"] = int(obv)

        # ADX (simplified)
        ind["adx"] = round(self._adx(highs, lows, closes, 14), 2)

        # Price vs SMA
        if ind["sma_20"]:
            ind["price_to_sma20"] = round(float(closes[-1] / ind["sma_20"]), 4)

        ind["last_close"] = round(float(closes[-1]), 2)

        return ind

    # ── Candlestick Patterns (6 patterns) ────────────────────────────────

    def _detect_patterns(self, opens, highs, lows, closes) -> List[str]:
        """Detect 6 candlestick patterns: 3 bullish + 3 bearish."""
        patterns = []
        if len(closes) < 3:
            return patterns

        o, h, l, c = opens[-1], highs[-1], lows[-1], closes[-1]
        o1, h1, l1, c1 = opens[-2], highs[-2], lows[-2], closes[-2]
        o2, h2, l2, c2 = opens[-3], highs[-3], lows[-3], closes[-3]
        body = abs(c - o)
        body1 = abs(c1 - o1)
        avg_body = np.mean(np.abs(closes[-10:] - opens[-10:])) or 1

        # 1. Hammer (Bullish)
        lower_wick = min(o, c) - l
        upper_wick = h - max(o, c)
        if lower_wick > 2 * body and upper_wick < body * 0.5 and c1 < o1:
            patterns.append("Bullish Hammer")

        # 2. Bullish Engulfing
        if c1 < o1 and c > o and o <= c1 and c >= o1 and body > body1:
            patterns.append("Bullish Engulfing")

        # 3. Morning Star (3-candle)
        if c2 < o2 and body1 < avg_body * 0.3 and c > o and c > (o2 + c2) / 2:
            patterns.append("Bullish Morning Star")

        # 4. Shooting Star (Bearish)
        if upper_wick > 2 * body and lower_wick < body * 0.5 and c1 > o1:
            patterns.append("Bearish Shooting Star")

        # 5. Bearish Engulfing
        if c1 > o1 and c < o and o >= c1 and c <= o1 and body > body1:
            patterns.append("Bearish Engulfing")

        # 6. Evening Star (3-candle)
        if c2 > o2 and body1 < avg_body * 0.3 and c < o and c < (o2 + c2) / 2:
            patterns.append("Bearish Evening Star")

        # Bonus: Doji
        if body < avg_body * 0.1:
            patterns.append("Doji")

        return patterns

    # ── Signal classification ────────────────────────────────────────────

    def _classify_signals(self, ind: Dict) -> tuple:
        bullish = 0
        bearish = 0
        neutral = 0

        # RSI
        rsi = ind.get("rsi", 50)
        if rsi < 30:
            bullish += 1  # oversold = buy signal
        elif rsi > 70:
            bearish += 1
        else:
            neutral += 1

        # MACD
        if ind.get("macd", 0) > ind.get("macd_signal", 0):
            bullish += 1
        else:
            bearish += 1

        # Price vs SMA
        ratio = ind.get("price_to_sma20", 1.0)
        if ratio > 1.02:
            bullish += 1
        elif ratio < 0.98:
            bearish += 1
        else:
            neutral += 1

        # Bollinger
        close = ind.get("last_close", 0)
        if close and ind.get("bb_lower") and close <= ind["bb_lower"]:
            bullish += 1
        elif close and ind.get("bb_upper") and close >= ind["bb_upper"]:
            bearish += 1
        else:
            neutral += 1

        # Stochastic
        sk = ind.get("stoch_k", 50)
        if sk < 20:
            bullish += 1
        elif sk > 80:
            bearish += 1
        else:
            neutral += 1

        # Williams %R
        wr = ind.get("williams_r", -50)
        if wr < -80:
            bullish += 1
        elif wr > -20:
            bearish += 1
        else:
            neutral += 1

        # CCI
        cci = ind.get("cci", 0)
        if cci < -100:
            bullish += 1
        elif cci > 100:
            bearish += 1
        else:
            neutral += 1

        # ADX trend strength
        adx = ind.get("adx", 20)
        if adx > 25:
            bullish += 1  # strong trend
        else:
            neutral += 1

        return bullish, bearish, neutral

    # ── Helper math ──────────────────────────────────────────────────────

    @staticmethod
    def _ema(data, period):
        arr = np.array(data, dtype=float)
        k = 2 / (period + 1)
        ema = np.zeros_like(arr)
        ema[0] = arr[0]
        for i in range(1, len(arr)):
            ema[i] = arr[i] * k + ema[i - 1] * (1 - k)
        return ema

    @staticmethod
    def _rsi(closes, period=14):
        if len(closes) < period + 1:
            return 50.0
        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return float(100 - 100 / (1 + rs))

    @staticmethod
    def _atr(highs, lows, closes, period=14):
        if len(closes) < period + 1:
            return float(np.mean(highs - lows))
        tr = np.maximum(
            highs[1:] - lows[1:],
            np.maximum(
                np.abs(highs[1:] - closes[:-1]),
                np.abs(lows[1:] - closes[:-1])
            ),
        )
        return float(np.mean(tr[-period:]))

    @staticmethod
    def _adx(highs, lows, closes, period=14):
        if len(closes) < period + 2:
            return 20.0
        plus_dm = np.maximum(highs[1:] - highs[:-1], 0)
        minus_dm = np.maximum(lows[:-1] - lows[1:], 0)
        # Zero out where not dominant
        mask = plus_dm > minus_dm
        plus_dm[~mask] = 0
        minus_dm[mask] = 0
        tr = np.maximum(
            highs[1:] - lows[1:],
            np.maximum(np.abs(highs[1:] - closes[:-1]), np.abs(lows[1:] - closes[:-1]))
        )
        atr = np.mean(tr[-period:]) or 1
        plus_di = np.mean(plus_dm[-period:]) / atr * 100
        minus_di = np.mean(minus_dm[-period:]) / atr * 100
        dx = abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9) * 100
        return float(dx)
