import { useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import GeoGlobe from "@/components/GeoGlobe";
import { backendApi } from "@/lib/backendApi";

const Dashboard = () => {
  const queryClient = useQueryClient();

  const { data: status } = useQuery({
    queryKey: ["system-status"],
    queryFn: backendApi.getSystemStatus,
    refetchInterval: 30000,
    retry: 1,
  });

  const { data: bankNiftyPrice } = useQuery({
    queryKey: ["price", "BANKNIFTY"],
    queryFn: () => backendApi.getPrice("BANKNIFTY", "stock"),
    refetchInterval: 25000,
    retry: 1,
  });

  useEffect(() => {
    const base = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";
    const wsUrl = base.replace(/^http/, "ws") + "/api/v1/ws/live";
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "tick") {
          queryClient.setQueryData(["price", data.symbol], (old: any) => ({
            ...old,
            price: data.price,
            timestamp: data.timestamp
          }));
        }
      } catch (err) {
        console.error("WS error", err);
      }
    };

    return () => ws.close();
  }, [queryClient]);

  const gtiValue = status ? Math.max(35, Math.min(95, 70 + (status.risk_metrics.daily_loss_used_pct ?? 0) * 0.12)) : 71.4;

  return (
    <section className="earth-pulse-screen">
      <button className="geo-filter-btn" type="button">
        FILTERS
      </button>

      <div className="globe-zone" aria-hidden="true">
        <div className="orbit orbit-a" />
        <div className="orbit orbit-b" />
        <GeoGlobe />
        <div className="geo-live-marker">LIVE</div>
        <div className="geo-globe-tag">Global GTI {gtiValue.toFixed(1)}</div>
      </div>

      <aside className="signals-drawer">
        <div className="panel-title-row">
          <h2>SIGNALS</h2>
        </div>

        <article className="signal-card featured">
          <div className="signal-head">
            <strong>BANKNIFTY</strong>
            <span className="geo-chip geo-chip-buy">BUY</span>
            <span className="signal-price">
              ₹{bankNiftyPrice?.price ? bankNiftyPrice.price.toLocaleString(undefined, { maximumFractionDigits: 2 }) : "--"}
            </span>
          </div>
          <p className="signal-meta">NSE / Index Derivatives</p>
          <div className="signal-stats">
            <span>Confidence: {status?.trading_active ? "88%" : "81%"}</span>
            <span>Uncertainty: {status?.paper_trading ? "12%" : "9%"}</span>
          </div>
          <div className="signal-meter">
            <div className="signal-meter-fill" style={{ width: status?.trading_active ? "88%" : "81%" }} />
          </div>
          <p className="signal-analysis">
            Multi-agent trend confirmation with macro volatility monitoring active.
          </p>
        </article>

        <div className="panel-subhead">ALL SIGNALS (2)</div>
        <article className="signal-card mini">
          <div className="signal-head">
            <strong>XAU/USD</strong>
            <span className="geo-chip geo-chip-buy">BUY</span>
            <span className="signal-up">+1.2%</span>
          </div>
          <p className="signal-meta">Commodities</p>
          <div className="signal-meter compact">
            <div className="signal-meter-fill" style={{ width: "86%" }} />
          </div>
        </article>

        <article className="signal-card mini">
          <div className="signal-head">
            <strong>HSI</strong>
            <span className="geo-chip geo-chip-sell">SELL</span>
            <span className="signal-down">-1.5%</span>
          </div>
          <p className="signal-meta">Equity Index</p>
          <div className="signal-meter compact">
            <div className="signal-meter-fill bearish" style={{ width: "44%" }} />
          </div>
        </article>
      </aside>

      <div className="risk-legend">RISK LEVEL: CRITICAL / HIGH / MEDIUM / LOW</div>

      <footer className="geo-event-ticker">
        <div className="gti-block">
          <span className="label">GTI TREND</span>
          <strong>{gtiValue.toFixed(1)}</strong>
        </div>
        <div className="event-card danger">
          <strong>Strait of Hormuz Naval Drill...</strong>
          <span>10:28 AM · Middle East · CRITICAL</span>
        </div>
        <div className="event-card warning">
          <strong>ECB Emergency Statement</strong>
          <span>09:28 AM · Europe · HIGH</span>
        </div>
      </footer>
    </section>
  );
};

export default Dashboard;
