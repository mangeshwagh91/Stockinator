"""News scraping and sentiment analysis service"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import openai

from app.core.config import settings
from app.models.news import News
from app.schemas.news import NewsCreate, NewsSentimentUpdate


class NewsService:
    """Service for news scraping and LLM sentiment analysis"""
    
    def __init__(self):
        self.news_api_key = settings.NEWS_API_KEY
        self.openai_api_key = settings.OPENAI_API_KEY
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
    
    def fetch_news_from_api(self, symbol: str, days: int = 1) -> List[Dict]:
        """
        Fetch news from NewsAPI
        
        Args:
            symbol: Stock symbol
            days: Number of days to look back
        
        Returns:
            List of news articles
        """
        if not self.news_api_key:
            return []
        
        from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': symbol,
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
        if not self.openai_api_key:
            # Fallback to simple keyword-based sentiment
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
            response = openai.ChatCompletion.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a financial news analyst expert in sentiment analysis for trading."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            result_text = response.choices[0].message.content
            
            # Parse response
            sentiment_data = self._parse_llm_response(result_text)
            sentiment_data['llm_model'] = settings.OPENAI_MODEL
            
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
