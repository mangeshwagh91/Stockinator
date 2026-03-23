"""Risk-first controls used by orchestrator and execution."""

from dataclasses import dataclass


@dataclass
class RiskLimits:
    max_daily_loss: float
    max_open_positions: int
    risk_per_trade: float


class RiskMonitor:
    """Tracks account-wide limits and simple risk state snapshots."""

    def __init__(self, limits: RiskLimits):
        self.limits = limits

    def evaluate(self, daily_pnl: float, open_positions: int) -> dict[str, float | bool | int]:
        max_loss_used = 0.0
        if self.limits.max_daily_loss > 0:
            max_loss_used = abs(min(daily_pnl, 0.0)) / self.limits.max_daily_loss

        return {
            "halted": daily_pnl <= (-1 * self.limits.max_daily_loss),
            "max_loss_used": round(max_loss_used, 4),
            "open_positions": open_positions,
            "max_open_positions": self.limits.max_open_positions,
        }
