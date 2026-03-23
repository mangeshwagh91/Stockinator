"""Trend-following strategy implementation."""
from typing import Dict

from app.services.strategies.base import StrategyResult


def evaluate(features: Dict[str, float], sentiment_score: float = 0.0) -> StrategyResult:
    """Evaluate trend-following conditions and produce a strategy score."""
    adx = float(features.get("adx", 25.0))
    macd = float(features.get("macd", 0.0))
    macd_signal = float(features.get("macd_signal", 0.0))
    price_to_sma20 = float(features.get("price_to_sma20", 1.0))

    score = 50.0
    direction = "HOLD"
    reason = "No clear trend"

    if adx >= 20:
        score += min(18.0, (adx - 20.0) * 0.9)

    if macd > macd_signal and price_to_sma20 >= 1.0:
        score += 15.0
        direction = "BUY"
        reason = "Bullish momentum with trend strength"
    elif macd < macd_signal and price_to_sma20 < 1.0:
        score += 15.0
        direction = "SELL"
        reason = "Bearish momentum with trend strength"

    score += max(-5.0, min(5.0, sentiment_score * 5.0))

    return StrategyResult(
        name="trend_following",
        score=score,
        direction=direction,
        reason=reason,
        metadata={
            "adx": adx,
            "macd_spread": macd - macd_signal,
            "price_to_sma20": price_to_sma20,
        },
    )
