"""Market data and indicators endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from app.api.dependencies import get_database
from app.schemas.indicator import IndicatorValues, IndicatorListResponse, IndicatorRequest
from app.services.market_data import market_data_service
from app.services.indicator_service import indicator_service
from app.services.news_service import news_service
from app.schemas.news import NewsListResponse

router = APIRouter()


@router.get("/price/{symbol}")
async def get_latest_price(
    symbol: str,
    asset_type: str = "stock"
):
    """Get latest price for a symbol"""
    try:
        price = market_data_service.get_latest_price(symbol, asset_type)
        return {
            "symbol": symbol,
            "price": price,
            "timestamp": datetime.now()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/historical/{symbol}")
async def get_historical_data(
    symbol: str,
    interval: str = "1m",
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 1000,
    asset_type: str = "stock"
):
    """Get historical OHLCV data"""
    try:
        df = market_data_service.fetch_historical_data(
            symbol=symbol,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            asset_type=asset_type
        )
        
        # Convert to list of dicts
        data = df.reset_index().to_dict('records')
        
        return {
            "symbol": symbol,
            "interval": interval,
            "count": len(data),
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/indicators/calculate")
async def calculate_indicators(request: IndicatorRequest):
    """Calculate technical indicators for a symbol"""
    try:
        # Fetch historical data
        df = market_data_service.fetch_historical_data(
            symbol=request.symbol,
            interval=request.interval,
            start_time=request.start_time,
            end_time=request.end_time,
            limit=1000
        )
        
        # Calculate indicators
        df_with_indicators = indicator_service.calculate_all_indicators(df)
        
        # Extract latest features
        features = indicator_service.extract_latest_features(df_with_indicators)
        
        return {
            "symbol": request.symbol,
            "interval": request.interval,
            "timestamp": datetime.now(),
            "features": features,
            "indicators": df_with_indicators.tail(10).to_dict('records')
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/news/{symbol}")
async def get_news_for_symbol(
    symbol: str,
    db: Session = Depends(get_database),
    page: int = 1,
    page_size: int = 20,
    hours: int = 24
):
    """Get recent news for a symbol"""
    from app.models.news import News
    
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    query = db.query(News).filter(
        News.symbol == symbol,
        News.created_at >= cutoff_time
    ).order_by(News.created_at.desc())
    
    total = query.count()
    news_items = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return NewsListResponse(
        news=[item for item in news_items],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/sentiment/{symbol}")
async def get_sentiment_score(
    symbol: str,
    db: Session = Depends(get_database),
    hours: int = 24
):
    """Get average sentiment score for a symbol"""
    try:
        sentiment = news_service.get_latest_sentiment(symbol, db, hours)
        return {
            "symbol": symbol,
            "sentiment_score": sentiment,
            "hours": hours,
            "timestamp": datetime.now()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/news/fetch/{symbol}")
async def fetch_news(
    symbol: str,
    db: Session = Depends(get_database),
    days: int = 1
):
    """Fetch and analyze news for a symbol"""
    try:
        articles = news_service.fetch_news_from_api(symbol, days)
        saved_count = news_service.save_news_to_db(symbol, articles, db)
        
        return {
            "symbol": symbol,
            "fetched": len(articles),
            "saved": saved_count,
            "timestamp": datetime.now()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
