"""News scraping Celery task"""
from workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.news_service import news_service


# Watchlist of symbols to monitor
WATCHLIST = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA', 'AMD', 'META']


@celery_app.task(name='scrape_news_for_watchlist')
def scrape_news_for_watchlist():
    """
    Periodically scrape news for all symbols in watchlist
    """
    db = SessionLocal()
    
    try:
        print("📰 Starting news scraping for watchlist...")
        total_saved = 0
        
        for symbol in WATCHLIST:
            try:
                # Fetch news from API
                articles = news_service.fetch_news_from_api(symbol, days=1)
                
                if articles:
                    # Save to database with sentiment analysis
                    saved_count = news_service.save_news_to_db(symbol, articles, db)
                    total_saved += saved_count
                    
                    print(f"✓ {symbol}: Fetched {len(articles)}, Saved {saved_count} new articles")
                else:
                    print(f"⚠️ {symbol}: No articles found")
            
            except Exception as e:
                print(f"❌ Error scraping news for {symbol}: {e}")
        
        print(f"📰 News scraping completed. Total saved: {total_saved}")
        
        return {
            "status": "completed",
            "symbols_processed": len(WATCHLIST),
            "articles_saved": total_saved
        }
    
    except Exception as e:
        print(f"❌ Error in news scraping task: {e}")
        return {"status": "error", "message": str(e)}
    
    finally:
        db.close()


@celery_app.task(name='scrape_news_for_symbol')
def scrape_news_for_symbol(symbol: str, days: int = 1):
    """
    Scrape news for a specific symbol
    
    Args:
        symbol: Stock symbol
        days: Number of days to look back
    """
    db = SessionLocal()
    
    try:
        print(f"📰 Scraping news for {symbol}...")
        
        articles = news_service.fetch_news_from_api(symbol, days)
        saved_count = news_service.save_news_to_db(symbol, articles, db)
        
        print(f"✓ {symbol}: Saved {saved_count} articles")
        
        return {
            "status": "completed",
            "symbol": symbol,
            "articles_fetched": len(articles),
            "articles_saved": saved_count
        }
    
    except Exception as e:
        print(f"❌ Error scraping news for {symbol}: {e}")
        return {"status": "error", "message": str(e)}
    
    finally:
        db.close()
