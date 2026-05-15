"""Stockinator Live Dashboard — Streamlit

Run from project root:
    cd backend
    streamlit run ../dashboard.py

Displays:
  • 8-agent live status grid (confidence + latest signal)
  • Real-time trade recommendations from TradeAgent
  • Backtest results & equity curve
  • News sentiment feed
"""

import sys, os, time, json, threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# ── Path setup ────────────────────────────────────────────────────────────────
DASHBOARD_DIR = Path(__file__).resolve().parent
BACKEND_DIR = DASHBOARD_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Stockinator — Live Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main { background: #0d1117; }
    .stApp { background: #0d1117; }

    /* Agent card */
    .agent-card {
        background: linear-gradient(135deg,#161b22,#1c2128);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        transition: border-color .2s;
    }
    .agent-card:hover { border-color: #58a6ff; }
    .agent-name { font-size:13px; font-weight:700; color:#c9d1d9; letter-spacing:.08em; }
    .agent-signal-buy  { color:#3fb950; font-weight:700; font-size:16px; }
    .agent-signal-sell { color:#f85149; font-weight:700; font-size:16px; }
    .agent-signal-hold { color:#8b949e; font-weight:700; font-size:16px; }
    .conf-bar { height:4px; border-radius:2px; margin-top:6px; }
    .status-dot {
        width:8px; height:8px; border-radius:50%; display:inline-block; margin-right:6px;
    }
    .dot-green { background:#3fb950; box-shadow:0 0 6px #3fb950; }
    .dot-red   { background:#f85149; box-shadow:0 0 6px #f85149; }
    .dot-gray  { background:#8b949e; }

    /* Trade recommendation */
    .trade-buy  { background:linear-gradient(135deg,#0d2218,#0a2e1a); border:1px solid #3fb950; border-radius:10px; padding:14px; }
    .trade-sell { background:linear-gradient(135deg,#2d1116,#3d0d0d); border:1px solid #f85149; border-radius:10px; padding:14px; }
    .trade-hold { background:linear-gradient(135deg,#161b22,#1c2128); border:1px solid #8b949e; border-radius:10px; padding:14px; }

    /* Metric overrides */
    [data-testid="metric-container"] { background:#161b22; border:1px solid #30363d; border-radius:10px; padding:10px; }
    [data-testid="stMetricValue"] { color:#c9d1d9; font-size:22px !important; }
    [data-testid="stMetricLabel"] { color:#8b949e; font-size:11px !important; }

    /* Section header */
    .section-header {
        font-size:13px; font-weight:700; color:#8b949e; letter-spacing:.1em;
        text-transform:uppercase; border-bottom:1px solid #21262d; padding-bottom:8px; margin-bottom:16px;
    }

    /* News item */
    .news-item { border-left:3px solid #58a6ff; padding:6px 10px; margin:6px 0; background:#161b22; border-radius:0 6px 6px 0; }
    .news-positive { border-left-color:#3fb950; }
    .news-negative { border-left-color:#f85149; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Backend helpers (graceful degradation if backend not running)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_resource
def get_orchestrator():
    try:
        from app.orchestrator.runtime import Orchestrator
        return Orchestrator(threshold=65.0, paper=True)
    except Exception:
        return None

@st.cache_resource
def get_backtest_service():
    try:
        from app.services.backtest_service import BacktestService
        return BacktestService(threshold=60.0, hold_days=5)
    except Exception:
        return None

@st.cache_resource
def get_vision_agent():
    try:
        from app.agents.vision_agent import VisionAgent
        return VisionAgent()
    except Exception:
        return None


# ── Mock data for when backend is unavailable ─────────────────────────────────

def _mock_agent_status() -> List[Dict]:
    agents = [
        {"name": "Scraping",    "signal": "BUY",  "confidence": 0.82, "score": 72, "status": "ready", "detail": "NSE data + NewsAPI live"},
        {"name": "Indicator",   "signal": "BUY",  "confidence": 0.78, "score": 68, "status": "ready", "detail": "RSI=38 | MACD↑ | ADX=28"},
        {"name": "Pattern",     "signal": "HOLD", "confidence": 0.55, "score": 55, "status": "ready", "detail": "Doji detected"},
        {"name": "Prediction",  "signal": "BUY",  "confidence": 0.71, "score": 64, "status": "fallback", "detail": "XGBoost fallback (no .pkl)"},
        {"name": "Algorithm",   "signal": "BUY",  "confidence": 0.80, "score": 70, "status": "ready", "detail": "Bullish consensus 8/11"},
        {"name": "Aggregation", "signal": "BUY",  "confidence": 0.73, "score": 66, "status": "partial", "detail": "Via memory_agent + market_data"},
        {"name": "Vision",      "signal": "HOLD", "confidence": 0.50, "score": 50, "status": "partial", "detail": "Rule-based (no CNN weights)"},
        {"name": "Trade",       "signal": "BUY",  "confidence": 0.77, "score": 67, "status": "ready", "detail": "Paper mode active"},
    ]
    return agents

def _mock_trade_recommendation() -> Dict:
    return {
        "symbol": "RELIANCE",
        "action": "BUY",
        "entry": 2891.45,
        "stop_loss": 2834.62,
        "take_profit": 3005.10,
        "quantity": 1,
        "success_score": 74.3,
        "reasons": ["Bullish consensus 8/11 indicators", "RSI oversold bounce", "MACD bullish crossover"],
        "risk_reward": "1:2.0",
        "timestamp": datetime.now().isoformat(),
    }

def _mock_backtest_result() -> Dict:
    n = 200
    equity = [100.0]
    for _ in range(n):
        equity.append(equity[-1] * (1 + np.random.normal(0.003, 0.015)))
    return {
        "symbol": "NSE Portfolio (30 stocks)",
        "sharpe": 1.42,
        "win_rate": 61.3,
        "max_drawdown": -12.4,
        "total_return": 18.7,
        "n_trades": 312,
        "equity_curve": equity,
        "trades": [],
    }

def _mock_news() -> List[Dict]:
    return [
        {"headline": "Reliance Q4 profit beats estimates by 8%", "sentiment": 0.78, "symbol": "RELIANCE"},
        {"headline": "RBI holds rates steady — markets cheer", "sentiment": 0.65, "symbol": "INDIA_MARKET"},
        {"headline": "TCS sees strong deal wins in BFSI segment", "sentiment": 0.70, "symbol": "TCS"},
        {"headline": "Rupee weakens against dollar on FII outflows", "sentiment": -0.45, "symbol": "INDIA_MARKET"},
        {"headline": "HDFC Bank gross NPA falls to 3-year low", "sentiment": 0.60, "symbol": "HDFCBANK"},
        {"headline": "Auto sector faces headwinds from rising input costs", "sentiment": -0.35, "symbol": "MARUTI"},
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Live data fetch (with fallback)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def fetch_live_cycle(symbol: str) -> Dict:
    orch = get_orchestrator()
    if orch is None:
        return {}
    try:
        result = orch.run_cycle(symbol)
        return orch.to_dict(result)
    except Exception:
        return {}

@st.cache_data(ttl=300)
def fetch_backtest(symbol: str, period: str = "1y") -> Dict:
    bt = get_backtest_service()
    if bt is None:
        return _mock_backtest_result()
    try:
        result = bt.run(symbol + ".NS" if not symbol.endswith(".NS") else symbol, period)
        return result.to_dict()
    except Exception:
        return _mock_backtest_result()

@st.cache_data(ttl=120)
def fetch_news() -> List[Dict]:
    try:
        from app.services.news_service import news_service
        articles = news_service.fetch_market_impact_news_from_sources()
        out = []
        for a in articles[:10]:
            sentiment_raw = a.get("sentiment_score", 0.0)
            out.append({
                "headline": a.get("title", ""),
                "sentiment": float(sentiment_raw),
                "symbol": a.get("symbol", "MARKET"),
            })
        return out if out else _mock_news()
    except Exception:
        return _mock_news()


# ─────────────────────────────────────────────────────────────────────────────
# Agent status builder
# ─────────────────────────────────────────────────────────────────────────────

def build_agent_statuses(cycle: Dict) -> List[Dict]:
    if not cycle:
        return _mock_agent_status()

    def sig(score: float) -> str:
        if score >= 65: return "BUY"
        if score <= 40: return "SELL"
        return "HOLD"

    scraping_score = min(100, 50 + (cycle.get("news_sentiment", 50) - 50) * 0.5 + 15)
    algo_score     = float(cycle.get("algo_score", 50))
    pred_score     = float(cycle.get("success_score", 50))
    vision_score   = float(cycle.get("vision_score", 50))
    vision_pattern = cycle.get("vision_pattern", "no_pattern")
    vision_dir     = cycle.get("vision_direction", "HOLD")
    vision_model   = cycle.get("vision_model", "rule_based")
    trade_score    = pred_score

    return [
        {"name": "Scraping",    "signal": sig(scraping_score), "confidence": scraping_score/100, "score": scraping_score, "status": "ready", "detail": f"Price={cycle.get('price',0):.0f} | News={cycle.get('news_count',0)} articles"},
        {"name": "Indicator",   "signal": sig(algo_score),     "confidence": algo_score/100,     "score": algo_score,     "status": "ready", "detail": f"Bullish={cycle.get('bullish_count',0)} Bearish={cycle.get('bearish_count',0)}"},
        {"name": "Pattern",     "signal": sig(algo_score),     "confidence": algo_score/100,     "score": algo_score,     "status": "ready", "detail": " | ".join(cycle.get("patterns", ["None detected"]))[:60]},
        {"name": "Prediction",  "signal": cycle.get("direction","HOLD"), "confidence": pred_score/100, "score": pred_score, "status": "ready", "detail": f"ML={cycle.get('ml_score',0):.1f} Combined={pred_score:.1f}"},
        {"name": "Algorithm",   "signal": sig(algo_score),     "confidence": algo_score/100,     "score": algo_score,     "status": "ready", "detail": f"Consensus={algo_score:.1f}/100"},
        {"name": "Aggregation", "signal": sig(pred_score),     "confidence": pred_score/100,     "score": pred_score,     "status": "partial","detail": "Memory + market_data pipeline"},
        {"name": "Vision",      "signal": vision_dir,          "confidence": vision_score/100,   "score": vision_score,   "status": "partial","detail": f"{vision_pattern.replace('_',' ').title()} [{vision_model}]"},
        {"name": "Trade",       "signal": cycle.get("action","HOLD"), "confidence": trade_score/100, "score": trade_score, "status": "ready", "detail": f"SL={cycle.get('trade_sl',0):.0f} TP={cycle.get('trade_tp',0):.0f}"},
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Render helpers
# ─────────────────────────────────────────────────────────────────────────────

def signal_color(signal: str) -> str:
    return {"BUY": "#3fb950", "SELL": "#f85149"}.get(signal, "#8b949e")

def signal_class(signal: str) -> str:
    return {"BUY": "agent-signal-buy", "SELL": "agent-signal-sell"}.get(signal, "agent-signal-hold")

def status_dot(status: str) -> str:
    dot = {"ready": "dot-green", "partial": "dot-gray", "fallback": "dot-gray"}.get(status, "dot-red")
    return f'<span class="status-dot {dot}"></span>'

def render_agent_card(a: Dict):
    bar_color = signal_color(a["signal"])
    bar_w = int(a["confidence"] * 100)
    status_html = status_dot(a["status"])
    sig_cls = signal_class(a["signal"])
    st.markdown(f"""
    <div class="agent-card">
      <div class="agent-name">{status_html}{a['name'].upper()} AGENT</div>
      <div class="{sig_cls}" style="margin:6px 0 2px">{a['signal']} &nbsp;<span style="font-size:12px;color:#8b949e;">score {a['score']:.0f}</span></div>
      <div style="background:#21262d;border-radius:2px;height:4px;">
        <div style="width:{bar_w}%;height:4px;border-radius:2px;background:{bar_color};transition:width .5s;"></div>
      </div>
      <div style="font-size:11px;color:#8b949e;margin-top:6px;">{a['detail']}</div>
    </div>
    """, unsafe_allow_html=True)

def render_trade_card(trade: Dict):
    action = trade.get("action", "HOLD")
    card_class = {"BUY": "trade-buy", "SELL": "trade-sell"}.get(action, "trade-hold")
    color = signal_color(action)
    st.markdown(f"""
    <div class="{card_class}" style="margin-bottom:12px;">
      <div style="font-size:11px;color:#8b949e;margin-bottom:4px;">LATEST RECOMMENDATION</div>
      <div style="font-size:26px;font-weight:700;color:{color};">{action} {trade.get('symbol','—')}</div>
      <div style="font-size:13px;color:#c9d1d9;margin:8px 0 4px;">
        Entry <b>₹{trade.get('entry',0):.2f}</b> &nbsp;|&nbsp;
        SL <span style="color:#f85149;">₹{trade.get('stop_loss',0):.2f}</span> &nbsp;|&nbsp;
        TP <span style="color:#3fb950;">₹{trade.get('take_profit',0):.2f}</span>
      </div>
      <div style="font-size:12px;color:#8b949e;">
        Score <b>{trade.get('success_score',0):.1f}</b> &nbsp;|&nbsp;
        R:R <b>{trade.get('risk_reward','—')}</b> &nbsp;|&nbsp;
        Qty <b>{trade.get('quantity',1)}</b>
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_equity_chart(equity: List[float], title: str = "Equity Curve"):
    fig = go.Figure()
    x = list(range(len(equity)))
    fig.add_trace(go.Scatter(
        x=x, y=equity, mode="lines",
        line=dict(color="#58a6ff", width=2),
        fill="tozeroy", fillcolor="rgba(88,166,255,0.07)",
        name="Equity",
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color="#c9d1d9")),
        paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
        font=dict(color="#8b949e", size=11),
        margin=dict(l=40, r=20, t=40, b=30),
        xaxis=dict(showgrid=False, color="#8b949e"),
        yaxis=dict(showgrid=True, gridcolor="#21262d", color="#8b949e"),
        height=280,
    )
    st.plotly_chart(fig, use_container_width=True)


def render_news_feed(news: List[Dict]):
    st.markdown('<div class="section-header">📰 News Sentiment Feed</div>', unsafe_allow_html=True)
    for n in news:
        s = n.get("sentiment", 0)
        css = "news-positive" if s > 0.2 else ("news-negative" if s < -0.2 else "")
        bar_color = "#3fb950" if s > 0 else "#f85149"
        bar_w = int(abs(s) * 100)
        label = "▲" if s > 0.2 else ("▼" if s < -0.2 else "◆")
        st.markdown(f"""
        <div class="news-item {css}">
          <span style="font-size:12px;color:#c9d1d9;">{label} {n.get('headline','')}</span>
          <div style="background:#21262d;border-radius:2px;height:3px;margin-top:4px;width:100%;">
            <div style="width:{bar_w}%;height:3px;border-radius:2px;background:{bar_color};"></div>
          </div>
          <span style="font-size:10px;color:#8b949e;">{n.get('symbol','')}  sentiment={s:+.2f}</span>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚡ Stockinator")
    st.markdown("Multi-Agent Trading Platform")
    st.divider()

    symbol = st.text_input("Symbol", value="RELIANCE", help="NSE symbol (e.g. RELIANCE, TCS, NIFTY50)").upper()
    period = st.selectbox("Backtest Period", ["1y", "2y", "6mo"], index=0)
    threshold = st.slider("Signal Threshold", 50, 90, 65, 5,
                          help="Minimum success score to trigger a BUY signal")
    auto_refresh = st.checkbox("Auto-refresh (60s)", value=False)

    st.divider()
    if st.button("🔄 Run Full Cycle", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    if st.button("🎯 Run Backtest", use_container_width=True):
        st.cache_data.clear()

    st.divider()
    st.markdown("**Agent Registry**")
    st.markdown("✅ Scraping &nbsp; ✅ Indicator  \n✅ Pattern &nbsp; ✅ Algorithm  \n✅ Prediction &nbsp; ⚠️ Aggregation  \n⚠️ Vision &nbsp; ✅ Trade")
    st.divider()
    st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")


# ─────────────────────────────────────────────────────────────────────────────
# Main layout
# ─────────────────────────────────────────────────────────────────────────────

st.markdown(f"## 📈 Stockinator Live Dashboard &nbsp; <span style='font-size:14px;color:#8b949e;'>— {symbol}</span>", unsafe_allow_html=True)

# Fetch data
with st.spinner("Fetching live data…"):
    cycle_data   = fetch_live_cycle(symbol)
    backtest_res = fetch_backtest(symbol, period)
    news_items   = fetch_news()

agent_statuses = build_agent_statuses(cycle_data)

# ── Top KPI bar ───────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5, k6 = st.columns(6)
sharpe   = backtest_res.get("sharpe", 0)
win_rate = backtest_res.get("win_rate", 0)
max_dd   = backtest_res.get("max_drawdown", 0)
tot_ret  = backtest_res.get("total_return", 0)
n_trades = backtest_res.get("n_trades", 0)
pred_sc  = cycle_data.get("success_score", agent_statuses[3]["score"])

k1.metric("Success Score", f"{pred_sc:.1f}", delta=None)
k2.metric("Sharpe Ratio",  f"{sharpe:.2f}",  delta=f"{'Good' if sharpe>1 else 'Low'}")
k3.metric("Win Rate",      f"{win_rate:.1f}%")
k4.metric("Max Drawdown",  f"{max_dd:.1f}%")
k5.metric("Total Return",  f"{tot_ret:.1f}%")
k6.metric("Trades",        f"{n_trades}")

st.divider()

# ── Main content columns ──────────────────────────────────────────────────────
left, mid, right = st.columns([1.1, 1.4, 1.1])

# ── LEFT: Agent Status Grid ───────────────────────────────────────────────────
with left:
    st.markdown('<div class="section-header">🤖 Agent Status</div>', unsafe_allow_html=True)
    for agent in agent_statuses:
        render_agent_card(agent)

# ── MID: Trade Recommendation + Equity Curve ─────────────────────────────────
with mid:
    st.markdown('<div class="section-header">💹 Trade Recommendation</div>', unsafe_allow_html=True)

    # Build trade dict from cycle or mock
    if cycle_data and cycle_data.get("action") not in [None, ""]:
        trade_rec = {
            "symbol": symbol,
            "action": cycle_data.get("action", "HOLD"),
            "entry":  cycle_data.get("price", 0),
            "stop_loss":  cycle_data.get("trade_sl", cycle_data.get("price", 0) * 0.98),
            "take_profit":cycle_data.get("trade_tp", cycle_data.get("price", 0) * 1.04),
            "quantity": 1,
            "success_score": cycle_data.get("success_score", 50),
            "risk_reward": "1:2.0",
            "reasons": cycle_data.get("reasons", []),
        }
    else:
        trade_rec = _mock_trade_recommendation()

    render_trade_card(trade_rec)

    # Reasons
    reasons = trade_rec.get("reasons", [])
    if reasons:
        with st.expander("📋 Decision Reasoning", expanded=False):
            for r in reasons:
                st.markdown(f"• {r}")

    # Equity Curve
    st.markdown('<div class="section-header" style="margin-top:16px;">📊 Equity Curve</div>', unsafe_allow_html=True)
    equity = backtest_res.get("equity_curve", [100])
    render_equity_chart(equity, f"Backtest: {symbol} ({period})")

    # Backtest metrics table
    bt_cols = st.columns(4)
    bt_cols[0].metric("Sharpe",   f"{sharpe:.2f}")
    bt_cols[1].metric("Win Rate", f"{win_rate:.1f}%")
    bt_cols[2].metric("Max DD",   f"{max_dd:.1f}%")
    bt_cols[3].metric("Return",   f"{tot_ret:.1f}%")

# ── RIGHT: News Feed + Agent Confidence Chart ─────────────────────────────────
with right:
    render_news_feed(news_items)

    st.divider()
    st.markdown('<div class="section-header">📡 Agent Confidence</div>', unsafe_allow_html=True)

    names   = [a["name"] for a in agent_statuses]
    scores  = [a["score"] for a in agent_statuses]
    colors  = [signal_color(a["signal"]) for a in agent_statuses]

    fig_bar = go.Figure(go.Bar(
        x=scores, y=names, orientation="h",
        marker=dict(color=colors, opacity=0.85),
        text=[f"{s:.0f}" for s in scores],
        textposition="auto",
    ))
    fig_bar.add_vline(x=threshold, line=dict(color="#f0a500", width=1.5, dash="dash"),
                      annotation_text="threshold", annotation_font_color="#f0a500")
    fig_bar.update_layout(
        paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
        font=dict(color="#8b949e", size=10),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(range=[0, 100], showgrid=True, gridcolor="#21262d"),
        yaxis=dict(showgrid=False),
        showlegend=False,
        height=280,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ── Cycle steps trace ─────────────────────────────────────────────────────────
if cycle_data.get("cycle_steps"):
    with st.expander("🔍 Cycle Execution Trace", expanded=False):
        steps = cycle_data["cycle_steps"]
        for i, step in enumerate(steps):
            st.markdown(f"`{i+1:02d}` ✅ **{step}**")
        if cycle_data.get("errors"):
            for err in cycle_data["errors"]:
                st.error(f"⚠ {err}")

# ── Indicator snapshot table ──────────────────────────────────────────────────
if cycle_data.get("indicators"):
    with st.expander("📐 Indicator Snapshot", expanded=False):
        ind = cycle_data["indicators"]
        rows = [(k.upper(), f"{v:.4f}" if isinstance(v, float) else str(v)) for k, v in ind.items()]
        df_ind = pd.DataFrame(rows, columns=["Indicator", "Value"])
        st.dataframe(df_ind, use_container_width=True, hide_index=True)

# ── Auto-refresh ──────────────────────────────────────────────────────────────
if auto_refresh:
    time.sleep(60)
    st.rerun()
