"""Decision engine for trade decision making"""
from datetime import datetime, timedelta
from typing import Optional, Dict
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import CooldownActiveError, RiskLimitExceededError
from app.models.trade import Trade, TradeType
from app.services.risk_manager import risk_manager


class DecisionEngine:
    """Engine for making trading decisions based on ML scores and rules"""
    
    def __init__(self):
        self.threshold = settings.DEFAULT_THRESHOLD
        self.cooldown_minutes = settings.COOLDOWN_MINUTES
        self.min_expected_profit = 50.0  # Minimum expected profit in currency
    
    def should_trade(
        self,
        symbol: str,
        success_score: float,
        current_price: float,
        db: Session,
        features: Dict[str, float]
    ) -> Dict:
        """
        Evaluate whether to place a trade
        
        Args:
            symbol: Trading symbol
            success_score: ML predicted success score (0-100)
            current_price: Current market price
            db: Database session
            features: Indicator features used for decision
        
        Returns:
            Dictionary with decision details
        """
        decision = {
            "should_trade": False,
            "action": "HOLD",
            "reason": [],
            "success_score": success_score,
            "quantity": 0,
            "stop_loss": None,
            "take_profit": None
        }
        
        # Check 1: Score threshold
        if success_score < self.threshold:
            decision["reason"].append(f"Score {success_score:.1f} below threshold {self.threshold}")
            return decision
        
        # Check 2: Cooldown period
        if not self._check_cooldown(symbol, db):
            decision["reason"].append(f"Cooldown active (last trade < {self.cooldown_minutes} min ago)")
            raise CooldownActiveError(f"Cooldown period active for {symbol}")
        
        # Check 3: Risk limits
        try:
            position_size = risk_manager.calculate_position_size(
                symbol=symbol,
                current_price=current_price,
                atr=features.get('atr', current_price * 0.02),
                db=db
            )
        except RiskLimitExceededError as e:
            decision["reason"].append(str(e))
            return decision
        
        # Check 4: Expected profit vs costs
        expected_profit = self._estimate_profit(success_score, current_price, position_size)
        costs = self._calculate_costs(current_price, position_size)
        
        if expected_profit <= costs + self.min_expected_profit:
            decision["reason"].append(
                f"Expected profit {expected_profit:.2f} too low vs costs {costs:.2f}"
            )
            return decision
        
        # All checks passed - generate trade signal
        decision["should_trade"] = True
        decision["action"] = "BUY"  # Currently only supporting long positions
        decision["quantity"] = position_size / current_price
        decision["reason"].append("All conditions met for trade")
        
        # Calculate stop loss and take profit
        atr = features.get('atr', current_price * 0.02)
        decision["stop_loss"] = current_price - (2 * atr)  # 2 ATR stop loss
        decision["take_profit"] = current_price + (3 * atr)  # 3 ATR take profit (1.5:1 R:R)
        
        return decision
    
    def _check_cooldown(self, symbol: str, db: Session) -> bool:
        """
        Check if cooldown period has passed since last trade
        
        Args:
            symbol: Trading symbol
            db: Database session
        
        Returns:
            True if cooldown passed, False otherwise
        """
        cooldown_time = datetime.now() - timedelta(minutes=self.cooldown_minutes)
        
        last_trade = db.query(Trade).filter(
            Trade.symbol == symbol,
            Trade.created_at >= cooldown_time
        ).order_by(Trade.created_at.desc()).first()
        
        return last_trade is None
    
    def _estimate_profit(self, success_score: float, price: float, position_size: float) -> float:
        """
        Estimate expected profit based on success score
        
        Args:
            success_score: ML success score
            price: Current price
            position_size: Position size in currency
        
        Returns:
            Estimated profit
        """
        # Simple model: higher score = higher expected return
        # Assuming 0.5% to 2% potential move based on score
        expected_return_pct = 0.5 + (success_score / 100) * 1.5
        expected_profit = position_size * (expected_return_pct / 100)
        
        return expected_profit
    
    def _calculate_costs(self, price: float, position_size: float) -> float:
        """
        Calculate brokerage and estimated slippage
        
        Args:
            price: Current price
            position_size: Position size in currency
        
        Returns:
            Total estimated costs
        """
        # Brokerage: 0.1% (adjust based on your broker)
        brokerage = position_size * 0.001
        
        # Slippage: 0.05%
        slippage = position_size * 0.0005
        
        return brokerage + slippage
    
    def set_threshold(self, threshold: float):
        """Update the score threshold"""
        self.threshold = max(0, min(100, threshold))
    
    def set_cooldown(self, minutes: int):
        """Update the cooldown period"""
        self.cooldown_minutes = max(0, minutes)


# Global instance
decision_engine = DecisionEngine()
