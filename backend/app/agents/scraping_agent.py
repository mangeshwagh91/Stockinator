"""Scraping agent: market data + news + sentiment collection.

Wires to market_data.py and news_service.py for actual data fetching.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import pandas as pd

from app.services.market_data import market_data_service
from app.services.news_service import news_service

@dataclass
class MarketSnapshot:
    symbol: str
    price: float
    open: float
    high: float
    low: float
    volume: int
    change: float
    change_pct: float
    timestamp: datetime
    sentiment: float = 50.0
    news_headlines: List[str] = field(default_factory=list)


class ScrapingAgent:
    """Collects tick/candle, news, and sentiment inputs for downstream agents."""

    name = "scraping-agent"

    def gather(self, symbol: str) -> MarketSnapshot:
        """Fetch real-time quote for a symbol using market_data_service."""
        # Get today's daily candle for Open, High, Low, Volume
        df_day = market_data_service.fetch_historical_data(
            symbol=symbol,
            interval="1d",
            limit=2,
            asset_type="stock"
        )
        
        # Get latest minute closing price
        df_min = market_data_service.fetch_historical_data(
            symbol=symbol,
            interval="1m",
            limit=1,
            asset_type="stock"
        )
        
        price = 0.0
        if not df_min.empty:
            price = float(df_min["close"].iloc[-1])
            
        open_price = price
        high_price = price
        low_price = price
        volume = 0
        prev_close = price

        if not df_day.empty:
            if len(df_day) >= 1:
                today = df_day.iloc[-1]
                open_price = float(today["open"])
                high_price = float(today["high"])
                low_price = float(today["low"])
                volume = int(today["volume"])
                if len(df_day) >= 2:
                    prev_close = float(df_day.iloc[-2]["close"])
                else:
                    prev_close = open_price

        change = round(price - prev_close, 2)
        change_pct = round((change / prev_close) * 100, 2) if prev_close else 0.0

        return MarketSnapshot(
            symbol=symbol,
            price=price,
            open=open_price,
            high=high_price,
            low=low_price,
            volume=volume,
            change=change,
            change_pct=change_pct,
            timestamp=datetime.utcnow(),
        )

    def gather_history(self, symbol: str, period: str = "3mo", interval: str = "1d") -> List[Dict]:
        """Fetch OHLCV history for indicator/pattern calculation."""
        # Map period to limit roughly (3mo approx 60 trading days)
        limit = 60 if period == "3mo" else 100
        
        df = market_data_service.fetch_historical_data(
            symbol=symbol,
            interval=interval,
            limit=limit,
            asset_type="stock"
        )
        if df.empty:
            return []
            
        candles = []
        for ts, row in df.iterrows():
            candles.append({
                "time": str(ts),
                "open": round(float(row["open"]), 2),
                "high": round(float(row["high"]), 2),
                "low": round(float(row["low"]), 2),
                "close": round(float(row["close"]), 2),
                "volume": int(row.get("volume", 0)),
            })
        return candles

    def gather_news_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Fetch news headlines and basic sentiment score for a symbol."""
        try:
            articles = news_service.fetch_news_from_api(symbol, days=2)
            if not articles:
                # Fallback to scraped sources if api fails or has no data
                impact_news = news_service.fetch_market_impact_news_from_sources()
                articles = [n for n in impact_news if n.get("symbol") == symbol or n.get("symbol") == "INDIA_MARKET"]
                
            if not articles:
                return {"sentiment": 50.0, "headlines": [], "count": 0}

            headlines = []
            total_sentiment = 0.0
            count = 0
            
            for a in articles[:10]:
                title = a.get("title", "")
                desc = a.get("description", "")
                if not title:
                    continue
                    
                headlines.append(title)
                # Analyze sentiment
                sent_data = news_service.analyze_sentiment_with_llm(title, desc)
                # Map -1.0 to 1.0 to 0-100 logic
                score_0_100 = 50 + (sent_data["sentiment_score"] * 50)
                total_sentiment += score_0_100
                count += 1
                
            avg_sentiment = total_sentiment / count if count > 0 else 50.0
            
            return {
                "sentiment": round(avg_sentiment, 1), 
                "headlines": headlines, 
                "count": count
            }
        except Exception as e:
            return {"sentiment": 50.0, "headlines": [], "count": 0}

    def health(self) -> Dict[str, Any]:
        return {
            "agent": self.name,
            "status": "ready",
            "feeds": ["market_data_service", "news_service"],
        }
