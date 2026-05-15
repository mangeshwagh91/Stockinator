"""Agent package for the multi-agent trading workflow."""

from app.agents.algo_agent import AlgoAgent
from app.agents.memory_agent import MemoryAgent
from app.agents.prediction_agent import PredictionAgent
from app.agents.scraping_agent import ScrapingAgent
from app.agents.trade_agent import TradeAgent
from app.agents.vision_agent import VisionAgent

__all__ = [
    "ScrapingAgent",
    "AlgoAgent",
    "PredictionAgent",
    "TradeAgent",
    "MemoryAgent",
    "VisionAgent",
]
