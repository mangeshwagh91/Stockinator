"""Strategy registry and ensemble scorer for the algo agent."""
from collections import Counter
from typing import Dict, List

from app.services.strategies.base import StrategyResult
from app.services.strategies.mean_reversion.basic_mean_reversion import evaluate as evaluate_mean_reversion
from app.services.strategies.momentum.trend_following import evaluate as evaluate_trend_following
from app.services.strategies.scalping.mayank_ema_scalping import evaluate_for_registry as evaluate_mayank_scalping
from app.services.strategies.breakout.black_box import evaluate_for_registry as evaluate_black_box
from app.services.strategies.traffic_light.pankajraj_traffic_light import evaluate_for_registry as evaluate_traffic_light
from app.services.strategies.quant.jim_simons import evaluate_for_registry as evaluate_jim_simons


class StrategyRegistry:
    """Holds enabled strategies and builds a blended algo signal."""

    def __init__(self):
        self._strategies = [
            evaluate_trend_following,
            evaluate_mean_reversion,
            evaluate_mayank_scalping,
            evaluate_black_box,
            evaluate_traffic_light,
            evaluate_jim_simons,
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
