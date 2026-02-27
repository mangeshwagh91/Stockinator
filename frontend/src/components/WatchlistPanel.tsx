import { watchlist, type SymbolData } from "@/data/mockData";

const ScoreGauge = ({ score, size = 80 }: { score: number; size?: number }) => {
  const circumference = 2 * Math.PI * 35;
  const offset = circumference - (score / 100) * circumference;
  const color = score >= 80 ? "text-bullish" : score >= 50 ? "text-warning" : "text-bearish";

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg className="transform -rotate-90" width={size} height={size} viewBox="0 0 80 80">
        <circle cx="40" cy="40" r="35" fill="none" stroke="hsl(var(--muted))" strokeWidth="5" />
        <circle
          cx="40" cy="40" r="35" fill="none"
          className={`stroke-current ${color}`}
          strokeWidth="5" strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 1s ease" }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className={`font-mono text-lg font-bold ${color}`}>{score}</span>
      </div>
    </div>
  );
};

const signalColor = (signal: SymbolData["signal"]) => {
  switch (signal) {
    case "STRONG_BUY": return "text-bullish bg-bullish/10 border-bullish";
    case "BUY": return "text-bullish bg-bullish/10";
    case "SELL": return "text-bearish bg-bearish/10";
    case "STRONG_SELL": return "text-bearish bg-bearish/10 border-bearish";
    default: return "text-muted-foreground bg-muted";
  }
};

const WatchlistPanel = () => {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <h2 className="font-mono text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-4">
        Watchlist & Scores
      </h2>
      <div className="space-y-3">
        {watchlist.map((item) => (
          <div
            key={item.symbol}
            className="flex items-center justify-between rounded-md border border-border bg-secondary/30 p-3 hover:bg-secondary/50 transition-colors"
          >
            <div className="flex items-center gap-3">
              <ScoreGauge score={item.score} size={56} />
              <div>
                <div className="font-mono text-sm font-semibold text-foreground">{item.symbol}</div>
                <div className="text-xs text-muted-foreground">{item.name}</div>
                <div className="flex items-center gap-2 mt-1">
                  <span className="font-mono text-sm text-foreground">
                    {item.price.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </span>
                  <span className={`font-mono text-xs ${item.change >= 0 ? "text-bullish" : "text-bearish"}`}>
                    {item.change >= 0 ? "+" : ""}{item.change.toFixed(2)} ({item.changePercent.toFixed(2)}%)
                  </span>
                </div>
              </div>
            </div>
            <div className="flex flex-col items-end gap-1">
              <span className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded ${signalColor(item.signal)}`}>
                {item.signal.replace("_", " ")}
              </span>
              <span className="text-[10px] text-muted-foreground font-mono">Vol: {item.volume}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default WatchlistPanel;
