"""News schemas for API requests and responses"""
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import Optional


class NewsBase(BaseModel):
    """Base news schema"""
    symbol: str = Field(..., max_length=20)
    title: str
    url: Optional[str] = None
    source: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None


class NewsCreate(NewsBase):
    """Schema for creating news"""
    published_at: Optional[datetime] = None


class NewsResponse(NewsBase):
    """Schema for news response"""
    id: int
    sentiment: Optional[str] = None
    sentiment_score: float = 0.0
    impact_score: float = 0.0
    llm_summary: Optional[str] = None
    llm_model: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: datetime
    processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class NewsListResponse(BaseModel):
    """Schema for news list response"""
    news: list[NewsResponse]
    total: int
    page: int
    page_size: int


class NewsSentimentUpdate(BaseModel):
    """Schema for updating news sentiment"""
    sentiment: str = Field(..., pattern="^(positive|negative|neutral)$")
    sentiment_score: float = Field(..., ge=-1, le=1)
    impact_score: float = Field(..., ge=0, le=1)
    llm_summary: Optional[str] = None
    llm_model: Optional[str] = None
