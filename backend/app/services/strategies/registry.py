"""Strategy registry and ensemble scorer for the algo agent."""
from collections import Counter
from typing import Dict, List

from app.services.strategies.base import StrategyResult
from app.services.strategies.mean_reversion import evaluate as evaluate_mean_reversion
from app.services.strategies.trend_following import evaluate as evaluate_trend_following


class StrategyRegistry:
    """Holds enabled strategies and builds a blended algo signal."""

    def __init__(self):
        self._strategies = [
            evaluate_trend_following,
            evaluate_mean_reversion,
        ]

    def evaluate(self, features: Dict[str, float], sentiment_score: float = 0.0) -> Dict:
        """Evaluate all strategies and return blended score and direction."""
        results: List[StrategyResult] = [
            strategy(features, sentiment_score)
            for strategy in self._strategies
        ]

        if not results:
            return {
                "algo_score": 50.0,
                "direction_hint": "BUY",
                "breakdown": [],
            }

        algo_score = sum(result.bounded_score() for result in results) / len(results)

        # Resolve direction by majority vote over non-HOLD outputs.
        directions = [r.direction for r in results if r.direction != "HOLD"]
        if directions:
            direction_hint = Counter(directions).most_common(1)[0][0]
        else:
            direction_hint = "BUY"

        breakdown = [
            {
                "name": r.name,
                "score": round(r.bounded_score(), 2),
                "direction": r.direction,
                "reason": r.reason,
                "metadata": r.metadata,
            }
            for r in results
        ]

        return {
            "algo_score": max(0.0, min(100.0, algo_score)),
            "direction_hint": direction_hint,
            "breakdown": breakdown,
        }


strategy_registry = StrategyRegistry()
