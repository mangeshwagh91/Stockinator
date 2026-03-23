"""Memory agent: persistent trade learning and pattern recall.

Uses JSON file storage as a lightweight alternative to Neo4j.
Stores trade outcomes with context for future pattern matching.
"""

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path


@dataclass
class TradeMemory:
    symbol: str
    side: str
    entry: float
    exit: Optional[float]
    pnl: float
    success_score: float
    algo_score: float
    news_score: float
    indicators: Dict[str, Any]
    patterns: List[str]
    regime: str           # "trending", "ranging", "volatile"
    outcome: str          # "win", "loss", "breakeven"
    timestamp: str


class MemoryAgent:
    """Stores and retrieves normalized trade memories for continual learning."""

    name = "memory-agent"

    def __init__(self, storage_path: str = "backend/models/trade_memory.json"):
        self._path = Path(storage_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._memories: List[Dict] = self._load()

    def _load(self) -> List[Dict]:
        if self._path.exists():
            try:
                with open(self._path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def _save(self):
        try:
            with open(self._path, "w") as f:
                json.dump(self._memories[-500:], f, indent=2, default=str)
        except IOError:
            pass

    def record(
        self,
        symbol: str,
        side: str,
        entry: float,
        pnl: float,
        success_score: float,
        algo_score: float,
        news_score: float,
        indicators: Dict[str, Any],
        patterns: List[str],
        exit_price: Optional[float] = None,
    ) -> TradeMemory:
        """Record a completed trade with full context."""
        # Detect regime from indicators
        adx = indicators.get("adx", 20)
        atr = indicators.get("atr", 0)
        bb_width = indicators.get("bb_width", 0)
        if adx > 25:
            regime = "trending"
        elif bb_width > 5:
            regime = "volatile"
        else:
            regime = "ranging"

        outcome = "breakeven"
        if pnl > 0:
            outcome = "win"
        elif pnl < 0:
            outcome = "loss"

        memory = TradeMemory(
            symbol=symbol,
            side=side,
            entry=entry,
            exit=exit_price,
            pnl=round(pnl, 2),
            success_score=success_score,
            algo_score=algo_score,
            news_score=news_score,
            indicators=indicators,
            patterns=patterns,
            regime=regime,
            outcome=outcome,
            timestamp=datetime.utcnow().isoformat(),
        )
        self._memories.append(asdict(memory))
        self._save()
        return memory

    def recall_similar(self, symbol: str, regime: str, limit: int = 5) -> List[Dict]:
        """Find past trades with similar conditions for learning."""
        matches = [
            m for m in self._memories
            if m.get("symbol") == symbol or m.get("regime") == regime
        ]
        return sorted(matches, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]

    def win_rate(self, symbol: Optional[str] = None) -> Dict[str, float]:
        """Calculate win rate overall or for a specific symbol."""
        filtered = self._memories
        if symbol:
            filtered = [m for m in filtered if m.get("symbol") == symbol]
        if not filtered:
            return {"trades": 0, "win_rate": 0.0, "avg_pnl": 0.0}

        wins = sum(1 for m in filtered if m.get("outcome") == "win")
        total_pnl = sum(m.get("pnl", 0) for m in filtered)
        return {
            "trades": len(filtered),
            "win_rate": round(wins / len(filtered) * 100, 1),
            "avg_pnl": round(total_pnl / len(filtered), 2),
        }

    def recent(self, limit: int = 20) -> List[Dict]:
        """Get recent trade memories."""
        return self._memories[-limit:]

    def all_memories(self) -> List[Dict]:
        return self._memories

    def health(self) -> Dict[str, Any]:
        return {
            "agent": self.name,
            "status": "ready",
            "memory_count": len(self._memories),
            "storage": str(self._path),
        }
