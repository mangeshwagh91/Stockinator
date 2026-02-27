"""WebSocket endpoint for real-time updates"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json
import asyncio
from datetime import datetime

router = APIRouter()


class ConnectionManager:
    """Manager for WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific client"""
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        """Broadcast message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Connection might be closed
                pass
    
    async def broadcast_json(self, data: dict):
        """Broadcast JSON data to all connected clients"""
        message = json.dumps(data)
        await self.broadcast(message)


manager = ConnectionManager()


@router.websocket("/live")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for live trading updates"""
    await manager.connect(websocket)
    
    try:
        # Send initial connection message
        await manager.send_personal_message(
            json.dumps({
                "type": "connection",
                "status": "connected",
                "timestamp": datetime.now().isoformat()
            }),
            websocket
        )
        
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                        }),
                        websocket
                    )
                elif message.get("type") == "subscribe":
                    # Subscribe to specific symbols
                    symbols = message.get("symbols", [])
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "subscribed",
                            "symbols": symbols,
                            "timestamp": datetime.now().isoformat()
                        }),
                        websocket
                    )
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "message": "Invalid JSON"
                    }),
                    websocket
                )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client disconnected")


async def broadcast_score_update(symbol: str, score: float, features: dict):
    """Broadcast ML score update to all clients"""
    await manager.broadcast_json({
        "type": "score_update",
        "symbol": symbol,
        "score": score,
        "features": features,
        "timestamp": datetime.now().isoformat()
    })


async def broadcast_trade_execution(trade_data: dict):
    """Broadcast trade execution to all clients"""
    await manager.broadcast_json({
        "type": "trade_executed",
        "trade": trade_data,
        "timestamp": datetime.now().isoformat()
    })


async def broadcast_trade_closed(trade_data: dict):
    """Broadcast trade closure to all clients"""
    await manager.broadcast_json({
        "type": "trade_closed",
        "trade": trade_data,
        "timestamp": datetime.now().isoformat()
    })


async def broadcast_error(error_message: str):
    """Broadcast error to all clients"""
    await manager.broadcast_json({
        "type": "error",
        "message": error_message,
        "timestamp": datetime.now().isoformat()
    })
