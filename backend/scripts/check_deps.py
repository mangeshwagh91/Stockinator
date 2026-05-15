import pathlib
import sys

sys.path.insert(0, ".")

src = pathlib.Path("../dashboard.py").read_text(encoding="utf-8")
bt_src = pathlib.Path("app/services/backtest_service.py").read_text(encoding="utf-8")

issues = []

# 1. fetch_live_cycle must call to_dict on CycleResult
if "run_cycle" in src and "to_dict" not in src:
    issues.append("dashboard: run_cycle returns CycleResult dataclass, but to_dict is never called")

# 2. vision_score not surfaced in build_agent_statuses
if "vision_score" not in src:
    issues.append("dashboard: vision_score not read from cycle_data in build_agent_statuses")

# 3. Date column safety in backtest
if 'bars.iloc' in bt_src and '"Date"' in bt_src:
    issues.append("backtest_service: unsafe access to Date column after reset_index (yfinance may use index name)")

# 4. scipy
try:
    import scipy
    print(f"scipy OK: {scipy.__version__}")
except ImportError:
    issues.append("scipy not installed: VisionAgent _local_peaks will fail")

# 5. matplotlib
try:
    import matplotlib
    print(f"matplotlib OK: {matplotlib.__version__}")
except ImportError:
    issues.append("matplotlib not installed: chart rendering disabled")

# 6. plotly
try:
    import plotly
    print(f"plotly OK: {plotly.__version__}")
except ImportError:
    issues.append("plotly not installed: dashboard charts will fail")

# 7. streamlit
try:
    import streamlit
    print(f"streamlit OK: {streamlit.__version__}")
except ImportError:
    issues.append("streamlit not installed: dashboard cannot run")

# 8. Train script - check xgboost import
try:
    import xgboost
    print(f"xgboost OK: {xgboost.__version__}")
except ImportError:
    issues.append("xgboost not installed: train_prediction_model will fail")

# 9. Check backtest Date column access pattern
if "bars.reset_index()" in bt_src:
    if '"Date"' in bt_src or "'Date'" in bt_src:
        issues.append("backtest_service: bars after reset_index() uses hard-coded 'Date' column - yfinance returns index as 'Date' for daily but need safe fallback")

print()
print(f"Logic issues found: {len(issues)}")
for i in issues:
    print(f"  - {i}")
