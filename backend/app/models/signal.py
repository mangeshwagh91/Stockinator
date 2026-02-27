"""Signal model for storing trading signals"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON
from sqlalchemy.sql import func

from app.core.database import Base


class Signal(Base):
    """Signal model - stores ML predictions and decisions"""
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    interval = Column(String(10), default="1m")  # 1m, 5m, 15m, 1h, etc.
    
    # ML Score
    success_score = Column(Float, nullable=False)
    threshold = Column(Float, default=80.0)
    
    # Decision
    action = Column(String(10))  # BUY, SELL, HOLD
    confidence = Column(Float)
    
    # Features used for prediction
    features = Column(JSON, nullable=True)  # Store feature vector as JSON
    
    # Indicator values at signal time
    rsi = Column(Float, nullable=True)
    macd = Column(Float, nullable=True)
    macd_signal = Column(Float, nullable=True)
    adx = Column(Float, nullable=True)
    sma_20 = Column(Float, nullable=True)
    sma_50 = Column(Float, nullable=True)
    
    # Market data
    price = Column(Float, nullable=True)
    volume = Column(Float, nullable=True)
    
    # Sentiment
    sentiment_score = Column(Float, nullable=True)
    
    # Whether this signal resulted in a trade
    executed = Column(Boolean, default=False)
    trade_id = Column(Integer, nullable=True)  # FK to trades table
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Signal {self.symbol} score={self.success_score} action={self.action}>"
