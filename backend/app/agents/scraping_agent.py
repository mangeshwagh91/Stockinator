"""Scraping agent: market data + news + sentiment collection.

Wires to market_data.py and news_service.py for actual data fetching.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import yfinance as yf


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
    sentiment: float = 0.0
    news_headlines: List[str] = field(default_factory=list)


class ScrapingAgent:
    """Collects tick/candle, news, and sentiment inputs for downstream agents."""

    name = "scraping-agent"

    # ── yfinance symbol map (Indian market) ──────────────────────────────
    _YF_MAP = {
        "NIFTY50": "^NSEI", "BANKNIFTY": "^NSEBANK",
        "FINNIFTY": "NIFTY_FIN_SERVICE.NS", "MIDCPNIFTY": "^NSEMDCP50",
        "SENSEX": "^BSESN", "BANKEX": "BSE-BANK.BO",
    }

    def gather(self, symbol: str) -> MarketSnapshot:
        """Fetch real-time quote for a symbol using yfinance."""
        yf_sym = self._YF_MAP.get(symbol.upper(), f"{symbol}.NS")
        ticker = yf.Ticker(yf_sym)
        info = ticker.fast_info

        price = float(getattr(info, "last_price", 0) or 0)
        prev = float(getattr(info, "previous_close", price) or price)
        change = round(price - prev, 2)
        change_pct = round((change / prev) * 100, 2) if prev else 0.0

        return MarketSnapshot(
            symbol=symbol,
            price=price,
            open=float(getattr(info, "open", price) or price),
            high=float(getattr(info, "day_high", price) or price),
            low=float(getattr(info, "day_low", price) or price),
            volume=int(getattr(info, "last_volume", 0) or 0),
            change=change,
            change_pct=change_pct,
            timestamp=datetime.utcnow(),
        )

    def gather_history(self, symbol: str, period: str = "3mo", interval: str = "1d") -> List[Dict]:
        """Fetch OHLCV history for indicator/pattern calculation."""
        yf_sym = self._YF_MAP.get(symbol.upper(), f"{symbol}.NS")
        hist = yf.Ticker(yf_sym).history(period=period, interval=interval)
        if hist.empty:
            return []
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
        return candles

    def gather_news_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Fetch news headlines and basic sentiment score for a symbol."""
        try:
            from app.services.news_service import news_service
            articles = news_service.fetch_news(symbol, limit=10)
            if not articles:
                return {"sentiment": 0.0, "headlines": [], "count": 0}

            headlines = [a.get("title", "") for a in articles[:10]]
            # Simple keyword-based sentiment
            pos_words = {"surge", "rally", "gain", "bull", "up", "high", "buy", "profit", "growth", "strong"}
            neg_words = {"crash", "fall", "drop", "bear", "down", "low", "sell", "loss", "weak", "decline"}
            score = 0
            for h in headlines:
                words = set(h.lower().split())
                score += len(words & pos_words) - len(words & neg_words)
            # Normalize to 0-100
            sentiment = max(0, min(100, 50 + score * 5))
            return {"sentiment": sentiment, "headlines": headlines, "count": len(articles)}
        except Exception:
            return {"sentiment": 50.0, "headlines": [], "count": 0}

    def health(self) -> Dict[str, Any]:
        return {
            "agent": self.name,
            "status": "ready",
            "feeds": ["yfinance", "news_api"],
        }
