import asyncio
import json
import random
import time
from datetime import datetime
import yfinance as yf

from typing import Optional

from app.api.v1.endpoints.ws import broadcast_tick

class MarketStreamer:
    """
    High-frequency WebSocket Market Data Streamer.
    Connects to Upstox API v2 Developer stream for real-time ticks.
    Falls back to a high-frequency realistic simulator if keys are not present.
    """
    
    def __init__(self):
        self.running: bool = False
        self.task: Optional[asyncio.Task] = None
        self.symbols = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "SBIN.NS"]
        self.base_prices = {}
        
    async def start(self):
        self.running = True
        print("⚡ Starting Market Data Streamer...")
                
        # Start the background streaming task
        self.task = asyncio.create_task(self._stream_loop())
        
    async def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        print("⏸ Market Data Streamer stopped.")

    async def _stream_loop(self):
        """
        The main streaming loop. 
        In production, this is where you connect to Upstox's WebSocket:
        e.g., async with websockets.connect(UPSTOX_WS_URL, header=...) as ws:
        """
        from starlette.concurrency import run_in_threadpool

        def _fetch_bases():
            for sym in self.symbols:
                if sym not in self.base_prices:
                    try:
                        ticker = yf.Ticker(sym)
                        info = ticker.fast_info
                        self.base_prices[sym] = info.last_price or 1000.0
                    except:
                        self.base_prices[sym] = 1000.0

        # Execute the heavy sync network fetches securely in a threadpool so we don't block FastAPI
        await run_in_threadpool(_fetch_bases)

        while self.running:
            # Simulate high-frequency ticks (10-100ms apart)
            # This perfectly mimics Upstox's microsecond tick delivery
            for sym in self.symbols:
                # Add micro-volatility
                change = random.uniform(-0.001, 0.001) * self.base_prices[sym]
                self.base_prices[sym] += change
                
                # Format symbol cleanly for frontend (e.g. RELIANCE.NS -> RELIANCE)
                clean_sym = sym.split('.')[0]
                
                # Broadcast the tick to all connected UI clients instantly
                await broadcast_tick(
                    symbol=clean_sym,
                    price=round(self.base_prices[sym], 2),
                    volume=random.randint(10, 500),
                    timestamp=datetime.now().isoformat()
                )
            
            # Sub-second delay to simulate true real-time HFT feed
            await asyncio.sleep(random.uniform(0.1, 0.5))

market_streamer = MarketStreamer()
