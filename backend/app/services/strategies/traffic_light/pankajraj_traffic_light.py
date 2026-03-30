"""
Traffic Light Setup — Options Scalping Strategy
Based on the video strategy by Pankajraj Thakur.

Core Concept:
- Ignore the 9:15 opening candle (too volatile)
- Scan candles from 9:16 onwards for a RED + GREEN adjacent pair
- Mark the range: High of Green candle = upper boundary, Low of Red candle = lower boundary
- Wait for price to BREAK OUT of this range:
    - Break UP  → BUY  (call option)
    - Break DOWN → SELL (put option)
- Stop loss = other side of the range
"""

from dataclasses import dataclass
from typing import Literal, Optional

import numpy as np
import pandas as pd


# ─────────────────────────────────────────────
# Data Structures
# ─────────────────────────────────────────────

@dataclass
class Candle:
    timestamp: pd.Timestamp
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    @property
    def is_green(self) -> bool:
        return self.close >= self.open

    @property
    def is_red(self) -> bool:
        return self.close < self.open

    @property
    def body_size(self) -> float:
        return abs(self.close - self.open)

    @property
    def total_range(self) -> float:
        return self.high - self.low


@dataclass
class TrafficLightZone:
    red_candle_index: int
    green_candle_index: int
    red_timestamp: pd.Timestamp
    green_timestamp: pd.Timestamp
    zone_high: float
    zone_low: float
    zone_width: float
    pair_type: str


@dataclass
class TrafficLightSignal:
    direction: Literal["BUY", "SELL", "NO_SIGNAL"]
    entry_price: float = 0.0
    stop_loss: float = 0.0
    target: float = 0.0
    risk: float = 0.0
    zone: Optional[TrafficLightZone] = None
    reason: str = ""
    candle_index: int = 0
    timestamp: Optional[pd.Timestamp] = None


# ─────────────────────────────────────────────
# Traffic Light Zone Detection
# ─────────────────────────────────────────────

def is_opening_candle(candle: Candle, market_open_hour: int = 9, market_open_minute: int = 15) -> bool:
    return candle.timestamp.hour == market_open_hour and candle.timestamp.minute == market_open_minute


def find_traffic_light_zones(
    candles: list[Candle],
    skip_opening_candle: bool = True,
    min_body_ratio: float = 0.3,
) -> list[TrafficLightZone]:
    zones = []

    for i in range(1, len(candles)):
        prev = candles[i - 1]
        curr = candles[i]

        if skip_opening_candle and is_opening_candle(prev):
            continue

        if prev.total_range == 0 or curr.total_range == 0:
            continue

        prev_body_ok = prev.body_size / prev.total_range >= min_body_ratio
        curr_body_ok = curr.body_size / curr.total_range >= min_body_ratio

        if not (prev_body_ok and curr_body_ok):
            continue

        if prev.is_red and curr.is_green:
            zone_high = curr.high
            zone_low = prev.low
            if zone_high > zone_low:
                zones.append(TrafficLightZone(
                    red_candle_index=i - 1, green_candle_index=i,
                    red_timestamp=prev.timestamp, green_timestamp=curr.timestamp,
                    zone_high=zone_high, zone_low=zone_low, zone_width=zone_high - zone_low,
                    pair_type="RED_THEN_GREEN",
                ))

        elif prev.is_green and curr.is_red:
            zone_high = prev.high
            zone_low = curr.low
            if zone_high > zone_low:
                zones.append(TrafficLightZone(
                    red_candle_index=i, green_candle_index=i - 1,
                    red_timestamp=curr.timestamp, green_timestamp=prev.timestamp,
                    zone_high=zone_high, zone_low=zone_low, zone_width=zone_high - zone_low,
                    pair_type="GREEN_THEN_RED",
                ))

    return zones


def detect_breakout(
    candles: list[Candle],
    zone: TrafficLightZone,
    from_index: int,
    lookforward: int = 10,
    buffer_pct: float = 0.001,
) -> TrafficLightSignal:
    end_index = min(from_index + lookforward, len(candles))

    for i in range(from_index, end_index):
        candle = candles[i]

        if candle.close > zone.zone_high:
            entry = zone.zone_high
            stop_loss = zone.zone_low * (1 - buffer_pct)
            risk = entry - stop_loss
            target = entry + risk * 2

            return TrafficLightSignal(
                direction="BUY", entry_price=round(entry, 2),
                stop_loss=round(stop_loss, 2), target=round(target, 2),
                risk=round(risk, 2), zone=zone,
                reason=f"Breakout UP above zone high {zone.zone_high:.2f}",
                candle_index=i, timestamp=candle.timestamp,
            )

        elif candle.close < zone.zone_low:
            entry = zone.zone_low
            stop_loss = zone.zone_high * (1 + buffer_pct)
            risk = stop_loss - entry
            target = entry - risk * 2

            return TrafficLightSignal(
                direction="SELL", entry_price=round(entry, 2),
                stop_loss=round(stop_loss, 2), target=round(target, 2),
                risk=round(risk, 2), zone=zone,
                reason=f"Breakout DOWN below zone low {zone.zone_low:.2f}",
                candle_index=i, timestamp=candle.timestamp,
            )

    return TrafficLightSignal(direction="NO_SIGNAL", reason="No breakout")


def evaluate_for_registry(features: dict, sentiment_score: float = 0.0):
    """
    Adapter to fit into the standard strategy registry.
    We look for injected 'traffic_light_signal' data from indicators/pricing engine.
    """
    from app.services.strategies.base import StrategyResult

    signal_status = features.get("traffic_light_status", "NO_SIGNAL")
    zone_high = features.get("tl_zone_high", 0.0)
    zone_low = features.get("tl_zone_low", 0.0)

    score = 50.0
    direction = "HOLD"
    reason = "No Traffic Light breakout signal active"

    if signal_status == "BUY":
        score += 30.0
        direction = "BUY"
        reason = f"Traffic Light Breakout UP (Zone High: {zone_high})"
    elif signal_status == "SELL":
        score += 30.0
        direction = "SELL"
        reason = f"Traffic Light Breakout DOWN (Zone Low: {zone_low})"

    score += max(-5.0, min(5.0, sentiment_score * 5.0))

    return StrategyResult(
        name="pankajraj_traffic_light",
        score=score,
        direction=direction,
        reason=reason,
        metadata={
            "signal": signal_status,
            "zone_high": zone_high,
            "zone_low": zone_low,
        },
    )
