"""Database connection management for PostgreSQL and InfluxDB"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
import redis
from typing import Generator

from app.core.config import settings

# PostgreSQL setup
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# InfluxDB setup
class InfluxDBManager:
    """Manager for InfluxDB connections"""
    
    def __init__(self):
        self.client = None
        self.write_api = None
        self.query_api = None
    
    def connect(self):
        """Connect to InfluxDB"""
        self.client = InfluxDBClient(
            url=settings.INFLUX_URL,
            token=settings.INFLUX_TOKEN,
            org=settings.INFLUX_ORG
        )
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()
        return self
    
    def disconnect(self):
        """Close InfluxDB connection"""
        if self.client:
            self.client.close()
    
    def write_point(self, measurement: str, tags: dict, fields: dict, timestamp=None):
        """Write a data point to InfluxDB"""
        from influxdb_client import Point
        
        point = Point(measurement)
        for key, value in tags.items():
            point.tag(key, value)
        for key, value in fields.items():
            point.field(key, value)
        if timestamp:
            point.time(timestamp)
        
        self.write_api.write(bucket=settings.INFLUX_BUCKET, record=point)
    
    def query(self, flux_query: str):
        """Execute a Flux query"""
        return self.query_api.query(flux_query)


# Global InfluxDB instance
influx_db = InfluxDBManager()


# Redis setup
class RedisManager:
    """Manager for Redis connections"""
    
    def __init__(self):
        self.client = None
    
    def connect(self):
        """Connect to Redis"""
        self.client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            decode_responses=True
        )
        return self
    
    def disconnect(self):
        """Close Redis connection"""
        if self.client:
            self.client.close()
    
    def publish(self, channel: str, message: str):
        """Publish message to Redis channel"""
        self.client.publish(channel, message)
    
    def get(self, key: str):
        """Get value from Redis"""
        return self.client.get(key)
    
    def set(self, key: str, value: str, ex: int = None):
        """Set value in Redis with optional expiration"""
        self.client.set(key, value, ex=ex)


# Global Redis instance
redis_manager = RedisManager()


def init_db():
    """Initialize databases - create tables"""
    Base.metadata.create_all(bind=engine)
