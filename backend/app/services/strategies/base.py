"""Base strategy contracts for algo evaluation."""
from dataclasses import dataclass, field
from typing import Dict, Literal

StrategyDirection = Literal["BUY", "SELL", "HOLD"]


@dataclass
class StrategyResult:
    """Standardized strategy output for ensemble scoring."""

    name: str
    score: float
    direction: StrategyDirection
    reason: str
    metadata: Dict[str, float] = field(default_factory=dict)

    def bounded_score(self) -> float:
        """Return score normalized to 0-100."""
        return max(0.0, min(100.0, float(self.score)))
