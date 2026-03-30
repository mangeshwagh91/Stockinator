"""Mean-reversion strategy implementation."""
from typing import Dict

from app.services.strategies.base import StrategyResult


def evaluate(features: Dict[str, float], sentiment_score: float = 0.0) -> StrategyResult:
    """Evaluate mean-reversion conditions and produce a strategy score."""
    rsi = float(features.get("rsi", 50.0))
    bollinger_position = float(features.get("bollinger_position", 0.5))

    score = 50.0
    direction = "HOLD"
    reason = "No mean-reversion edge"

    if rsi <= 32 and bollinger_position <= 0.15:
        score += 22.0
        direction = "BUY"
        reason = "Oversold conditions near lower band"
    elif rsi >= 68 and bollinger_position >= 0.85:
        score += 22.0
        direction = "SELL"
        reason = "Overbought conditions near upper band"
    elif 40 <= rsi <= 60:
        score -= 8.0

    score -= max(-4.0, min(4.0, sentiment_score * 4.0))

    return StrategyResult(
        name="mean_reversion",
        score=score,
        direction=direction,
        reason=reason,
        metadata={
            "rsi": rsi,
            "bollinger_position": bollinger_position,
        },
    )
