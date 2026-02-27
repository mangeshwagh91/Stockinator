"""News model for storing news articles and sentiment"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func

from app.core.database import Base


class News(Base):
    """News model - stores news articles with LLM sentiment analysis"""
    __tablename__ = "news"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    
    # Article details
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=True)
    source = Column(String(100), nullable=True)
    author = Column(String(200), nullable=True)
    
    # Content
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    
    # Sentiment analysis
    sentiment = Column(String(20))  # positive, negative, neutral
    sentiment_score = Column(Float, default=0.0)  # -1 to 1
    impact_score = Column(Float, default=0.0)  # 0 to 1, relevance/impact
    
    # LLM analysis
    llm_summary = Column(Text, nullable=True)
    llm_model = Column(String(50), nullable=True)
    
    # Timestamps
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<News {self.symbol} {self.sentiment} score={self.sentiment_score}>"
