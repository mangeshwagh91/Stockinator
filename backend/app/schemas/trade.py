"""Trade schemas for API requests and responses"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class TradeType(str, Enum):
    """Trade type"""
    BUY = "BUY"
    SELL = "SELL"


class TradeStatus(str, Enum):
    """Trade status"""
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIAL = "PARTIAL"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class TradeBase(BaseModel):
    """Base trade schema"""
    symbol: str = Field(..., max_length=20)
    trade_type: TradeType
    quantity: float = Field(..., gt=0)
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    notes: Optional[str] = Field(None, max_length=500)


class TradeCreate(TradeBase):
    """Schema for creating a new trade"""
    success_score: Optional[float] = None
    is_paper: bool = True


class TradeUpdate(BaseModel):
    """Schema for updating a trade"""
    status: Optional[TradeStatus] = None
    exit_price: Optional[float] = None
    profit_loss: Optional[float] = None
    profit_loss_percentage: Optional[float] = None
    closed_at: Optional[datetime] = None


class TradeResponse(TradeBase):
    """Schema for trade response"""
    id: int
    status: TradeStatus
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    brokerage: float = 0.0
    slippage: float = 0.0
    profit_loss: Optional[float] = None
    profit_loss_percentage: Optional[float] = None
    success_score: Optional[float] = None
    broker_order_id: Optional[str] = None
    broker_name: str
    created_at: datetime
    filled_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    is_paper: bool
    
    class Config:
        from_attributes = True


class TradeListResponse(BaseModel):
    """Schema for trade list response"""
    trades: list[TradeResponse]
    total: int
    page: int
    page_size: int


class TradeSummary(BaseModel):
    """Schema for trade summary statistics"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_profit_loss: float
    win_rate: float
    avg_profit: float
    avg_loss: float
    best_trade: float
    worst_trade: float
