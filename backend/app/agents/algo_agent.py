"""Algo agent: technical indicators + candlestick pattern detection.

Wires to indicator_service.py for the heavy calculations and adds
6 candlestick pattern detectors (manual implementation, no TA-Lib needed).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from app.services.indicator_service import indicator_service

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
        if len(candles) < 30:
            return IndicatorConsensus(symbol=symbol, score=50, bullish_count=0,
                                     bearish_count=0, neutral_count=0)

        # Convert candles to DataFrame for indicator_service
        df = pd.DataFrame(candles)
        if "time" in df.columns:
            df["timestamp"] = pd.to_datetime(df["time"])
            df.set_index("timestamp", inplace=True)
            df.drop(columns=["time"], inplace=True)

        closes = df["close"].values
        highs = df["high"].values
        lows = df["low"].values
        opens = df["open"].values

        # Calculate indicators via service
        try:
            df_ind = indicator_service.calculate_all_indicators(df)
            indicators = indicator_service.extract_latest_features(df_ind)
            indicators["last_close"] = float(closes[-1])
        except Exception as e:
            print(f"Indicator calculation failed: {e}")
            indicators = {"last_close": float(closes[-1])}

        # Detect patterns manually
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

        # Bollinger position (0 to 1)
        bb_pos = ind.get("bollinger_position", 0.5)
        if bb_pos <= 0.05:
            bullish += 1
        elif bb_pos >= 0.95:
            bearish += 1
        else:
            neutral += 1

        # Stochastic
        sk = ind.get("stochastic_k", 50)
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
