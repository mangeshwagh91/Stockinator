"""Application configuration using Pydantic settings"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "Stockinator"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    
    # Database - MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017/Stockinator"
    
    # Database - PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "stockinator"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    
    # InfluxDB
    INFLUX_URL: str = "http://localhost:8086"
    INFLUX_TOKEN: str = ""
    INFLUX_ORG: str = "stockinator"
    INFLUX_BUCKET: str = "market_data"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # OpenAI / Ollama
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4"
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    OLLAMA_MODEL: str = "llama3"
    
    # News API
    NEWS_API_KEY: str = ""
    
    # Broker APIs
    ALPACA_API_KEY: str = ""
    ALPACA_SECRET_KEY: str = ""
    ALPACA_BASE_URL: str = "https://paper-api.alpaca.markets"

    # Upstox (Indian market)
    UPSTOX_API_KEY: str = ""
    UPSTOX_SECRET_KEY: str = ""
    UPSTOX_ACCESS_TOKEN: str = ""
    UPSTOX_API_URL: str = "https://api.upstox.com/v2"
    
    # iTick API (for Indian market historical data)
    ITICK_API_KEY: str = ""
    ITICK_API_URL: str = "https://api.itick.in/api/v1"
    
    # Trading Settings
    PAPER_TRADING: bool = True
    DEFAULT_THRESHOLD: float = 80.0
    COOLDOWN_MINUTES: int = 30
    MAX_DAILY_LOSS: float = 5000.0
    MAX_POSITION_SIZE: float = 10000.0
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    @property
    def database_url(self) -> str:
        """Construct PostgreSQL database URL"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def redis_url(self) -> str:
        """Construct Redis URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
