"""Indicator schemas for API responses"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any


class IndicatorValues(BaseModel):
    """Schema for indicator values at a point in time"""
    symbol: str
    interval: str = "1m"
    timestamp: datetime
    
    # Price data
    open: float
    high: float
    low: float
    close: float
    volume: float
    
    # Trend indicators
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    
    # Momentum indicators
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    stochastic_k: Optional[float] = None
    stochastic_d: Optional[float] = None
    
    # Volatility indicators
    bollinger_upper: Optional[float] = None
    bollinger_middle: Optional[float] = None
    bollinger_lower: Optional[float] = None
    atr: Optional[float] = None
    
    # Trend strength
    adx: Optional[float] = None
    adx_pos: Optional[float] = None
    adx_neg: Optional[float] = None
    
    # Volume indicators
    obv: Optional[float] = None
    vwap: Optional[float] = None
    
    class Config:
        from_attributes = True


class IndicatorListResponse(BaseModel):
    """Schema for list of indicator values"""
    indicators: list[IndicatorValues]
    total: int


class IndicatorRequest(BaseModel):
    """Schema for requesting indicator calculations"""
    symbol: str
    interval: str = "1m"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    indicators: list[str] = ["sma_20", "sma_50", "rsi", "macd", "adx"]
