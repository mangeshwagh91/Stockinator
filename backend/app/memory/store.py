"""In-memory adapter for learning records (replace with Neo4j/vector DB in prod)."""

from collections import deque
from typing import Any


class TradeMemoryStore:
    """Small ring buffer used for recent trade learning snapshots."""

    def __init__(self, capacity: int = 200):
        self._memory = deque(maxlen=capacity)

    def add(self, record: dict[str, Any]) -> None:
        self._memory.append(record)

    def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        return list(self._memory)[-limit:]
