"""News scraping and sentiment analysis service"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from openai import OpenAI
from urllib.parse import urljoin
import re

from app.core.config import settings
from app.models.news import News
from app.schemas.news import NewsCreate, NewsSentimentUpdate


class NewsService:
    """Service for news scraping and LLM sentiment analysis"""

    NEWS_SOURCES = {
        "Reuters": "https://www.reuters.com/",
        "BBC": "https://www.bbc.com/",
        "The Guardian": "https://www.theguardian.com/international",
        "The Hindu": "https://www.thehindu.com/",
        "Indian Express": "https://indianexpress.com/",
        "Times of India": "https://timesofindia.indiatimes.com/",
    }

    RSS_SOURCES = {
        "Reuters": "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best",
        "BBC": "https://feeds.bbci.co.uk/news/business/rss.xml",
        "The Guardian": "https://www.theguardian.com/business/rss",
        "The Hindu": "https://www.thehindu.com/business/feeder/default.rss",
        "Indian Express": "https://indianexpress.com/section/business/feed/",
        "Times of India": "https://timesofindia.indiatimes.com/rssfeeds/1898055.cms",
    }

    MARKET_IMPACT_KEYWORDS = {
        "rbi", "repo", "reverse repo", "inflation", "gdp", "fii", "dii", "sensex", "nifty",
        "bank nifty", "rupee", "usd", "dollar", "bond", "g-sec", "yield", "crude", "oil",
        "gas", "coal", "metals", "gold", "silver", "earnings", "results", "guidance", "ipo",
        "sebi", "finance ministry", "budget", "tax", "tariff", "sanction", "war", "fed",
        "interest rate", "rate hike", "rate cut", "china", "us economy", "export", "import",
        "banking", "it sector", "auto sector", "pharma", "fmcg", "telecom", "infrastructure",
    }

    SYMBOL_KEYWORD_MAP = {
        "bank nifty": "BANKNIFTY",
        "nifty": "NIFTY",
        "sensex": "SENSEX",
        "rupee": "USDINR",
        "usd": "USDINR",
        "crude": "CRUDEOIL",
        "oil": "CRUDEOIL",
        "it": "NIFTYIT",
        "auto": "NIFTYAUTO",
        "pharma": "NIFTYPHARMA",
        "fmcg": "NIFTYFMCG",
        "bank": "NIFTYBANK",
    }
    
    def __init__(self):
        self.news_api_key = settings.NEWS_API_KEY
        self.openai_api_key = settings.OPENAI_API_KEY
        self.openai_client: Optional[OpenAI] = None
        
        if self._has_real_openai_key():
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            self.llm_model = settings.OPENAI_MODEL
        else:
            # Fallback to local Ollama (OpenAI API compatible)
            self.openai_client = OpenAI(
                base_url=settings.OLLAMA_BASE_URL,
                api_key="ollama" # Required but ignored
            )
            self.llm_model = settings.OLLAMA_MODEL

    def _has_real_news_key(self) -> bool:
        return bool(self.news_api_key and not self.news_api_key.lower().startswith("your-"))

    def _has_real_openai_key(self) -> bool:
        return bool(self.openai_api_key and not self.openai_api_key.lower().startswith("your-"))

    def _normalize_title(self, text: str) -> str:
        normalized = re.sub(r"[^a-z0-9\s]", " ", text.lower())
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def _fingerprint_title(self, text: str) -> str:
        normalized = self._normalize_title(text)
        tokens = [t for t in normalized.split(" ") if len(t) > 2]
        return " ".join(sorted(set(tokens)))

    def _is_market_impacting(self, title: str, description: str = "") -> bool:
        haystack = f"{title} {description}".lower()
        return any(keyword in haystack for keyword in self.MARKET_IMPACT_KEYWORDS)

    def _infer_symbol(self, title: str, description: str = "") -> str:
        haystack = f"{title} {description}".lower()
        for keyword, symbol in self.SYMBOL_KEYWORD_MAP.items():
            if keyword in haystack:
                return symbol
        return "INDIA_MARKET"

    def scrape_headlines_from_source(self, source_name: str, source_url: str, timeout: int = 10) -> List[Dict]:
        """Scrape candidate headlines from a source homepage using BeautifulSoup."""
        try:
            response = requests.get(
                source_url,
                timeout=timeout,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept-Language": "en-US,en;q=0.9",
                },
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            print(f"Error scraping {source_name}: {e}")
            return []

        candidates: List[Dict] = []
        seen_links = set()

        for a_tag in soup.select("a[href]"):
            href = (a_tag.get("href") or "").strip()
            title = " ".join(a_tag.get_text(" ", strip=True).split())

            if not href or href.startswith("#") or href.startswith("javascript:"):
                continue
            if len(title) < 35 or len(title) > 240:
                continue

            full_url = urljoin(source_url, href)
            if full_url in seen_links:
                continue

            seen_links.add(full_url)
            candidates.append(
                {
                    "title": title,
                    "url": full_url,
                    "source": source_name,
                    "description": "",
                    "published_at": None,
                }
            )

            if len(candidates) >= 120:
                break

        return candidates

    def scrape_headlines_from_rss(self, source_name: str, rss_url: str, timeout: int = 10) -> List[Dict]:
        """Fallback RSS scraper for sources that limit homepage scraping."""
        try:
            response = requests.get(
                rss_url,
                timeout=timeout,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                },
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "xml")
        except Exception as e:
            print(f"Error scraping RSS for {source_name}: {e}")
            return []

        items: List[Dict] = []
        for entry in soup.find_all("item")[:120]:
            title = (entry.title.text or "").strip() if entry.title else ""
            link = (entry.link.text or "").strip() if entry.link else ""
            description = (entry.description.text or "").strip() if entry.description else ""

            if len(title) < 20:
                continue

            items.append(
                {
                    "title": title,
                    "url": link,
                    "source": source_name,
                    "description": description,
                    "published_at": None,
                }
            )

        return items

    def fetch_market_impact_news_from_sources(self) -> List[Dict]:
        """Scrape configured sites, filter market-impact news, and deduplicate across sources."""
        all_candidates: List[Dict] = []
        for source_name, source_url in self.NEWS_SOURCES.items():
            source_items = self.scrape_headlines_from_source(source_name, source_url)
            if not source_items and source_name in self.RSS_SOURCES:
                source_items = self.scrape_headlines_from_rss(source_name, self.RSS_SOURCES[source_name])

            all_candidates.extend(source_items)

        unique_by_fp: Dict[str, Dict] = {}
        for item in all_candidates:
            title = item.get("title", "")
            if not title:
                continue

            if not self._is_market_impacting(title, item.get("description", "")):
                continue

            item["symbol"] = self._infer_symbol(title, item.get("description", ""))
            fp = self._fingerprint_title(title)

            if fp in unique_by_fp:
                existing = unique_by_fp[fp]
                existing_sources = set((existing.get("source") or "").split(", "))
                existing_sources.add(item.get("source", ""))
                existing["source"] = ", ".join(sorted(s for s in existing_sources if s))
                continue

            unique_by_fp[fp] = item

        return list(unique_by_fp.values())

    def save_scraped_news_to_db(self, articles: List[Dict], db: Session) -> int:
        """Persist deduplicated scraped articles with sentiment and impact labels."""
        if not articles:
            return 0

        cutoff_time = datetime.now() - timedelta(days=2)
        recent_rows = db.query(News).filter(News.created_at >= cutoff_time).all()

        recent_by_url = {row.url for row in recent_rows if row.url}
        recent_by_fp: Dict[str, News] = {
            self._fingerprint_title(row.title): row for row in recent_rows if row.title
        }

        saved_count = 0
        for article in articles:
            title = (article.get("title") or "").strip()
            if not title:
                continue

            url = article.get("url")
            if url and url in recent_by_url:
                continue

            fp = self._fingerprint_title(title)
            duplicate_row = recent_by_fp.get(fp)
            if duplicate_row:
                incoming_source = article.get("source") or ""
                if incoming_source and incoming_source not in (duplicate_row.source or ""):
                    merged = ", ".join(sorted(set((duplicate_row.source or "").split(", ")) | {incoming_source}))
                    duplicate_row.source = merged.strip(", ")
                    duplicate_row.processed_at = datetime.now()
                continue

            sentiment_data = self.analyze_sentiment_with_llm(
                title=title,
                description=article.get("description") or "",
                content=article.get("content"),
            )

            news = News(
                symbol=article.get("symbol") or "INDIA_MARKET",
                title=title,
                url=url,
                source=article.get("source"),
                author=article.get("author"),
                description=article.get("description"),
                content=article.get("content"),
                sentiment=sentiment_data["sentiment"],
                sentiment_score=sentiment_data["sentiment_score"],
                impact_score=max(0.4, sentiment_data.get("impact_score", 0.5)),
                llm_summary=sentiment_data.get("llm_summary"),
                llm_model=sentiment_data.get("llm_model"),
                published_at=article.get("published_at"),
                processed_at=datetime.now(),
            )

            db.add(news)
            saved_count += 1
            if url:
                recent_by_url.add(url)
            recent_by_fp[fp] = news

        db.commit()
        return saved_count
    
    def fetch_news_from_api(self, symbol: str, days: int = 1) -> List[Dict]:
        """
        Fetch news from NewsAPI
        
        Args:
            symbol: Stock symbol
            days: Number of days to look back
        
        Returns:
            List of news articles
        """
        if not self._has_real_news_key():
            return []
        
        from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': f"{symbol} AND (NSE OR BSE OR India)",
            'from': from_date,
            'sortBy': 'publishedAt',
            'apiKey': self.news_api_key,
            'language': 'en',
            'pageSize': 20
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return data.get('articles', [])
        except Exception as e:
            print(f"Error fetching news: {e}")
            return []
    
    def scrape_news_content(self, url: str) -> Optional[str]:
        """
        Scrape full content from news URL
        
        Args:
            url: Article URL
        
        Returns:
            Article content or None
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text[:2000]  # Limit to first 2000 characters
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None
    
    def analyze_sentiment_with_llm(
        self,
        title: str,
        description: str,
        content: Optional[str] = None
    ) -> Dict:
        """
        Analyze sentiment using OpenAI LLM
        
        Args:
            title: Article title
            description: Article description
            content: Full article content (optional)
        
        Returns:
            Dictionary with sentiment analysis
        """
        if not self.openai_client:
            # Fallback to simple keyword-based sentiment if both OpenAI and Ollama fail setup (unlikely)
            return self._simple_sentiment_analysis(title, description)
        
        # Construct prompt
        text_to_analyze = f"Title: {title}\n\nDescription: {description}"
        if content:
            text_to_analyze += f"\n\nContent: {content[:500]}"
        
        prompt = f"""Analyze the following news article for stock trading sentiment.

{text_to_analyze}

Provide your analysis in the following format:
Sentiment: [positive/negative/neutral]
Score: [number from -1.0 to 1.0, where -1 is very negative, 0 is neutral, 1 is very positive]
Impact: [number from 0.0 to 1.0, where 0 is no impact, 1 is high impact]
Summary: [brief summary of why this matters for trading]

Focus on the implications for stock price movement."""
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": "You are a financial news analyst expert in sentiment analysis for trading."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=200,
            )
            
            result_text = response.choices[0].message.content or ""
            
            # Parse response
            sentiment_data = self._parse_llm_response(result_text)
            sentiment_data['llm_model'] = self.llm_model
            
            return sentiment_data
        except Exception as e:
            print(f"Error with LLM sentiment analysis: {e}")
            return self._simple_sentiment_analysis(title, description)
    
    def _parse_llm_response(self, response_text: str) -> Dict:
        """Parse LLM response into structured data"""
        lines = response_text.strip().split('\n')
        
        sentiment = "neutral"
        score = 0.0
        impact = 0.5
        summary = ""
        
        for line in lines:
            line_lower = line.lower()
            if line_lower.startswith('sentiment:'):
                sentiment = line.split(':', 1)[1].strip().lower()
            elif line_lower.startswith('score:'):
                try:
                    score = float(line.split(':', 1)[1].strip())
                except:
                    pass
            elif line_lower.startswith('impact:'):
                try:
                    impact = float(line.split(':', 1)[1].strip())
                except:
                    pass
            elif line_lower.startswith('summary:'):
                summary = line.split(':', 1)[1].strip()
        
        return {
            'sentiment': sentiment,
            'sentiment_score': max(-1.0, min(1.0, score)),
            'impact_score': max(0.0, min(1.0, impact)),
            'llm_summary': summary
        }
    
    def _simple_sentiment_analysis(self, title: str, description: str) -> Dict:
        """Simple keyword-based sentiment analysis as fallback"""
        text = (title + " " + description).lower()
        
        positive_words = ['surge', 'gain', 'profit', 'growth', 'rally', 'boom', 'bullish', 'rise', 'up', 'success']
        negative_words = ['fall', 'loss', 'decline', 'crash', 'bearish', 'down', 'drop', 'fail', 'weak']
        
        pos_count = sum(1 for word in positive_words if word in text)
        neg_count = sum(1 for word in negative_words if word in text)
        
        if pos_count > neg_count:
            sentiment = "positive"
            score = min(0.8, pos_count * 0.2)
        elif neg_count > pos_count:
            sentiment = "negative"
            score = max(-0.8, -neg_count * 0.2)
        else:
            sentiment = "neutral"
            score = 0.0
        
        return {
            'sentiment': sentiment,
            'sentiment_score': score,
            'impact_score': 0.5,
            'llm_summary': "Simple keyword-based analysis",
            'llm_model': 'keyword'
        }
    
    def save_news_to_db(
        self,
        symbol: str,
        articles: List[Dict],
        db: Session
    ) -> int:
        """
        Save news articles to database with sentiment analysis
        
        Args:
            symbol: Stock symbol
            articles: List of article dictionaries
            db: Database session
        
        Returns:
            Number of articles saved
        """
        saved_count = 0
        
        for article in articles:
            # Check if article already exists
            existing = db.query(News).filter(
                News.url == article.get('url')
            ).first()
            
            if existing:
                continue
            
            # Analyze sentiment
            sentiment_data = self.analyze_sentiment_with_llm(
                title=article.get('title', ''),
                description=article.get('description', ''),
                content=article.get('content')
            )
            
            # Create news entry
            news = News(
                symbol=symbol,
                title=article.get('title'),
                url=article.get('url'),
                source=article.get('source', {}).get('name'),
                author=article.get('author'),
                description=article.get('description'),
                content=article.get('content'),
                sentiment=sentiment_data['sentiment'],
                sentiment_score=sentiment_data['sentiment_score'],
                impact_score=sentiment_data['impact_score'],
                llm_summary=sentiment_data.get('llm_summary'),
                llm_model=sentiment_data.get('llm_model'),
                published_at=datetime.fromisoformat(article['publishedAt'].replace('Z', '+00:00'))
                    if article.get('publishedAt') else None,
                processed_at=datetime.now()
            )
            
            db.add(news)
            saved_count += 1
        
        db.commit()
        return saved_count
    
    def get_latest_sentiment(self, symbol: str, db: Session, hours: int = 24) -> float:
        """
        Get average sentiment score for recent news
        
        Args:
            symbol: Stock symbol
            db: Database session
            hours: Look back period in hours
        
        Returns:
            Average sentiment score (-1 to 1)
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        news_items = db.query(News).filter(
            News.symbol == symbol,
            News.created_at >= cutoff_time
        ).all()
        
        if not news_items:
            return 0.0
        
        # Weighted average by impact score
        total_weight = sum(n.impact_score for n in news_items)
        if total_weight == 0:
            return 0.0
        
        weighted_sentiment = sum(
            n.sentiment_score * n.impact_score
            for n in news_items
        ) / total_weight
        
        return weighted_sentiment


# Global instance
news_service = NewsService()
