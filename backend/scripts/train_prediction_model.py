"""Train the XGBoost success-score model for PredictionAgent.

Run from the project root:
    cd backend
    python scripts/train_prediction_model.py

Outputs:
    backend/models/prediction_v1.pkl   ← loaded by MLService at startup
    backend/models/train_report.json   ← accuracy / feature-importance summary

Dataset:
    Downloads 1-year daily OHLCV for ~30 NSE blue-chips via yfinance.
    Labels a candle as SUCCESS=1 if the next-5-day return > +1.5%.
    Features: 20+ technical indicators (same set as indicator_service.py).
"""

import json
import logging
import os
import pickle
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    roc_auc_score,
)
import xgboost as xgb

# ── Ensure app imports work when run from scripts/ ────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger("train")

# ── Config ────────────────────────────────────────────────────────────────────

NSE_SYMBOLS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "HINDUNILVR.NS", "KOTAKBANK.NS",
    "LT.NS", "AXISBANK.NS", "BAJFINANCE.NS", "MARUTI.NS", "TATAMOTORS.NS",
    "SUNPHARMA.NS", "WIPRO.NS", "HCLTECH.NS", "ASIANPAINT.NS", "TITAN.NS",
    "TATASTEEL.NS", "ULTRACEMCO.NS", "POWERGRID.NS", "NTPC.NS", "ONGC.NS",
    "BPCL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "DIVISLAB.NS", "DRREDDY.NS",
]

PERIOD = "1y"          # 1 year of daily data
FORWARD_DAYS = 5       # predict 5-day ahead return
SUCCESS_THRESHOLD = 1.5  # % gain to label as SUCCESS=1

MODEL_DIR = BACKEND_DIR / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_PKL = MODEL_DIR / "prediction_v1.pkl"
OUTPUT_REPORT = MODEL_DIR / "train_report.json"


# ── Feature engineering ───────────────────────────────────────────────────────

def _ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()

def _sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n).mean()

def _rsi(s: pd.Series, n: int = 14) -> pd.Series:
    delta = s.diff()
    gain = delta.clip(lower=0).rolling(n).mean()
    loss = (-delta.clip(upper=0)).rolling(n).mean()
    rs = gain / (loss + 1e-9)
    return 100 - 100 / (1 + rs)

def _atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(n).mean()

def _macd(s: pd.Series) -> Tuple[pd.Series, pd.Series]:
    fast = _ema(s, 12)
    slow = _ema(s, 26)
    macd_line = fast - slow
    signal = _ema(macd_line, 9)
    return macd_line, signal

def _bollinger(s: pd.Series, n: int = 20) -> Tuple[pd.Series, pd.Series, pd.Series]:
    mid = _sma(s, n)
    std = s.rolling(n).std()
    upper = mid + 2 * std
    lower = mid - 2 * std
    return upper, mid, lower

def _stochastic(df: pd.DataFrame, k: int = 14, d: int = 3) -> Tuple[pd.Series, pd.Series]:
    low_min = df["low"].rolling(k).min()
    high_max = df["high"].rolling(k).max()
    sto_k = 100 * (df["close"] - low_min) / (high_max - low_min + 1e-9)
    sto_d = sto_k.rolling(d).mean()
    return sto_k, sto_d

def _cci(df: pd.DataFrame, n: int = 20) -> pd.Series:
    tp = (df["high"] + df["low"] + df["close"]) / 3
    sma_tp = tp.rolling(n).mean()
    mad = tp.rolling(n).apply(lambda x: np.mean(np.abs(x - x.mean())), raw=True)
    return (tp - sma_tp) / (0.015 * mad + 1e-9)

def _williams_r(df: pd.DataFrame, n: int = 14) -> pd.Series:
    high_max = df["high"].rolling(n).max()
    low_min = df["low"].rolling(n).min()
    return -100 * (high_max - df["close"]) / (high_max - low_min + 1e-9)

