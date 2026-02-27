import { equityCurve, scoreHistory } from "@/data/mockData";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from "recharts";

const ChartPanel = () => {
  return (
    <div className="space-y-4">
      {/* Equity Curve */}
      <div className="rounded-lg border border-border bg-card p-4">
        <h2 className="font-mono text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-4">
          Equity Curve
        </h2>
        <div className="h-[200px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={equityCurve}>
              <defs>
                <linearGradient id="equityGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="hsl(174, 72%, 52%)" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="hsl(174, 72%, 52%)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(222, 25%, 16%)" />
              <XAxis dataKey="day" tick={{ fontSize: 10, fill: "hsl(215, 15%, 50%)" }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fontSize: 10, fill: "hsl(215, 15%, 50%)" }} tickLine={false} axisLine={false} tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}K`} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(222, 41%, 9%)",
                  border: "1px solid hsl(222, 25%, 16%)",
                  borderRadius: "8px",
                  fontSize: "11px",
                  fontFamily: "JetBrains Mono",
                }}
                labelStyle={{ color: "hsl(215, 15%, 50%)" }}
              />
              <Area type="monotone" dataKey="equity" stroke="hsl(174, 72%, 52%)" fill="url(#equityGrad)" strokeWidth={2} dot={false} name="Portfolio" />
              <Line type="monotone" dataKey="benchmark" stroke="hsl(215, 15%, 50%)" strokeWidth={1} strokeDasharray="4 4" dot={false} name="Benchmark" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Score History */}
      <div className="rounded-lg border border-border bg-card p-4">
        <h2 className="font-mono text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-4">
          Score History (24h)
        </h2>
        <div className="h-[180px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={scoreHistory}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(222, 25%, 16%)" />
              <XAxis dataKey="time" tick={{ fontSize: 10, fill: "hsl(215, 15%, 50%)" }} tickLine={false} axisLine={false} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: "hsl(215, 15%, 50%)" }} tickLine={false} axisLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(222, 41%, 9%)",
                  border: "1px solid hsl(222, 25%, 16%)",
                  borderRadius: "8px",
                  fontSize: "11px",
                  fontFamily: "JetBrains Mono",
                }}
              />
              <Line type="monotone" dataKey="RELIANCE" stroke="hsl(174, 72%, 52%)" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="BTC/USD" stroke="hsl(38, 92%, 50%)" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="TCS" stroke="hsl(210, 80%, 60%)" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="flex items-center justify-center gap-4 mt-2">
          <LegendDot color="hsl(174, 72%, 52%)" label="RELIANCE" />
          <LegendDot color="hsl(38, 92%, 50%)" label="BTC/USD" />
          <LegendDot color="hsl(210, 80%, 60%)" label="TCS" />
        </div>
      </div>
    </div>
  );
};

const LegendDot = ({ color, label }: { color: string; label: string }) => (
  <div className="flex items-center gap-1.5">
    <div className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
    <span className="font-mono text-[10px] text-muted-foreground">{label}</span>
  </div>
);

export default ChartPanel;
