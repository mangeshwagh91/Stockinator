import { riskMetrics } from "@/data/mockData";

const Header = () => {
  return (
    <header className="border-b border-border bg-card/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="flex items-center justify-between px-6 py-3">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-bullish animate-pulse" />
            <h1 className="font-mono text-sm font-bold text-foreground tracking-tight">
              NEXUS<span className="text-primary">TRADE</span>
            </h1>
          </div>
          <span className="text-[10px] font-mono text-muted-foreground border border-border rounded px-2 py-0.5">
            AI AUTO-TRADING v1.0
          </span>
        </div>

        <div className="flex items-center gap-6">
          <div className="flex items-center gap-4 text-xs font-mono">
            <div className="text-muted-foreground">
              Capital: <span className="text-foreground font-semibold">₹{(riskMetrics.totalCapital / 100000).toFixed(1)}L</span>
            </div>
            <div className="text-muted-foreground">
              Day P&L:{" "}
              <span className={`font-semibold ${riskMetrics.dailyPnL >= 0 ? "text-bullish" : "text-bearish"}`}>
                {riskMetrics.dailyPnL >= 0 ? "+" : ""}₹{riskMetrics.dailyPnL.toLocaleString()}
              </span>
            </div>
            <div className="text-muted-foreground">
              Positions: <span className="text-foreground font-semibold">{riskMetrics.currentPositions}/{riskMetrics.maxPositions}</span>
            </div>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-bullish" />
            <span className="text-[10px] font-mono text-bullish">CONNECTED</span>
          </div>
        </div>
      </div>

      {/* Ticker */}
      <div className="overflow-hidden border-t border-border/50 bg-background/50">
        <div className="flex items-center animate-ticker whitespace-nowrap py-1">
          {[...Array(2)].map((_, dupeIdx) => (
            <div key={dupeIdx} className="flex items-center gap-6 px-4">
              <TickerItem symbol="NIFTY 50" value="22,458.50" change="+0.85%" positive />
              <TickerItem symbol="SENSEX" value="73,892.20" change="+0.72%" positive />
              <TickerItem symbol="BTC/USD" value="67,432.18" change="+1.88%" positive />
              <TickerItem symbol="ETH/USD" value="3,521.44" change="-1.19%" positive={false} />
              <TickerItem symbol="GOLD" value="$2,342.50" change="+0.32%" positive />
              <TickerItem symbol="USD/INR" value="83.42" change="-0.15%" positive={false} />
              <TickerItem symbol="CRUDE" value="$78.90" change="+1.24%" positive />
            </div>
          ))}
        </div>
      </div>
    </header>
  );
};

const TickerItem = ({ symbol, value, change, positive }: { symbol: string; value: string; change: string; positive: boolean }) => (
  <div className="flex items-center gap-2">
    <span className="text-[10px] font-mono text-muted-foreground">{symbol}</span>
    <span className="text-[10px] font-mono text-foreground font-semibold">{value}</span>
    <span className={`text-[10px] font-mono font-semibold ${positive ? "text-bullish" : "text-bearish"}`}>{change}</span>
  </div>
);

export default Header;
