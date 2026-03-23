"""News scraping Celery task"""
from workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.news_service import news_service

@celery_app.task(name='scrape_news_for_watchlist')
def scrape_news_for_watchlist():
    """
    Periodically scrape configured global + Indian news websites,
    filter stock-market-impact stories, deduplicate, and persist to DB.
    """
    db = SessionLocal()
    
    try:
        print("📰 Starting source-based news scraping...")

        articles = news_service.fetch_market_impact_news_from_sources()
        total_saved = news_service.save_scraped_news_to_db(articles, db)

        print(f"📰 Source scraping completed. Candidates={len(articles)} Saved={total_saved}")
        
        return {
            "status": "completed",
            "sources_processed": len(news_service.NEWS_SOURCES),
            "candidates": len(articles),
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
