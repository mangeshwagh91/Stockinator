"""Control endpoints for trading system parameters"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from app.api.dependencies import get_database
from app.services.decision_engine import decision_engine
from app.services.risk_manager import risk_manager
from app.core.config import settings

router = APIRouter()


class TradingParams(BaseModel):
    """Trading parameters"""
    threshold: Optional[float] = Field(None, ge=0, le=100)
    cooldown_minutes: Optional[int] = Field(None, ge=0)
    max_daily_loss: Optional[float] = Field(None, gt=0)
    max_position_size: Optional[float] = Field(None, gt=0)
    risk_per_trade: Optional[float] = Field(None, ge=0.001, le=0.1)
    max_open_positions: Optional[int] = Field(None, ge=1)


class TradingStatus(BaseModel):
    """Trading system status"""
    is_active: bool
    paper_trading: bool
    threshold: float
    cooldown_minutes: int


class SystemStatus(BaseModel):
    """Overall system status"""
    trading_active: bool
    paper_trading: bool
    threshold: float
    cooldown_minutes: int
    risk_metrics: dict
    broker_connected: bool


# Global trading state
trading_active = False


@router.get("/status", response_model=SystemStatus)
async def get_system_status(db: Session = Depends(get_database)):
    """Get current system status"""
    risk_metrics = risk_manager.get_risk_metrics(db)
    
    return SystemStatus(
        trading_active=trading_active,
        paper_trading=settings.PAPER_TRADING,
        threshold=decision_engine.threshold,
        cooldown_minutes=decision_engine.cooldown_minutes,
        risk_metrics=risk_metrics,
        broker_connected=True  # Could check actual connection
    )


@router.post("/start")
async def start_trading():
    """Start automated trading"""
    global trading_active
    
    if trading_active:
        raise HTTPException(status_code=400, detail="Trading already active")
    
    trading_active = True
    return {
        "message": "Trading started",
        "status": "active",
        "paper_trading": settings.PAPER_TRADING
    }


@router.post("/stop")
async def stop_trading():
    """Stop automated trading"""
    global trading_active
    
    if not trading_active:
        raise HTTPException(status_code=400, detail="Trading already stopped")
    
    trading_active = False
    return {
        "message": "Trading stopped",
        "status": "inactive"
    }


@router.get("/params", response_model=TradingParams)
async def get_trading_params():
    """Get current trading parameters"""
    return TradingParams(
        threshold=decision_engine.threshold,
        cooldown_minutes=decision_engine.cooldown_minutes,
        max_daily_loss=risk_manager.max_daily_loss,
        max_position_size=risk_manager.max_position_size,
        risk_per_trade=risk_manager.risk_per_trade,
        max_open_positions=risk_manager.max_open_positions
    )


@router.post("/params")
async def update_trading_params(params: TradingParams):
    """Update trading parameters"""
    updated = []
    
    if params.threshold is not None:
        decision_engine.set_threshold(params.threshold)
        updated.append("threshold")
    
    if params.cooldown_minutes is not None:
        decision_engine.set_cooldown(params.cooldown_minutes)
        updated.append("cooldown_minutes")
    
    risk_manager.update_limits(
        max_daily_loss=params.max_daily_loss,
        max_position_size=params.max_position_size,
        risk_per_trade=params.risk_per_trade,
        max_open_positions=params.max_open_positions
    )
    
    if params.max_daily_loss:
        updated.append("max_daily_loss")
    if params.max_position_size:
        updated.append("max_position_size")
    if params.risk_per_trade:
        updated.append("risk_per_trade")
    if params.max_open_positions:
        updated.append("max_open_positions")
    
    return {
        "message": "Parameters updated",
        "updated": updated,
        "current_params": {
            "threshold": decision_engine.threshold,
            "cooldown_minutes": decision_engine.cooldown_minutes,
            "max_daily_loss": risk_manager.max_daily_loss,
            "max_position_size": risk_manager.max_position_size,
            "risk_per_trade": risk_manager.risk_per_trade,
            "max_open_positions": risk_manager.max_open_positions
        }
    }


@router.get("/risk-metrics")
async def get_risk_metrics(db: Session = Depends(get_database)):
    """Get current risk metrics"""
    metrics = risk_manager.get_risk_metrics(db)
    return {
        "risk_metrics": metrics,
        "status": "within_limits" if metrics["daily_loss_used_pct"] < 100 else "limits_exceeded"
    }


@router.post("/test-mode/{enabled}")
async def set_test_mode(enabled: bool):
    """Enable/disable paper trading mode"""
    # Note: This would require restarting the broker service
    return {
        "message": f"Test mode {'enabled' if enabled else 'disabled'}",
        "note": "Requires service restart to take effect",
        "current_mode": "paper" if settings.PAPER_TRADING else "live"
    }