def _adx(df: pd.DataFrame, n: int = 14) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    up = high.diff()
    down = -low.diff()
    plus_dm = up.where((up > down) & (up > 0), 0.0)
    minus_dm = down.where((down > up) & (down > 0), 0.0)
    atr = _atr(df, n)
    plus_di = 100 * _ema(plus_dm, n) / (atr + 1e-9)
    minus_di = 100 * _ema(minus_dm, n) / (atr + 1e-9)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-9)
    return dx.rolling(n).mean()

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame of 25 features (same names as indicator_service)."""
    c = df["close"]
    feat = pd.DataFrame(index=df.index)

    # Trend
    feat["rsi"] = _rsi(c)
    feat["rsi_14"] = _rsi(c, 14)
    feat["macd"], feat["macd_signal"] = _macd(c)
    feat["macd_hist"] = feat["macd"] - feat["macd_signal"]
    feat["adx"] = _adx(df)

    # Moving averages
    sma20 = _sma(c, 20)
    sma50 = _sma(c, 50)
    sma200 = _sma(c, 200)
    feat["price_to_sma20"] = c / (sma20 + 1e-9)
    feat["price_to_sma50"] = c / (sma50 + 1e-9)
    feat["sma20_to_sma50"] = sma20 / (sma50 + 1e-9)
    feat["sma50_to_sma200"] = sma50 / (sma200 + 1e-9)

    # Volatility
    upper, mid, lower = _bollinger(c)
    bb_width = (upper - lower) / (mid + 1e-9)
    feat["bollinger_position"] = (c - lower) / (upper - lower + 1e-9)
    feat["bb_width"] = bb_width
    feat["atr"] = _atr(df)
    feat["atr_pct"] = feat["atr"] / (c + 1e-9)

    # Momentum
    feat["stochastic_k"], feat["stochastic_d"] = _stochastic(df)
    feat["williams_r"] = _williams_r(df)
    feat["cci"] = _cci(df)
    feat["roc_5"] = c.pct_change(5) * 100
    feat["roc_20"] = c.pct_change(20) * 100

    # Volume
    if "volume" in df.columns:
        vol_sma = df["volume"].rolling(20).mean()
        feat["volume_ratio"] = df["volume"] / (vol_sma + 1e-9)
    else:
        feat["volume_ratio"] = 1.0

    # Candle body
    feat["body_pct"] = (df["close"] - df["open"]).abs() / (df["high"] - df["low"] + 1e-9)

    # Sentiment placeholder (will be added at predict time by PredictionAgent)
    feat["sentiment_score"] = 0.0

    return feat


def build_label(df: pd.DataFrame) -> pd.Series:
    """1 if forward FORWARD_DAYS return > SUCCESS_THRESHOLD%, else 0."""
    fwd_return = df["close"].shift(-FORWARD_DAYS) / df["close"] - 1
    return (fwd_return * 100 >= SUCCESS_THRESHOLD).astype(int)


# ── Data download ─────────────────────────────────────────────────────────────

def download_data() -> pd.DataFrame:
    log.info(f"Downloading {PERIOD} daily data for {len(NSE_SYMBOLS)} NSE symbols…")
    all_frames: List[pd.DataFrame] = []

    for sym in NSE_SYMBOLS:
        try:
            raw = yf.download(sym, period=PERIOD, interval="1d",
                              auto_adjust=True, progress=False)
            if raw.empty or len(raw) < 210:
                log.warning(f"  ⚠  {sym}: insufficient rows ({len(raw)})")
                continue
            raw.columns = [c.lower() for c in raw.columns]
            raw = raw[["open", "high", "low", "close", "volume"]].dropna()
            raw["symbol"] = sym
            all_frames.append(raw)
            log.info(f"  ✓  {sym}: {len(raw)} rows")
        except Exception as exc:
            log.warning(f"  ⚠  {sym}: {exc}")

    if not all_frames:
        raise RuntimeError("No data downloaded — check internet connectivity.")

    combined = pd.concat(all_frames)
    log.info(f"Total rows: {len(combined)}")
    return combined


# ── Training ──────────────────────────────────────────────────────────────────

def train(df: pd.DataFrame) -> Tuple[xgb.XGBClassifier, StandardScaler, List[str], Dict]:
    """Build feature matrix, train XGBoost, cross-validate, return artefacts."""
    feat_frames: List[pd.DataFrame] = []
    label_frames: List[pd.Series] = []

    for sym, grp in df.groupby("symbol"):
        grp = grp.sort_index().drop(columns=["symbol"])
        feats = build_features(grp)
        labels = build_label(grp)

        # Drop rows with NaN features or NaN label (last FORWARD_DAYS rows)
        combined = feats.join(labels.rename("label")).dropna()
        feat_frames.append(combined.drop(columns=["label"]))
        label_frames.append(combined["label"])

    X = pd.concat(feat_frames).reset_index(drop=True)
    y = pd.concat(label_frames).reset_index(drop=True)

    feature_names = X.columns.tolist()
    log.info(f"Feature matrix: {X.shape},  Positive rate: {y.mean():.2%}")

    # Scale
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # XGBoost
    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=5,
        scale_pos_weight=(y == 0).sum() / (y == 1).sum(),
        eval_metric="logloss",
        use_label_encoder=False,
        random_state=42,
        n_jobs=-1,
    )

    # 5-fold cross validation
    log.info("Running 5-fold cross-validation…")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X_scaled, y, cv=cv, scoring="roc_auc", n_jobs=-1)
    log.info(f"CV ROC-AUC: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    # Final fit on all data
    model.fit(X_scaled, y)

    y_pred = model.predict(X_scaled)
    y_prob = model.predict_proba(X_scaled)[:, 1]

    acc = accuracy_score(y, y_pred)
    auc = roc_auc_score(y, y_prob)
    report_str = classification_report(y, y_pred)

    log.info(f"Train accuracy: {acc:.4f}  |  Train AUC: {auc:.4f}")
    log.info(f"\n{report_str}")

    # Feature importance
    imp = dict(zip(feature_names, model.feature_importances_.tolist()))
    top_features = sorted(imp.items(), key=lambda x: x[1], reverse=True)[:10]

    report: Dict = {
        "cv_roc_auc_mean": round(float(cv_scores.mean()), 4),
        "cv_roc_auc_std": round(float(cv_scores.std()), 4),
        "train_accuracy": round(float(acc), 4),
        "train_roc_auc": round(float(auc), 4),
        "positive_rate": round(float(y.mean()), 4),
        "n_samples": int(len(y)),
        "n_features": len(feature_names),
        "top_10_features": [{"name": k, "importance": round(v, 5)} for k, v in top_features],
        "symbols_used": NSE_SYMBOLS,
        "forward_days": FORWARD_DAYS,
        "success_threshold_pct": SUCCESS_THRESHOLD,
    }

    return model, scaler, feature_names, report


# ── Save artefacts ────────────────────────────────────────────────────────────

def save(model, scaler, feature_names, report):
    model_data = {
        "model": model,
        "scaler": scaler,
        "feature_names": feature_names,
        "metadata": report,
    }

    with open(OUTPUT_PKL, "wb") as f:
        pickle.dump(model_data, f)
    log.info(f"✓ Model saved → {OUTPUT_PKL}")

    with open(OUTPUT_REPORT, "w") as f:
        json.dump(report, f, indent=2)
    log.info(f"✓ Report saved → {OUTPUT_REPORT}")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    log.info("=" * 60)
    log.info("Stockinator — PredictionAgent XGBoost Training")
    log.info("=" * 60)

    raw_df = download_data()
    model, scaler, feature_names, report = train(raw_df)
    save(model, scaler, feature_names, report)

    log.info("\n=== TRAINING COMPLETE ===")
    log.info(f"CV AUC : {report['cv_roc_auc_mean']:.4f} ± {report['cv_roc_auc_std']:.4f}")
    log.info(f"Model  : {OUTPUT_PKL}")
    log.info("Run `uvicorn app.main:app --reload` — the model will auto-load at startup.")
