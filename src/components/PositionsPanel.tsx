import { openPositions, recentTrades, riskMetrics } from "@/data/mockData";

const PositionsPanel = () => {
  const totalPnL = openPositions.reduce((sum, p) => sum + p.pnl, 0);

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-mono text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Open Positions
        </h2>
        <span className={`font-mono text-sm font-bold ${totalPnL >= 0 ? "text-bullish" : "text-bearish"}`}>
          P&L: ₹{totalPnL.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
        </span>
      </div>

      <div className="space-y-2 mb-6">
        {openPositions.map((pos) => (
          <div key={pos.symbol} className="rounded border border-border bg-secondary/20 p-3">
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-2">
                <span className="font-mono text-sm font-semibold text-foreground">{pos.symbol}</span>
                <span className={`text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded ${
                  pos.side === "LONG" ? "bg-bullish/10 text-bullish" : "bg-bearish/10 text-bearish"
                }`}>
                  {pos.side}
                </span>
              </div>
              <span className={`font-mono text-sm font-bold ${pos.pnl >= 0 ? "text-bullish" : "text-bearish"}`}>
                {pos.pnl >= 0 ? "+" : ""}₹{pos.pnl.toFixed(2)} ({pos.pnlPercent.toFixed(2)}%)
              </span>
            </div>
            <div className="flex items-center gap-4 text-[10px] text-muted-foreground font-mono">
              <span>Entry: {pos.entryPrice.toLocaleString()}</span>
              <span>Current: {pos.currentPrice.toLocaleString()}</span>
              <span>Qty: {pos.quantity}</span>
              <span className="text-bearish">SL: {pos.stopLoss.toLocaleString()}</span>
              <span className="text-bullish">TP: {pos.takeProfit.toLocaleString()}</span>
            </div>
          </div>
        ))}
      </div>

      <h2 className="font-mono text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
        Recent Trades
      </h2>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-muted-foreground font-mono text-[10px] uppercase">
              <th className="text-left py-1 pr-2">ID</th>
              <th className="text-left py-1 pr-2">Symbol</th>
              <th className="text-left py-1 pr-2">Side</th>
              <th className="text-right py-1 pr-2">Price</th>
              <th className="text-right py-1 pr-2">P&L</th>
              <th className="text-right py-1 pr-2">Score</th>
              <th className="text-right py-1">Time</th>
            </tr>
          </thead>
          <tbody>
            {recentTrades.map((t) => (
              <tr key={t.id} className="border-t border-border/50">
                <td className="py-1.5 pr-2 font-mono text-muted-foreground">{t.id}</td>
                <td className="py-1.5 pr-2 font-mono font-semibold text-foreground">{t.symbol}</td>
                <td className={`py-1.5 pr-2 font-mono font-semibold ${t.side === "BUY" ? "text-bullish" : "text-bearish"}`}>
                  {t.side}
                </td>
                <td className="py-1.5 pr-2 font-mono text-right text-foreground">{t.price.toLocaleString()}</td>
                <td className={`py-1.5 pr-2 font-mono text-right font-semibold ${
                  t.pnl > 0 ? "text-bullish" : t.pnl < 0 ? "text-bearish" : "text-muted-foreground"
                }`}>
                  {t.pnl !== 0 ? `${t.pnl > 0 ? "+" : ""}₹${t.pnl}` : "—"}
                </td>
                <td className="py-1.5 pr-2 font-mono text-right">
                  <span className={`${t.score >= 80 ? "text-bullish" : t.score >= 50 ? "text-warning" : "text-bearish"}`}>
                    {t.score}
                  </span>
                </td>
                <td className="py-1.5 font-mono text-right text-muted-foreground">{t.time}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default PositionsPanel;
