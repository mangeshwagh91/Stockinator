"""Celery application configuration"""
from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "stockinator",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        'workers.tasks.market_processor',
        'workers.tasks.news_scraper',
        'workers.tasks.model_retrain'
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Periodic task schedule
celery_app.conf.beat_schedule = {
    'scrape-news-every-15-seconds': {
        'task': 'workers.tasks.news_scraper.scrape_news_for_watchlist',
        'schedule': 15.0,  # Every 15 seconds
    },
    'retrain-model-daily': {
        'task': 'workers.tasks.model_retrain.retrain_model_task',
        'schedule': 86400.0,  # Every 24 hours
    },
}
