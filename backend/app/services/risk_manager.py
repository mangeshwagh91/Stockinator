"""Risk management service for position sizing and limits"""
from datetime import datetime, date
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.config import settings
from app.core.exceptions import RiskLimitExceededError
from app.models.trade import Trade, TradeStatus


class RiskManager:
    """Manager for risk limits and position sizing"""
    
    def __init__(self):
        self.max_daily_loss = settings.MAX_DAILY_LOSS
        self.max_position_size = settings.MAX_POSITION_SIZE
        self.risk_per_trade = 0.02  # 2% of account per trade
        self.max_open_positions = 5
    
    def calculate_position_size(
        self,
        symbol: str,
        current_price: float,
        atr: float,
        db: Session,
        account_equity: float = 100000.0  # Default account size
    ) -> float:
        """
        Calculate position size based on risk parameters
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
            atr: Average True Range for volatility
            db: Database session
            account_equity: Total account equity
        
        Returns:
            Position size in currency units
        """
        # Check risk limits first
        self._check_risk_limits(db)
        
        # Method 1: Fixed percentage of equity
        max_size_by_equity = account_equity * self.risk_per_trade
        
        # Method 2: ATR-based (risking 2% on a 2 ATR stop loss)
        risk_amount = account_equity * self.risk_per_trade
        stop_distance = 2 * atr  # 2 ATR stop loss
        shares = risk_amount / stop_distance if stop_distance > 0 else 0
        max_size_by_atr = shares * current_price
        
        # Take the minimum of both methods and max position size
        position_size = min(
            max_size_by_equity,
            max_size_by_atr,
            self.max_position_size
        )
        
        return max(position_size, 100.0)  # Minimum position size
    
    def _check_risk_limits(self, db: Session):
        """
        Check if any risk limits would be exceeded
        
        Args:
            db: Database session
        
        Raises:
            RiskLimitExceededError: If any risk limit is exceeded
        """
        # Check daily loss limit
        today_pnl = self._get_today_pnl(db)
        if today_pnl < -self.max_daily_loss:
            raise RiskLimitExceededError(
                f"Daily loss limit exceeded: {today_pnl:.2f}"
            )
        
        # Check max open positions
        open_positions = self._count_open_positions(db)
        if open_positions >= self.max_open_positions:
            raise RiskLimitExceededError(
                f"Max open positions reached: {open_positions}/{self.max_open_positions}"
            )
    
    def _get_today_pnl(self, db: Session) -> float:
        """
        Calculate today's P&L
        
        Args:
            db: Database session
        
        Returns:
            Today's total P&L
        """
        today = date.today()
        
        result = db.query(
            func.sum(Trade.profit_loss)
        ).filter(
            func.date(Trade.closed_at) == today,
            Trade.status == TradeStatus.FILLED,
            Trade.profit_loss.isnot(None)
        ).scalar()
        
        return float(result) if result else 0.0
    
    def _count_open_positions(self, db: Session) -> int:
        """
        Count currently open positions
        
        Args:
            db: Database session
        
        Returns:
            Number of open positions
        """
        count = db.query(Trade).filter(
            Trade.status.in_([TradeStatus.PENDING, TradeStatus.PARTIAL]),
            Trade.closed_at.is_(None)
        ).count()
        
        return count
    
    def get_risk_metrics(self, db: Session) -> dict:
        """
        Get current risk metrics
        
        Args:
            db: Database session
        
        Returns:
            Dictionary of risk metrics
        """
        return {
            "today_pnl": self._get_today_pnl(db),
            "max_daily_loss": self.max_daily_loss,
            "daily_loss_used_pct": abs(self._get_today_pnl(db) / self.max_daily_loss * 100),
            "open_positions": self._count_open_positions(db),
            "max_open_positions": self.max_open_positions,
            "max_position_size": self.max_position_size,
            "risk_per_trade_pct": self.risk_per_trade * 100
        }
    
    def update_limits(
        self,
        max_daily_loss: Optional[float] = None,
        max_position_size: Optional[float] = None,
        risk_per_trade: Optional[float] = None,
        max_open_positions: Optional[int] = None
    ):
        """Update risk limits"""
        if max_daily_loss is not None:
            self.max_daily_loss = max_daily_loss
        if max_position_size is not None:
            self.max_position_size = max_position_size
        if risk_per_trade is not None:
            self.risk_per_trade = min(0.1, max(0.001, risk_per_trade))  # Between 0.1% and 10%
        if max_open_positions is not None:
            self.max_open_positions = max(1, max_open_positions)


# Global instance
risk_manager = RiskManager()
