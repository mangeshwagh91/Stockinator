"""System-level endpoints for multi-agent orchestration.

Provides run-cycle, workflow info, memory recall, and agent health.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Query
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from app.orchestrator.runtime import Orchestrator

router = APIRouter()

# Global orchestrator instance
orchestrator = Orchestrator(threshold=75.0, paper=True)

# Watchlist of symbols to scan
WATCHLIST = [
    "NIFTY50", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY",
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK",
    "SBIN", "BHARTIARTL", "ITC", "HINDUNILVR", "KOTAKBANK",
    "LT", "AXISBANK", "BAJFINANCE", "MARUTI", "TATAMOTORS",
    "SUNPHARMA", "WIPRO", "HCLTECH", "ADANIENT", "ASIANPAINT",
    "TATASTEEL", "ULTRACEMCO", "TITAN", "POWERGRID",
]


# ── Run one full agent cycle for a symbol ────────────────────────────────

@router.post("/run-cycle/{symbol}")
async def run_cycle(symbol: str):
    """Run the complete Scrape → Algo → Predict → Decide → Trade → Memory cycle."""
    result = await run_in_threadpool(orchestrator.run_cycle, symbol.upper())
    return orchestrator.to_dict(result)


@router.post("/run-all")
async def run_all_cycles(
    symbols: Optional[List[str]] = None,
):
    """Run the agent cycle for all watchlist symbols (or a custom list)."""
    syms = symbols or WATCHLIST[:10]  # Default to first 10 to avoid timeout
    results = await run_in_threadpool(orchestrator.run_all, [s.upper() for s in syms])
    return {
        "count": len(results),
        "results": [orchestrator.to_dict(r) for r in results],
    }


# ── Legacy decision endpoint (backward compat) ──────────────────────────

class DecisionRequest(BaseModel):
    symbol: str = Field(..., min_length=1)
    last_price: float = Field(0, gt=0)
    bullish_patterns: int = Field(0, ge=0)
    bearish_patterns: int = Field(0, ge=0)
    xgboost_probability: float = Field(50, ge=0, le=100)
    news_sentiment: float = Field(50, ge=0, le=100)
    expected_profit: float = Field(100, gt=0)
    cost_estimate: float = Field(50, ge=0)
    daily_pnl: float = 0
    open_positions: int = Field(0, ge=0)
    cooldown_elapsed: bool = True
    position_size_within_limits: bool = True


@router.post("/decision")
async def evaluate_decision(payload: DecisionRequest):
    """Run the full agent cycle for the requested symbol (backward compatible)."""
    result = orchestrator.run_cycle(payload.symbol.upper())
    d = orchestrator.to_dict(result)
    # Reshape for backward compatibility with SystemControl page
    return {
        "snapshot": {
            "symbol": result.symbol,
            "price": result.price,
            "sentiment": result.news_sentiment,
            "timestamp": result.timestamp,
        },
        "indicator_consensus": {
            "score": result.algo_score,
            "bullish_patterns": result.bullish_count,
            "bearish_patterns": result.bearish_count,
        },
        "prediction": {
            "success_score": result.success_score,
            "confidence_low": result.confidence_low,
            "confidence_high": result.confidence_high,
        },
        "risk": {
            "halted": orchestrator.is_halted,
        },
        "decision": {
            "action": result.action,
            "reason": "; ".join(result.reasons) if result.reasons else "Cycle complete",
        },
        "trade": {
            "executed": result.trade_executed,
            "side": result.trade_side,
            "quantity": result.trade_quantity,
            "entry": result.trade_entry,
            "sl": result.trade_sl,
            "tp": result.trade_tp,
            "status": result.trade_status,
        },
        "patterns": result.patterns,
        "cycle_steps": result.cycle_steps,
    }


# ── Workflow info ────────────────────────────────────────────────────────

@router.get("/workflow")
async def get_workflow_summary():
    return {
        "motive": "Democratize autonomous, risk-first algorithmic trading for retail users.",
        "cycle": [
            "scrape_market_data",
            "scrape_news_sentiment",
            "compute_indicators",
            "detect_patterns",
            "predict_success_score",
            "decision_gate",
            "execute_trade",
            "record_memory",
        ],
        "agents": [
            "scraping_agent",
            "algo_agent",
            "prediction_agent",
            "trade_agent",
            "memory_agent",
        ],
        "timestamp": datetime.utcnow().isoformat(),
    }


# ── Kill switch ──────────────────────────────────────────────────────────

@router.post("/halt")
async def halt_system():
    orchestrator.halt()
    return {"status": "halted", "message": "Kill switch activated — all trading stopped"}


@router.post("/resume")
async def resume_system():
    orchestrator.resume()
    return {"status": "active", "message": "System resumed"}


# ── Memory / learning endpoints ──────────────────────────────────────────

@router.get("/memory/recent")
async def recent_memories(limit: int = 20):
    return {"items": orchestrator.memory.recent(limit=limit)}


@router.get("/memory/win-rate")
async def memory_win_rate(symbol: Optional[str] = None):
    return orchestrator.memory.win_rate(symbol)


# ── Agent health ─────────────────────────────────────────────────────────

@router.get("/health")
async def agent_health():
    return orchestrator.health()
