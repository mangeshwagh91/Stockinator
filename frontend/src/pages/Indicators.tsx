import { useQuery } from "@tanstack/react-query";
import { watchlist } from "@/data/mockData";
import { backendApi } from "@/lib/backendApi";

const Indicators = () => {
  const cards = watchlist.slice(0, 4);
  const { data: status } = useQuery({
    queryKey: ["system-status"],
    queryFn: backendApi.getSystemStatus,
    refetchInterval: 30000,
    retry: 1,
  });

  const { data: bankNiftyPrice } = useQuery({
    queryKey: ["price", "BANKNIFTY"],
    queryFn: () => backendApi.getPrice("BANKNIFTY", "stock"),
    refetchInterval: 20000,
    retry: 1,
  });

  return (
    <section className="signals-screen">
      <aside className="signals-left-rail">
        <div className="rail-group">
          <div className="rail-title">ASSET CLASS</div>
          <button type="button" className="rail-pill active">All</button>
          <div className="rail-links">
            <span>Commodities</span>
            <span>Equity Indices</span>
            <span>Forex</span>
            <span>Crypto</span>
            <span>Stocks</span>
            <span>ETFs</span>
            <span>Bonds</span>
          </div>
        </div>

        <div className="rail-group">
          <div className="rail-title">DIRECTION</div>
          <button type="button" className="rail-pill active">All</button>
          <div className="rail-links">
            <span className="up">BUY</span>
            <span className="down">SELL</span>
            <span className="neutral">HOLD</span>
          </div>
        </div>
      </aside>

      <div className="signals-list-col">
        <input className="signal-search" placeholder="Search asset..." />
        <div className="asset-list-scroll">
          {cards.map((item, idx) => {
            const bullish = item.signal.includes("BUY");
            return (
              <article key={item.symbol} className={`asset-card ${bullish ? "bull" : "bear"}`}>
                <div className="asset-header">
                  <strong>{item.symbol.replace("/", "")}</strong>
                  <span className={`geo-chip ${bullish ? "geo-chip-buy" : "geo-chip-sell"}`}>
                    {bullish ? "BUY" : "SELL"}
                  </span>
                  <span>{90 - idx}% confidence</span>
                </div>
                <p>{item.name}</p>
                <div className="dual-bars">
                  <div><span>Bull</span><i style={{ width: `${68 - idx * 4}%` }} /></div>
                  <div><span>Bear</span><i style={{ width: `${idx * 20}%` }} /></div>
                </div>
                <small>Iran-Israel Escalation - Missile Exchanges Risk</small>
              </article>
            );
          })}
        </div>
      </div>

      <article className="signal-detail">
        <div className="detail-top">
          <div>
            <h1>BANKNIFTY <span className="geo-chip geo-chip-buy">BUY</span></h1>
            <p>NSE · Index Derivatives</p>
            <small>OI-based breakout with momentum confirmation</small>
          </div>
          <div className="detail-confidence">
            <strong>{status?.trading_active ? "89%" : "84%"}</strong>
            <span>confidence</span>
            <em>{status?.paper_trading ? "11%" : "9%"}</em>
            <span>uncertainty</span>
          </div>
        </div>

        <div className="strength-bar-wrap">
          <span>Bullish Strength</span>
          <div className="strength-track"><i style={{ width: "74%" }} /></div>
          <span>Bearish Strength</span>
          <div className="strength-track bearish"><i style={{ width: "8%" }} /></div>
        </div>

        <div className="tag-row">
          <span className="tag warning">MEDIUM VOLATILITY</span>
          <span className="tag">short-term</span>
          <span className="tag">metals</span>
          <span className="tag">global</span>
        </div>

        <div className="trigger-box">
          <div className="trigger-title">TRIGGERING EVENT</div>
          <strong>Iran-Israel Escalation - Missile Exchanges</strong>
          <p>military escalation · Severity 92.0% · 09:28</p>
        </div>

        <div className="trade-tabs">
          <span className="active">TRADE SETUP</span>
          <span>AI REASONING</span>
          <span>TIMELINE</span>
          <span>RELIABILITY</span>
        </div>

        <div className="metrics-grid">
          <Metric label="CURRENT PRICE" value={bankNiftyPrice?.price ? bankNiftyPrice.price.toFixed(2) : "--"} />
          <Metric label="ENTRY" value={bankNiftyPrice?.price ? (bankNiftyPrice.price * 0.996).toFixed(2) : "--"} />
          <Metric label="STOP LOSS" value={bankNiftyPrice?.price ? (bankNiftyPrice.price * 0.972).toFixed(2) : "--"} danger />
          <Metric label="TARGET" value={bankNiftyPrice?.price ? (bankNiftyPrice.price * 1.038).toFixed(2) : "--"} good />
          <Metric label="RISK/REWARD" value="2.35x" />
          <Metric label="OPEN POSITIONS" value={`${status?.risk_metrics.open_positions ?? 0}/${status?.risk_metrics.max_open_positions ?? 5}`} warn />
        </div>
      </article>
    </section>
  );
};

const Metric = ({
  label,
  value,
  danger,
  good,
  warn,
}: {
  label: string;
  value: string;
  danger?: boolean;
  good?: boolean;
  warn?: boolean;
}) => (
  <div className="metric-card">
    <span>{label}</span>
    <strong className={danger ? "down" : good ? "up" : warn ? "warn" : ""}>{value}</strong>
  </div>
);

export default Indicators;
