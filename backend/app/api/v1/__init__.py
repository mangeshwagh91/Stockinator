"""API v1 router"""
from fastapi import APIRouter

from app.api.v1.endpoints import control, data, system, trades, ws

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(data.router, prefix="/data", tags=["market-data"])
api_router.include_router(trades.router, prefix="/trades", tags=["trades"])
api_router.include_router(control.router, prefix="/control", tags=["control"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(ws.router, prefix="/ws", tags=["websocket"])
