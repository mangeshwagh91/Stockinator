"""Vision Agent: chart pattern recognition via computer vision.

Pipeline:
  1. Render OHLCV candles to a matplotlib figure → PNG bytes
  2. Preprocess image (resize, normalize)
  3. Run through a lightweight CNN classifier (ResNet-18 or rule-based fallback)
  4. Output a structured VisionSignal with pattern label + confidence

Supported patterns (8 classes):
  0 head_and_shoulders   (bearish reversal)
  1 inverse_head_and_shoulders (bullish reversal)
  2 double_top           (bearish reversal)
  3 double_bottom        (bullish reversal)
  4 ascending_triangle   (bullish continuation)
  5 descending_triangle  (bearish continuation)
  6 cup_and_handle       (bullish continuation)
  7 no_pattern           (neutral)
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ── Optional heavy imports (graceful degradation) ─────────────────────────────

try:
    import matplotlib
    matplotlib.use("Agg")  # non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    _MPL_OK = True
except ImportError:
    _MPL_OK = False
    logger.warning("matplotlib not installed — vision agent will use fallback scoring only")

try:
    import cv2  # type: ignore
    _CV2_OK = True
except ImportError:
    _CV2_OK = False

try:
    import torch  # type: ignore
    import torch.nn as nn  # type: ignore
    from torchvision import models as tv_models  # type: ignore
    from torchvision import transforms as T  # type: ignore
    _TORCH_OK = True
except ImportError:
    _TORCH_OK = False

# ── Constants ─────────────────────────────────────────────────────────────────

PATTERN_LABELS = [
    "head_and_shoulders",
    "inverse_head_and_shoulders",
    "double_top",
    "double_bottom",
    "ascending_triangle",
    "descending_triangle",
    "cup_and_handle",
    "no_pattern",
]

PATTERN_DIRECTION = {
    "head_and_shoulders": "SELL",
    "inverse_head_and_shoulders": "BUY",
    "double_top": "SELL",
    "double_bottom": "BUY",
    "ascending_triangle": "BUY",
    "descending_triangle": "SELL",
    "cup_and_handle": "BUY",
    "no_pattern": "HOLD",
}

IMG_SIZE = 224  # ResNet input size
NUM_CLASSES = len(PATTERN_LABELS)


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class VisionSignal:
    symbol: str
    pattern: str                     # one of PATTERN_LABELS
    direction: str                   # BUY / SELL / HOLD
    confidence: float                # 0.0 – 1.0
    vision_score: float              # 0 – 100 (for orchestrator compatibility)
    secondary_patterns: List[str] = field(default_factory=list)
    model_used: str = "rule_based"   # "cnn" | "rule_based"
    chart_available: bool = False


# ── CNN model wrapper ─────────────────────────────────────────────────────────

class ChartPatternCNN:
    """Thin wrapper around ResNet-18 fine-tuned for chart pattern classification."""

    def __init__(self, weights_path: Optional[str] = None):
        self.model: Optional[Any] = None
        self.transform: Optional[Any] = None
        self._loaded = False

        if not _TORCH_OK:
            logger.warning("PyTorch not installed — CNN classifier unavailable")
            return

        self._build_model(weights_path)

    def _build_model(self, weights_path: Optional[str]) -> None:
        """Build ResNet-18 with a custom head for NUM_CLASSES outputs."""
        try:
            model = tv_models.resnet18(weights=None)
            model.fc = nn.Linear(model.fc.in_features, NUM_CLASSES)

            if weights_path:
                import torch
                state = torch.load(weights_path, map_location="cpu")
                model.load_state_dict(state)
                logger.info(f"VisionAgent: loaded CNN weights from {weights_path}")
            else:
                logger.info("VisionAgent: no weights provided — using random-init CNN (rule-based fallback preferred)")

            model.eval()
            self.model = model

            self.transform = T.Compose([
                T.ToPILImage(),
                T.Resize((IMG_SIZE, IMG_SIZE)),
                T.ToTensor(),
                T.Normalize(mean=[0.485, 0.456, 0.406],
                            std=[0.229, 0.224, 0.225]),
            ])
            self._loaded = bool(weights_path)
        except Exception as exc:
            logger.error(f"VisionAgent: CNN build failed: {exc}")

    def predict(self, image_bgr: np.ndarray) -> Tuple[str, float]:
        """
        Run inference on a BGR image array.

        Returns:
            (pattern_label, confidence)
        """
        if not self._loaded or self.model is None:
            return "no_pattern", 0.5

        try:
            import torch
            rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB) if _CV2_OK else image_bgr
            tensor = self.transform(rgb).unsqueeze(0)   # [1, 3, H, W]
            with torch.no_grad():
                logits = self.model(tensor)              # [1, NUM_CLASSES]
                probs = torch.softmax(logits, dim=1)[0]
            idx = int(probs.argmax())
            return PATTERN_LABELS[idx], float(probs[idx])
        except Exception as exc:
            logger.error(f"VisionAgent CNN inference error: {exc}")
            return "no_pattern", 0.5


# ── Chart renderer ────────────────────────────────────────────────────────────

def _render_chart(candles: List[Dict], symbol: str, lookback: int = 60) -> Optional[np.ndarray]:
    """
    Render the last `lookback` OHLCV candles to a PNG and return as a BGR ndarray.
    Returns None when matplotlib or cv2 is unavailable.
    """
    if not _MPL_OK:
        return None

    data = candles[-lookback:] if len(candles) >= lookback else candles
    if not data:
        return None

    closes = [c["close"] for c in data]
    highs = [c["high"] for c in data]
    lows = [c["low"] for c in data]
    opens = [c["open"] for c in data]
    xs = range(len(data))

    fig, ax = plt.subplots(figsize=(8, 4), dpi=56)   # 448 × 224 px
    ax.set_facecolor("#0d1117")
    fig.patch.set_facecolor("#0d1117")

    for i, (o, c, h, l) in enumerate(zip(opens, closes, highs, lows)):
        color = "#26a69a" if c >= o else "#ef5350"
        # Candle body
        ax.bar(i, abs(c - o), bottom=min(o, c), color=color, width=0.6)
        # Wick
        ax.plot([i, i], [l, h], color=color, linewidth=0.8)

    # SMA-20 overlay
    if len(closes) >= 20:
        sma = pd.Series(closes).rolling(20).mean().values
        ax.plot(xs, sma, color="#f0a500", linewidth=1.0, label="SMA20")

    ax.set_title(symbol, color="white", fontsize=9)
    ax.tick_params(colors="gray", labelsize=6)
    for spine in ax.spines.values():
        spine.set_edgecolor("#333")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    buf.seek(0)

    img_array = np.frombuffer(buf.read(), dtype=np.uint8)
    if _CV2_OK:
        bgr = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        return bgr

    # Fallback: return raw PNG bytes wrapped as 1-D array (triggers rule-based path)
    return None


# ── Rule-based fallback analyser ──────────────────────────────────────────────

class RuleBasedPatternAnalyser:
    """
    Detects chart patterns from OHLCV arrays using classical signal processing.
    No ML required — fast & dependency-free.
    """

    @staticmethod
    def analyse(candles: List[Dict], lookback: int = 60) -> Tuple[str, float, List[str]]:
        """
        Returns: (primary_pattern, confidence, secondary_patterns)
        """
        data = candles[-lookback:] if len(candles) >= lookback else candles
        if len(data) < 20:
            return "no_pattern", 0.5, []

        closes = np.array([c["close"] for c in data], dtype=float)
        highs = np.array([c["high"] for c in data], dtype=float)
        lows = np.array([c["low"] for c in data], dtype=float)

        patterns_found: Dict[str, float] = {}

        # ── 1. Head & Shoulders / Inverse H&S ───────────────────────────────
        hs_conf = RuleBasedPatternAnalyser._check_head_and_shoulders(closes, highs)
        if hs_conf > 0:
            if hs_conf > 0:
                patterns_found["head_and_shoulders"] = hs_conf
        ihs_conf = RuleBasedPatternAnalyser._check_inverse_hs(closes, lows)
        if ihs_conf > 0:
            patterns_found["inverse_head_and_shoulders"] = ihs_conf

        # ── 2. Double Top / Double Bottom ────────────────────────────────────
        dt_conf = RuleBasedPatternAnalyser._check_double_top(highs)
        if dt_conf > 0:
            patterns_found["double_top"] = dt_conf
        db_conf = RuleBasedPatternAnalyser._check_double_bottom(lows)
        if db_conf > 0:
            patterns_found["double_bottom"] = db_conf

        # ── 3. Ascending / Descending Triangle ───────────────────────────────
        at_conf = RuleBasedPatternAnalyser._check_ascending_triangle(highs, lows, closes)
        if at_conf > 0:
            patterns_found["ascending_triangle"] = at_conf
        desc_t = RuleBasedPatternAnalyser._check_descending_triangle(highs, lows, closes)
        if desc_t > 0:
            patterns_found["descending_triangle"] = desc_t

        # ── 4. Cup and Handle ────────────────────────────────────────────────
        cah_conf = RuleBasedPatternAnalyser._check_cup_and_handle(closes)
        if cah_conf > 0:
            patterns_found["cup_and_handle"] = cah_conf

        if not patterns_found:
            return "no_pattern", 0.4, []

        primary = max(patterns_found, key=lambda k: patterns_found[k])
        conf = round(patterns_found.pop(primary), 3)
        secondary = list(patterns_found.keys())
        return primary, conf, secondary

    # ── Individual pattern detectors ──────────────────────────────────────────

    @staticmethod
    def _local_peaks(arr: np.ndarray, order: int = 5) -> np.ndarray:
        from scipy.signal import argrelextrema  # type: ignore
        try:
            peaks = argrelextrema(arr, np.greater, order=order)[0]
        except Exception:
            peaks = np.array([i for i in range(order, len(arr) - order)
                              if arr[i] == max(arr[i - order:i + order + 1])])
        return peaks

    @staticmethod
    def _local_troughs(arr: np.ndarray, order: int = 5) -> np.ndarray:
        from scipy.signal import argrelextrema  # type: ignore
        try:
            troughs = argrelextrema(arr, np.less, order=order)[0]
        except Exception:
            troughs = np.array([i for i in range(order, len(arr) - order)
                                if arr[i] == min(arr[i - order:i + order + 1])])
        return troughs

    @staticmethod
    def _check_head_and_shoulders(closes: np.ndarray, highs: np.ndarray) -> float:
        peaks = RuleBasedPatternAnalyser._local_peaks(highs, order=4)
        if len(peaks) < 3:
            return 0.0
        l, h, r = peaks[-3], peaks[-2], peaks[-1]
        left_h, head_h, right_h = highs[l], highs[h], highs[r]
        if head_h > left_h and head_h > right_h:
            shoulder_symmetry = 1 - abs(left_h - right_h) / head_h
            if shoulder_symmetry > 0.85:
                return round(0.55 + shoulder_symmetry * 0.3, 3)
        return 0.0

    @staticmethod
    def _check_inverse_hs(closes: np.ndarray, lows: np.ndarray) -> float:
        troughs = RuleBasedPatternAnalyser._local_troughs(lows, order=4)
        if len(troughs) < 3:
            return 0.0
        l, h, r = troughs[-3], troughs[-2], troughs[-1]
        left_l, head_l, right_l = lows[l], lows[h], lows[r]
        if head_l < left_l and head_l < right_l:
            symmetry = 1 - abs(left_l - right_l) / max(abs(left_l), 0.01)
            if symmetry > 0.85:
                return round(0.55 + symmetry * 0.3, 3)
        return 0.0

    @staticmethod
    def _check_double_top(highs: np.ndarray) -> float:
        peaks = RuleBasedPatternAnalyser._local_peaks(highs, order=5)
        if len(peaks) < 2:
            return 0.0
        p1, p2 = peaks[-2], peaks[-1]
        gap = abs(p2 - p1)
        if gap < 5:
            return 0.0
        h1, h2 = highs[p1], highs[p2]
        similarity = 1 - abs(h1 - h2) / max(h1, 0.01)
        if similarity > 0.97:
            return round(0.6 + similarity * 0.25, 3)
        return 0.0

    @staticmethod
    def _check_double_bottom(lows: np.ndarray) -> float:
        troughs = RuleBasedPatternAnalyser._local_troughs(lows, order=5)
        if len(troughs) < 2:
            return 0.0
        t1, t2 = troughs[-2], troughs[-1]
        if abs(t2 - t1) < 5:
            return 0.0
        l1, l2 = lows[t1], lows[t2]
        similarity = 1 - abs(l1 - l2) / max(l1, 0.01)
        if similarity > 0.97:
            return round(0.6 + similarity * 0.25, 3)
        return 0.0

    @staticmethod
    def _check_ascending_triangle(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> float:
        n = len(highs)
        if n < 15:
            return 0.0
        recent_highs = highs[-15:]
        recent_lows = lows[-15:]
        high_std = np.std(recent_highs) / (np.mean(recent_highs) + 1e-9)
        # Flat resistance + rising support
        xs = np.arange(15)
        low_slope = np.polyfit(xs, recent_lows, 1)[0]
        if high_std < 0.02 and low_slope > 0:
            return round(0.55 + min(low_slope / np.mean(recent_lows) * 500, 0.3), 3)
        return 0.0

    @staticmethod
    def _check_descending_triangle(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> float:
        n = len(lows)
        if n < 15:
            return 0.0
        recent_highs = highs[-15:]
        recent_lows = lows[-15:]
        low_std = np.std(recent_lows) / (np.mean(recent_lows) + 1e-9)
        xs = np.arange(15)
        high_slope = np.polyfit(xs, recent_highs, 1)[0]
        if low_std < 0.02 and high_slope < 0:
            return round(0.55 + min(abs(high_slope) / np.mean(recent_highs) * 500, 0.3), 3)
        return 0.0

    @staticmethod
    def _check_cup_and_handle(closes: np.ndarray) -> float:
        n = len(closes)
        if n < 30:
            return 0.0
        cup = closes[-30:-5]
        handle = closes[-5:]
        cup_min = cup.min()
        cup_left = cup[:5].mean()
        cup_right = cup[-5:].mean()
        handle_mean = handle.mean()
        # U-shaped cup + flat/slight downward handle
        if (cup_left > cup_min * 1.05 and
                cup_right > cup_min * 1.05 and
                abs(cup_left - cup_right) / cup_left < 0.05 and
                handle_mean >= cup_right * 0.97):
            return 0.65
        return 0.0


# ── Main Vision Agent ─────────────────────────────────────────────────────────

class VisionAgent:
    """
    Chart-pattern recognition agent.

    Usage:
        agent = VisionAgent(weights_path="backend/models/vision_v1.pt")
        signal = agent.analyse(symbol, candles)

    Output signal is compatible with the Orchestrator's CycleResult:
        signal.vision_score   → 0-100
        signal.direction      → BUY / SELL / HOLD
        signal.pattern        → human-readable label
        signal.confidence     → 0.0–1.0
    """

    name = "vision-agent"

    def __init__(self, weights_path: Optional[str] = None):
        self.cnn = ChartPatternCNN(weights_path) if _TORCH_OK else None
        self.rule_analyser = RuleBasedPatternAnalyser()
        self._weights_loaded = bool(weights_path and self.cnn and self.cnn._loaded)

    # ── Public API ────────────────────────────────────────────────────────────

    def analyse(self, symbol: str, candles: List[Dict]) -> VisionSignal:
        """
        Analyse candles and return a VisionSignal.

        Priority:
          1. CNN (if weights are loaded + dependencies available)
          2. Rule-based fallback (always available)
        """
        if len(candles) < 10:
            return VisionSignal(
                symbol=symbol,
                pattern="no_pattern",
                direction="HOLD",
                confidence=0.4,
                vision_score=40.0,
                model_used="rule_based",
            )

        if self._weights_loaded and _CV2_OK and _TORCH_OK:
            return self._run_cnn(symbol, candles)
        return self._run_rules(symbol, candles)

    def health(self) -> Dict[str, Any]:
        return {
            "agent": self.name,
            "status": "ready",
            "mode": "cnn" if self._weights_loaded else "rule_based",
            "dependencies": {
                "matplotlib": _MPL_OK,
                "opencv": _CV2_OK,
                "pytorch": _TORCH_OK,
            },
        }

    # ── Internal runners ──────────────────────────────────────────────────────

    def _run_cnn(self, symbol: str, candles: List[Dict]) -> VisionSignal:
        image = _render_chart(candles, symbol)
        if image is None:
            return self._run_rules(symbol, candles)

        pattern, conf = self.cnn.predict(image)
        direction = PATTERN_DIRECTION.get(pattern, "HOLD")
        vscore = self._score(pattern, conf)

        return VisionSignal(
            symbol=symbol,
            pattern=pattern,
            direction=direction,
            confidence=conf,
            vision_score=vscore,
            model_used="cnn",
            chart_available=True,
        )

    def _run_rules(self, symbol: str, candles: List[Dict]) -> VisionSignal:
        pattern, conf, secondary = self.rule_analyser.analyse(candles)
        direction = PATTERN_DIRECTION.get(pattern, "HOLD")
        vscore = self._score(pattern, conf)

        return VisionSignal(
            symbol=symbol,
            pattern=pattern,
            direction=direction,
            confidence=conf,
            vision_score=vscore,
            secondary_patterns=secondary,
            model_used="rule_based",
            chart_available=_MPL_OK,
        )

    @staticmethod
    def _score(pattern: str, conf: float) -> float:
        """Map pattern + confidence to 0-100 orchestrator score."""
        if pattern == "no_pattern":
            return 40.0
        base = 55.0 if PATTERN_DIRECTION.get(pattern) == "BUY" else 30.0
        return round(min(100.0, base + conf * 35), 1)


# ── Singleton ─────────────────────────────────────────────────────────────────
vision_agent = VisionAgent()
