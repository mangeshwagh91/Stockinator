"""Trade agent: order planning and broker execution.

Wires to broker_service.py for live/paper order execution
and risk_manager.py for position sizing.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Literal, Optional
import logging

logger = logging.getLogger(__name__)

TradeSide = Literal["BUY", "SELL", "HOLD"]


@dataclass
class TradePlan:
    symbol: str
    side: TradeSide
    quantity: float
    entry: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    estimated_cost: float


@dataclass
class TradeExecution:
    symbol: str
    side: str
    quantity: float
    entry: float
    stop_loss: float
    take_profit: float
    broker_order_id: Optional[str]
    status: str
    executed_at: datetime
    paper: bool


class TradeAgent:
    """Prepares executable order plans and executes via broker APIs."""

    name = "trade-agent"
    MIN_PROFIT = 50.0  # Minimum expected profit above costs (INR)

    def create_plan(
        self,
        symbol: str,
        side: TradeSide,
        entry: float,
        atr: float,
        quantity: float,
    ) -> TradePlan:
        """Create a trade plan with SL/TP based on ATR."""
        if side == "BUY":
            stop_loss = entry - (atr * 1.5)
            take_profit = entry + (atr * 3.0)
        elif side == "SELL":
            stop_loss = entry + (atr * 1.5)
            take_profit = entry - (atr * 3.0)
        else:
            stop_loss = entry
            take_profit = entry

        sl_dist = abs(entry - stop_loss)
        tp_dist = abs(take_profit - entry)
        rr = round(tp_dist / sl_dist, 2) if sl_dist > 0 else 0

        # Brokerage: 0.1% + slippage: 0.05%
        est_cost = round(quantity * entry * 0.0015, 2)

        return TradePlan(
            symbol=symbol,
            side=side,
            quantity=round(quantity, 4),
            entry=round(entry, 2),
            stop_loss=round(stop_loss, 2),
            take_profit=round(take_profit, 2),
            risk_reward=rr,
            estimated_cost=est_cost,
        )

    def execute(self, plan: TradePlan, paper: bool = True) -> TradeExecution:
        """Execute the trade plan via broker service."""
        broker_order_id = None
        status = "SIMULATED"

        if not paper:
            try:
                from app.services.broker_service import broker_service
                result = broker_service.place_order(
                    symbol=plan.symbol,
                    side=plan.side,
                    quantity=plan.quantity,
                    order_type="market",
                    stop_loss=plan.stop_loss,
                    take_profit=plan.take_profit,
                    asset_type="stock",
                )
                broker_order_id = result.get("broker_order_id")
                status = result.get("status", "SUBMITTED")
                logger.info(f"LIVE order placed: {plan.symbol} {plan.side} "
                            f"qty={plan.quantity} id={broker_order_id}")
            except Exception as e:
                status = f"FAILED: {str(e)}"
                logger.error(f"Order failed for {plan.symbol}: {e}")
        else:
            logger.info(f"PAPER trade: {plan.symbol} {plan.side} "
                        f"qty={plan.quantity} @ {plan.entry}")

        return TradeExecution(
            symbol=plan.symbol,
            side=plan.side,
            quantity=plan.quantity,
            entry=plan.entry,
            stop_loss=plan.stop_loss,
            take_profit=plan.take_profit,
            broker_order_id=broker_order_id,
            status=status,
            executed_at=datetime.utcnow(),
            paper=paper,
        )

    def should_execute(self, plan: TradePlan) -> bool:
        """Check if expected profit exceeds costs + minimum threshold."""
        expected_move = abs(plan.take_profit - plan.entry)
        expected_profit = plan.quantity * expected_move
        return expected_profit > (plan.estimated_cost + self.MIN_PROFIT)
