"""Trade model for storing executed trades"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class TradeType(str, enum.Enum):
    """Trade type enumeration"""
    BUY = "BUY"
    SELL = "SELL"


class TradeStatus(str, enum.Enum):
    """Trade status enumeration"""
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIAL = "PARTIAL"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class Trade(Base):
    """Trade model"""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    trade_type = Column(SQLEnum(TradeType), nullable=False)
    status = Column(SQLEnum(TradeStatus), default=TradeStatus.PENDING)
    
    # Quantities and prices
    quantity = Column(Float, nullable=False)
    entry_price = Column(Float)
    exit_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    
    # Costs and P&L
    brokerage = Column(Float, default=0.0)
    slippage = Column(Float, default=0.0)
    profit_loss = Column(Float, nullable=True)
    profit_loss_percentage = Column(Float, nullable=True)
    
    # ML Score
    success_score = Column(Float, nullable=True)
    
    # Broker info
    broker_order_id = Column(String(100), nullable=True)
    broker_name = Column(String(50), default="alpaca")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    filled_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    notes = Column(String(500), nullable=True)
    is_paper = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<Trade {self.symbol} {self.trade_type} @ {self.entry_price}>"
