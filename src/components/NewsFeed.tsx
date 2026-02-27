import { newsItems } from "@/data/mockData";

const impactBadge = (impact: string) => {
  switch (impact) {
    case "high": return "bg-bearish/20 text-bearish";
    case "medium": return "bg-warning/20 text-warning";
    default: return "bg-muted text-muted-foreground";
  }
};

const sentimentBar = (sentiment: number) => {
  const width = Math.abs(sentiment) * 10;
  const isPositive = sentiment >= 0;
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 h-1.5 rounded-full bg-muted overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${isPositive ? "bg-bullish ml-auto" : "bg-bearish"}`}
          style={{
            width: `${width}%`,
            marginLeft: isPositive ? `${100 - width}%` : "0",
          }}
        />
      </div>
      <span className={`font-mono text-[10px] font-semibold ${isPositive ? "text-bullish" : "text-bearish"}`}>
        {sentiment > 0 ? "+" : ""}{sentiment}
      </span>
    </div>
  );
};

const NewsFeed = () => {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <h2 className="font-mono text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-4">
        News Sentiment Feed
      </h2>
      <div className="space-y-3 max-h-[400px] overflow-y-auto pr-1">
        {newsItems.map((item) => (
          <div
            key={item.id}
            className="rounded border border-border bg-secondary/20 p-3 hover:bg-secondary/40 transition-colors"
          >
            <div className="flex items-start justify-between gap-2 mb-2">
              <p className="text-xs text-foreground leading-relaxed flex-1">{item.headline}</p>
              <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded shrink-0 ${impactBadge(item.impact)}`}>
                {item.impact.toUpperCase()}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-muted-foreground">{item.source}</span>
                <span className="text-[10px] text-muted-foreground">•</span>
                <span className="text-[10px] text-muted-foreground">{item.time}</span>
                <span className="text-[10px] font-mono text-primary">{item.eventType}</span>
              </div>
              {sentimentBar(item.sentiment)}
            </div>
            <div className="flex gap-1 mt-2">
              {item.relevantSymbols.map((s) => (
                <span key={s} className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-primary/10 text-primary">
                  {s}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default NewsFeed;
