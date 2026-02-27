import { indicators, type Indicator } from "@/data/mockData";

const categoryColors: Record<string, string> = {
  trend: "text-primary",
  momentum: "text-info",
  volatility: "text-warning",
  volume: "text-accent",
};

const IndicatorPanel = () => {
  const grouped = indicators.reduce<Record<string, Indicator[]>>((acc, ind) => {
    (acc[ind.category] ??= []).push(ind);
    return acc;
  }, {});

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <h2 className="font-mono text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-4">
        Technical Indicators
      </h2>
      <div className="space-y-4">
        {Object.entries(grouped).map(([category, inds]) => (
          <div key={category}>
            <div className={`font-mono text-[10px] uppercase tracking-widest mb-2 ${categoryColors[category]}`}>
              {category}
            </div>
            <div className="grid grid-cols-2 gap-2">
              {inds.map((ind) => (
                <div
                  key={ind.name}
                  className="flex items-center justify-between rounded border border-border bg-secondary/20 px-3 py-2"
                >
                  <span className="text-xs text-muted-foreground">{ind.name}</span>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-semibold text-foreground">{ind.value}</span>
                    <span
                      className={`w-2 h-2 rounded-full ${
                        ind.signal === "bullish" ? "bg-bullish" : ind.signal === "bearish" ? "bg-bearish" : "bg-warning"
                      }`}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default IndicatorPanel;
