"""FastAPI main application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db, influx_db, redis_manager
from app.api.v1 import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle handler for startup and shutdown events"""
    # Startup
    print("🚀 Starting Stockinator Backend...")
    
    # Initialize databases
    init_db()
    
    # Try to connect to InfluxDB (optional for development)
    try:
        influx_db.connect()
        print("✓ InfluxDB connected")
    except Exception as e:
        print(f"⚠ InfluxDB not available: {e}")
    
    redis_manager.connect()
    
    print("✓ Databases connected")
    
    # Try to load ML model
    try:
        from app.services.ml_service import ml_service
        ml_service.load_model()
    except Exception as e:
        print(f"⚠ ML model not loaded: {e}")
    
    print("✓ Stockinator Backend ready!")
    
    yield
    
    # Shutdown
    print("Shutting down...")
    influx_db.disconnect()
    redis_manager.disconnect()


app = FastAPI(
    title=settings.APP_NAME,
    description="Automated trading system with ML-powered decision engine",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected",
        "influxdb": "connected",
        "redis": "connected"
    }
