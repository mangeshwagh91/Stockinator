"""Prediction agent: success scoring from ML, indicators, and sentiment.

Wires to ml_service.py for XGBoost predictions and combines
with algo consensus and news sentiment using the 60/30/10 formula.
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class PredictionResult:
    symbol: str
    success_score: float         # 0-100 combined score
    ml_score: float              # XGBoost component
    algo_score: float            # Indicator consensus component
    news_score: float            # News sentiment component
    confidence_low: float
    confidence_high: float
    direction: str               # "BUY" or "SELL"


class PredictionAgent:
    """Generates a success score: XGBoost 60% + Indicators 30% + News 10%."""

    name = "prediction-agent"

    def predict(
        self,
        symbol: str,
        indicator_features: Dict[str, float],
        algo_consensus_score: float,
        news_sentiment: float,
    ) -> PredictionResult:
        """
        Compute the combined success score.

        Args:
            symbol: Trading symbol
            indicator_features: Dict of indicator values for ML model input
            algo_consensus_score: 0-100 from AlgoAgent
            news_sentiment: 0-100 from ScrapingAgent news
        """
        # 1. Get ML prediction (XGBoost or fallback)
        try:
            from app.services.ml_service import ml_service
            # news_sentiment for ml_service is -1 to 1, convert:
            ml_sentiment = (news_sentiment - 50) / 50  # map 0-100 → -1 to 1
            ml_score = ml_service.predict_success_score(indicator_features, ml_sentiment)
        except Exception:
            ml_score = self._simple_ml_fallback(indicator_features)

        # 2. Combine: XGBoost 60% + Indicators 30% + News 10%
        success_score = (
            ml_score * 0.60
            + algo_consensus_score * 0.30
            + news_sentiment * 0.10
        )
        bounded = max(0.0, min(100.0, success_score))

        # 3. Determine direction
        direction = "BUY"
        if algo_consensus_score < 40 and news_sentiment < 40:
            direction = "SELL"
        elif algo_consensus_score < 30:
            direction = "SELL"

        return PredictionResult(
            symbol=symbol,
            success_score=round(bounded, 1),
            ml_score=round(ml_score, 1),
            algo_score=round(algo_consensus_score, 1),
            news_score=round(news_sentiment, 1),
            confidence_low=round(max(0.0, bounded - 5.0), 1),
            confidence_high=round(min(100.0, bounded + 5.0), 1),
            direction=direction,
        )

    @staticmethod
    def _simple_ml_fallback(features: Dict[str, float]) -> float:
        """Fallback scoring when XGBoost model is not loaded."""
        score = 50.0
        rsi = features.get("rsi", 50)
        if 30 <= rsi <= 40:
            score += 10
        elif rsi > 80:
            score -= 10
        if features.get("macd", 0) > features.get("macd_signal", 0):
            score += 10
        else:
            score -= 5
        if features.get("adx", 20) > 25:
            score += 10
        r = features.get("price_to_sma20", 1.0)
        if r > 1.02:
            score += 10
        elif r < 0.98:
            score -= 10
        return max(0, min(100, score))
