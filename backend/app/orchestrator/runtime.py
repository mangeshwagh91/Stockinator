"""Central orchestrator: chains all agents in a DAG workflow.

DAG Flow: Scrape → Algo → Predict → Decide → Trade → Memory
Each step passes data to the next. Transparent decision gating at every stage.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional
import logging

from app.agents.scraping_agent import ScrapingAgent
from app.agents.algo_agent import AlgoAgent
from app.agents.prediction_agent import PredictionAgent
from app.agents.trade_agent import TradeAgent
from app.agents.memory_agent import MemoryAgent

logger = logging.getLogger(__name__)


@dataclass
class CycleResult:
    """Full result of one orchestrator cycle for a symbol."""
    symbol: str
    timestamp: str
    # Step 1: Scrape
    price: float = 0.0
    change: float = 0.0
    change_pct: float = 0.0
    news_sentiment: float = 50.0
    news_count: int = 0
    # Step 2: Algo
    algo_score: float = 50.0
    bullish_count: int = 0
    bearish_count: int = 0
    neutral_count: int = 0
    indicators: Dict[str, Any] = field(default_factory=dict)
    patterns: List[str] = field(default_factory=list)
    # Step 3: Predict
    success_score: float = 50.0
    ml_score: float = 50.0
    confidence_low: float = 45.0
    confidence_high: float = 55.0
    direction: str = "HOLD"
    # Step 4: Decision
    action: str = "HOLD"
    reasons: List[str] = field(default_factory=list)
    # Step 5: Trade (if executed)
    trade_executed: bool = False
    trade_side: str = ""
    trade_quantity: float = 0.0
    trade_entry: float = 0.0
    trade_sl: float = 0.0
    trade_tp: float = 0.0
    trade_status: str = ""
    # Meta
    cycle_steps: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class Orchestrator:
    """Coordinates the multi-agent DAG workflow with transparent decision gating."""

    def __init__(self, threshold: float = 75.0, paper: bool = True):
        self.threshold = threshold
        self.paper = paper
        self.scraper = ScrapingAgent()
        self.algo = AlgoAgent()
        self.predictor = PredictionAgent()
        self.trader = TradeAgent()
        self.memory = MemoryAgent()
        self._halted = False

    # ── Kill switch ──────────────────────────────────────────────────────

    def halt(self):
        self._halted = True
        logger.warning("ORCHESTRATOR HALTED — kill switch activated")

    def resume(self):
        self._halted = False
        logger.info("ORCHESTRATOR RESUMED")

    @property
    def is_halted(self) -> bool:
        return self._halted

    # ── Full cycle for one symbol ────────────────────────────────────────

    def run_cycle(self, symbol: str) -> CycleResult:
        """Run the complete agent cycle for a single symbol."""
        result = CycleResult(
            symbol=symbol,
            timestamp=datetime.utcnow().isoformat(),
        )

        if self._halted:
            result.action = "HALTED"
            result.reasons.append("System halted via kill switch")
            return result

        # ── Step 1: SCRAPE ───────────────────────────────────────────────
        try:
            snapshot = self.scraper.gather(symbol)
            result.price = snapshot.price
            result.change = snapshot.change
            result.change_pct = snapshot.change_pct
            result.cycle_steps.append("scrape_market_data")

            # History for indicators
            candles = self.scraper.gather_history(symbol, period="3mo", interval="1d")

            # News
            news_data = self.scraper.gather_news_sentiment(symbol)
            result.news_sentiment = news_data["sentiment"]
            result.news_count = news_data["count"]
            result.cycle_steps.append("scrape_news_sentiment")
        except Exception as e:
            result.errors.append(f"Scrape failed: {str(e)}")
            logger.error(f"Scrape failed for {symbol}: {e}")
            result.action = "ERROR"
            return result

        # ── Step 2: ALGO ─────────────────────────────────────────────────
        try:
            consensus = self.algo.compute_consensus(symbol, candles)
            result.algo_score = consensus.score
            result.bullish_count = consensus.bullish_count
            result.bearish_count = consensus.bearish_count
            result.neutral_count = consensus.neutral_count
            result.indicators = consensus.indicators
            result.patterns = consensus.patterns
            result.cycle_steps.append("compute_indicators")
            result.cycle_steps.append("detect_patterns")
        except Exception as e:
            result.errors.append(f"Algo failed: {str(e)}")
            logger.error(f"Algo failed for {symbol}: {e}")

        # ── Step 3: PREDICT ──────────────────────────────────────────────
        try:
            prediction = self.predictor.predict(
                symbol=symbol,
                indicator_features=result.indicators,
                algo_consensus_score=result.algo_score,
                news_sentiment=result.news_sentiment,
            )
            result.success_score = prediction.success_score
            result.ml_score = prediction.ml_score
            result.confidence_low = prediction.confidence_low
            result.confidence_high = prediction.confidence_high
            result.direction = prediction.direction
            result.cycle_steps.append("predict_success_score")
        except Exception as e:
            result.errors.append(f"Predict failed: {str(e)}")
            logger.error(f"Predict failed for {symbol}: {e}")

        # ── Step 4: DECIDE ───────────────────────────────────────────────
        if result.success_score < self.threshold:
            result.action = "HOLD"
            result.reasons.append(
                f"Score {result.success_score:.1f} below threshold {self.threshold}"
            )
            result.cycle_steps.append("decision_gate")
            return result

        # Cost check
        atr = result.indicators.get("atr", result.price * 0.02)
        quantity = 1.0  # Simplified: 1 lot
        trade_plan = self.trader.create_plan(
            symbol=symbol,
            side=result.direction,
            entry=result.price,
            atr=atr,
            quantity=quantity,
        )

        if not self.trader.should_execute(trade_plan):
            result.action = "HOLD"
            result.reasons.append("Expected profit below costs + minimum threshold")
            result.cycle_steps.append("cost_check_failed")
            return result

        result.action = result.direction
        result.reasons.append("All checks passed")
        result.cycle_steps.append("decision_approved")

        # ── Step 5: TRADE ────────────────────────────────────────────────
        try:
            execution = self.trader.execute(trade_plan, paper=self.paper)
            result.trade_executed = True
            result.trade_side = execution.side
            result.trade_quantity = execution.quantity
            result.trade_entry = execution.entry
            result.trade_sl = execution.stop_loss
            result.trade_tp = execution.take_profit
            result.trade_status = execution.status
            result.cycle_steps.append("execute_trade")
        except Exception as e:
            result.errors.append(f"Trade execution failed: {str(e)}")
            logger.error(f"Trade execution failed for {symbol}: {e}")

        # ── Step 6: MEMORY ───────────────────────────────────────────────
        try:
            self.memory.record(
                symbol=symbol,
                side=result.direction,
                entry=result.price,
                pnl=0.0,  # PnL unknown until trade closes
                success_score=result.success_score,
                algo_score=result.algo_score,
                news_score=result.news_sentiment,
                indicators=result.indicators,
                patterns=result.patterns,
            )
            result.cycle_steps.append("record_memory")
        except Exception as e:
            result.errors.append(f"Memory record failed: {str(e)}")

        return result

    # ── Run cycle for all watchlist symbols ───────────────────────────────

    def run_all(self, symbols: List[str]) -> List[CycleResult]:
        """Run the full agent cycle for a list of symbols."""
        results = []
        for sym in symbols:
            try:
                res = self.run_cycle(sym)
                results.append(res)
            except Exception as e:
                logger.error(f"Cycle failed for {sym}: {e}")
        return results

    # ── Agent health ─────────────────────────────────────────────────────

    def health(self) -> Dict[str, Any]:
        return {
            "orchestrator": "ready" if not self._halted else "halted",
            "threshold": self.threshold,
            "paper_trading": self.paper,
            "agents": {
                "scraper": self.scraper.health(),
                "algo": {"agent": self.algo.name, "status": "ready"},
                "predictor": {"agent": self.predictor.name, "status": "ready"},
                "trader": {"agent": self.trader.name, "status": "ready"},
                "memory": self.memory.health(),
            },
        }

    def to_dict(self, result: CycleResult) -> Dict[str, Any]:
        return asdict(result)
