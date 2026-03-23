"""Market data and indicators endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List
import yfinance as yf

from app.api.dependencies import get_database
from app.schemas.indicator import IndicatorValues, IndicatorListResponse, IndicatorRequest
from app.services.market_data import market_data_service
from app.services.indicator_service import indicator_service
from app.services.news_service import news_service
from app.schemas.news import NewsListResponse

router = APIRouter()


# ---------------------------------------------------------------------------
# Watchlist – curated list of Indian indices + large-cap stocks
# ---------------------------------------------------------------------------
_WATCHLIST = [
    # Indices
    {"symbol": "NIFTY50",     "yf": "^NSEI",     "name": "Nifty 50",              "exchange": "NSE", "segment": "NSE Equity Indices"},
    {"symbol": "BANKNIFTY",   "yf": "^NSEBANK",  "name": "Nifty Bank",           "exchange": "NSE", "segment": "NSE Equity Indices"},
    {"symbol": "FINNIFTY",    "yf": "NIFTY_FIN_SERVICE.NS", "name": "Nifty Fin Svc", "exchange": "NSE", "segment": "NSE Equity Indices"},
    {"symbol": "MIDCPNIFTY",  "yf": "^NSEMDCP50","name": "Nifty Midcap 50",     "exchange": "NSE", "segment": "NSE Equity Indices"},
    {"symbol": "SENSEX",      "yf": "^BSESN",    "name": "BSE Sensex",           "exchange": "BSE", "segment": "BSE Equity Indices"},
    {"symbol": "BANKEX",      "yf": "BSE-BANKEX.BO", "name": "BSE Bankex",       "exchange": "BSE", "segment": "BSE Equity Indices"},
    # NSE Cash Equity – Large Caps
    {"symbol": "RELIANCE",    "yf": "RELIANCE.NS",  "name": "Reliance Industries",  "exchange": "NSE", "segment": "NSE Cash Equity"},
    {"symbol": "TCS",         "yf": "TCS.NS",       "name": "Tata Consultancy Svc", "exchange": "NSE", "segment": "NSE Cash Equity"},
    {"symbol": "INFY",        "yf": "INFY.NS",      "name": "Infosys",              "exchange": "NSE", "segment": "NSE Cash Equity"},
    {"symbol": "HDFCBANK",    "yf": "HDFCBANK.NS",  "name": "HDFC Bank",           "exchange": "NSE", "segment": "NSE Cash Equity"},
    {"symbol": "ICICIBANK",   "yf": "ICICIBANK.NS", "name": "ICICI Bank",          "exchange": "NSE", "segment": "NSE Cash Equity"},
    {"symbol": "SBIN",        "yf": "SBIN.NS",      "name": "State Bank of India",  "exchange": "NSE", "segment": "NSE Cash Equity"},
    {"symbol": "AXISBANK",    "yf": "AXISBANK.NS",  "name": "Axis Bank",           "exchange": "NSE", "segment": "NSE Cash Equity"},
    {"symbol": "WIPRO",       "yf": "WIPRO.NS",     "name": "Wipro",               "exchange": "NSE", "segment": "NSE Cash Equity"},
    {"symbol": "HCLTECH",     "yf": "HCLTECH.NS",   "name": "HCL Technologies",    "exchange": "NSE", "segment": "NSE Cash Equity"},
    {"symbol": "LT",          "yf": "LT.NS",        "name": "Larsen & Toubro",     "exchange": "NSE", "segment": "NSE Cash Equity"},
    {"symbol": "MARUTI",      "yf": "MARUTI.NS",    "name": "Maruti Suzuki",       "exchange": "NSE", "segment": "NSE Cash Equity"},
    {"symbol": "TATAMOTORS",  "yf": "TATAMOTORS.NS","name": "Tata Motors",        "exchange": "NSE", "segment": "NSE Cash Equity"},
    {"symbol": "TATASTEEL",   "yf": "TATASTEEL.NS", "name": "Tata Steel",         "exchange": "NSE", "segment": "NSE Cash Equity"},
    {"symbol": "ADANIENT",    "yf": "ADANIENT.NS",  "name": "Adani Enterprises",  "exchange": "NSE", "segment": "NSE Cash Equity"},
    {"symbol": "SUNPHARMA",   "yf": "SUNPHARMA.NS", "name": "Sun Pharmaceutical", "exchange": "NSE", "segment": "NSE Cash Equity"},
    # F&O
    {"symbol": "NIFTY-FUT",   "yf": "^NSEI",     "name": "Nifty 50 Futures",  "exchange": "NSE", "segment": "F&O - Index Futures"},
    {"symbol": "BANKNIFTY-FUT","yf": "^NSEBANK", "name": "Bank Nifty Futures","exchange": "NSE", "segment": "F&O - Index Futures"},
    # Currency
    {"symbol": "USDINR",      "yf": "INR=X",     "name": "USD/INR",            "exchange": "NSE", "segment": "Currency Derivatives"},
    {"symbol": "EURINR",      "yf": "EURINR=X",  "name": "EUR/INR",            "exchange": "NSE", "segment": "Currency Derivatives"},
    # Commodities
    {"symbol": "CRUDEOIL",    "yf": "CL=F",      "name": "Crude Oil Futures",  "exchange": "MCX", "segment": "MCX Commodity Derivatives"},
    {"symbol": "GOLD",        "yf": "GC=F",      "name": "Gold Futures",       "exchange": "MCX", "segment": "MCX Commodity Derivatives"},
    {"symbol": "SILVER",      "yf": "SI=F",      "name": "Silver Futures",     "exchange": "MCX", "segment": "MCX Commodity Derivatives"},
]

_YF_SYMBOL_MAP = {item["symbol"]: item["yf"] for item in _WATCHLIST}


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
            "asset_type": asset_type,
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
    """Get historical OHLCV data. Use asset_type=stock for NSE/BSE/MCX symbols in India-first mode."""
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


# ---------------------------------------------------------------------------
# New endpoints for the AI Signals live page
# ---------------------------------------------------------------------------

@router.get("/symbols")
async def get_symbols():
    """Return the curated watchlist of symbols with metadata."""
    return {"symbols": _WATCHLIST}


@router.get("/quote/{symbol}")
def get_quote(symbol: str):
    """Return latest price, prev_close, change, change_pct for a symbol."""
    yf_sym = _YF_SYMBOL_MAP.get(symbol.upper(), f"{symbol}.NS")
    try:
        ticker = yf.Ticker(yf_sym)
        info = ticker.fast_info
        price = float(getattr(info, "last_price", None) or getattr(info, "regular_market_price", None) or 0)
        prev_close = float(getattr(info, "previous_close", None) or getattr(info, "regular_market_previous_close", None) or 0)
        # Fall back to history if fast_info gives 0
        if price == 0:
            hist = ticker.history(period="2d", interval="1d")
            if not hist.empty:
                price = float(hist["Close"].iloc[-1])
                prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else price
        change = round(price - prev_close, 2) if prev_close else 0.0
        change_pct = round((change / prev_close) * 100, 2) if prev_close else 0.0
        return {
            "symbol": symbol,
            "yf_symbol": yf_sym,
            "price": round(price, 2),
            "prev_close": round(prev_close, 2),
            "change": change,
            "change_pct": change_pct,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Quote error for {symbol}: {str(e)}")


import time
from starlette.concurrency import run_in_threadpool

_CHART_CACHE = {}

def _fetch_yf_history_cached(yf_sym: str, period: str, interval: str, ttl_seconds: int = 300):
    cache_key = f"{yf_sym}_{period}_{interval}"
    now = time.time()
    if cache_key in _CHART_CACHE:
        cache_time, data = _CHART_CACHE[cache_key]
        if now - cache_time < ttl_seconds:
            return data
            
    ticker = yf.Ticker(yf_sym)
    data = ticker.history(period=period, interval=interval)
    if not data.empty:
        _CHART_CACHE[cache_key] = (now, data)
    return data


@router.get("/chart/{symbol}")
def get_chart(
    symbol: str,
    period: str = Query("1mo", description="yfinance period: 1d, 5d, 1mo, 3mo, 6mo, 1y"),
    interval: str = Query("1d", description="yfinance interval: 1m, 5m, 15m, 60m, 1d, 1wk"),
):
    """Return OHLCV candles for a symbol (for candlestick chart rendering)."""
    yf_sym = _YF_SYMBOL_MAP.get(symbol.upper(), f"{symbol}.NS")
    try:
        hist = _fetch_yf_history_cached(yf_sym, period, interval)
        if hist.empty:
            raise HTTPException(status_code=404, detail=f"No chart data for {symbol}")
        hist.index = hist.index.astype(str)
        candles = []
        for ts, row in hist.iterrows():
            candles.append({
                "time": str(ts),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row.get("Volume", 0)),
            })
        return {
            "symbol": symbol,
            "yf_symbol": yf_sym,
            "period": period,
            "interval": interval,
            "count": len(candles),
            "candles": candles,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Chart error for {symbol}: {str(e)}")


@router.get("/latest-candle/{symbol}")
def get_latest_candle(
    symbol: str,
    interval: str = Query("1d", description="yfinance interval: 1m, 5m, 15m, 60m, 1d, 1wk"),
):
    """Return the single most recent OHLCV candle — used for real-time chart updates."""
    yf_sym = _YF_SYMBOL_MAP.get(symbol.upper(), f"{symbol}.NS")
    # For intraday intervals fetch a short window; for daily/weekly fetch 2 bars
    period_map = {
        "1m": "1d", "2m": "1d", "5m": "5d", "15m": "5d",
        "30m": "5d", "60m": "5d", "90m": "5d",
        "1d": "5d", "1wk": "1mo", "1mo": "3mo",
    }
    fetch_period = period_map.get(interval, "5d")
    try:
        ticker = yf.Ticker(yf_sym)
        hist = ticker.history(period=fetch_period, interval=interval)
        if hist.empty:
            raise HTTPException(status_code=404, detail=f"No data for {symbol}")
        last = hist.iloc[-1]
        ts = str(hist.index[-1])
        return {
            "symbol": symbol,
            "candle": {
                "time": ts,
                "open": round(float(last["Open"]), 2),
                "high": round(float(last["High"]), 2),
                "low": round(float(last["Low"]), 2),
                "close": round(float(last["Close"]), 2),
                "volume": int(last.get("Volume", 0)),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Latest candle error for {symbol}: {str(e)}")
