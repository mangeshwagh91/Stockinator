import { riskMetrics } from "@/data/mockData";
import { useState } from "react";

const RiskPanel = () => {
  const [isTrading, setIsTrading] = useState(true);
  const [threshold, setThreshold] = useState(80);

  const dailyLossUsed = Math.abs(riskMetrics.currentDailyLoss) / Math.abs(riskMetrics.maxDailyLoss) * 100;
  const capitalUsedPercent = (riskMetrics.capitalUsed / riskMetrics.totalCapital) * 100;

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <h2 className="font-mono text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-4">
        Risk & Controls
      </h2>

      {/* Trading Toggle */}
      <div className="flex items-center justify-between mb-4 p-3 rounded border border-border bg-secondary/20">
        <div>
          <div className="text-xs font-semibold text-foreground">Auto-Trading</div>
          <div className="text-[10px] text-muted-foreground">{isTrading ? "System is actively trading" : "Trading paused"}</div>
        </div>
        <button
          onClick={() => setIsTrading(!isTrading)}
          className={`px-4 py-2 rounded font-mono text-xs font-bold transition-all ${
            isTrading
              ? "bg-bullish/20 text-bullish border border-bullish/30 hover:bg-bullish/30"
              : "bg-bearish/20 text-bearish border border-bearish/30 hover:bg-bearish/30"
          }`}
        >
          {isTrading ? "● LIVE" : "■ PAUSED"}
        </button>
      </div>

      {/* Emergency Stop */}
      <button
        onClick={() => setIsTrading(false)}
        className="w-full mb-4 py-2.5 rounded font-mono text-xs font-bold bg-destructive/20 text-destructive border border-destructive/30 hover:bg-destructive/40 transition-all"
      >
        ⚠ EMERGENCY STOP
      </button>

      {/* Score Threshold */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-muted-foreground">Score Threshold</span>
          <span className="font-mono text-xs font-bold text-primary">{threshold}%</span>
        </div>
        <input
          type="range"
          min={50}
          max={95}
          value={threshold}
          onChange={(e) => setThreshold(Number(e.target.value))}
          className="w-full h-1 bg-muted rounded-full appearance-none cursor-pointer accent-primary"
        />
      </div>

      {/* Risk Metrics */}
      <div className="space-y-3">
        <MetricBar label="Daily P&L" value={`₹${riskMetrics.dailyPnL.toLocaleString()}`} percent={riskMetrics.dailyPnLPercent * 100} color="bullish" />
        <MetricBar label="Daily Loss Limit" value={`₹${Math.abs(riskMetrics.currentDailyLoss)} / ₹${Math.abs(riskMetrics.maxDailyLoss)}`} percent={dailyLossUsed} color="bearish" />
        <MetricBar label="Capital Deployed" value={`${capitalUsedPercent.toFixed(1)}%`} percent={capitalUsedPercent} color="primary" />

        <div className="grid grid-cols-2 gap-2 pt-2">
          <StatBox label="Positions" value={`${riskMetrics.currentPositions}/${riskMetrics.maxPositions}`} />
          <StatBox label="Trades Today" value={String(riskMetrics.tradesCount)} />
          <StatBox label="Brokerage Paid" value={`₹${riskMetrics.brokeragePaid}`} />
          <StatBox label="Cost/Trade" value="₹50" />
        </div>
      </div>
    </div>
  );
};

const MetricBar = ({ label, value, percent, color }: { label: string; value: string; percent: number; color: string }) => (
  <div>
    <div className="flex items-center justify-between mb-1">
      <span className="text-[10px] text-muted-foreground">{label}</span>
      <span className={`font-mono text-[10px] font-semibold ${color === "bullish" ? "text-bullish" : color === "bearish" ? "text-bearish" : "text-primary"}`}>{value}</span>
    </div>
    <div className="w-full h-1 rounded-full bg-muted overflow-hidden">
      <div
        className={`h-full rounded-full transition-all ${color === "bullish" ? "bg-bullish" : color === "bearish" ? "bg-bearish" : "bg-primary"}`}
        style={{ width: `${Math.min(percent, 100)}%` }}
      />
    </div>
  </div>
);

const StatBox = ({ label, value }: { label: string; value: string }) => (
  <div className="rounded border border-border bg-secondary/20 p-2 text-center">
    <div className="font-mono text-sm font-bold text-foreground">{value}</div>
    <div className="text-[10px] text-muted-foreground">{label}</div>
  </div>
);

export default RiskPanel;
