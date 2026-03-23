import { useQuery } from "@tanstack/react-query";
import {
  Zap, Shield, AlertTriangle, Activity, TrendingUp,
  TrendingDown, Target, BarChart3,
} from "lucide-react";

const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const Risk = () => {
  const { data: status } = useQuery({
    queryKey: ["system-status"],
    queryFn: () => fetch(`${BASE}/api/v1/control/status`).then((r) => r.json()),
    refetchInterval: 15000,
    retry: false,
  });

  const { data: winRate } = useQuery({
    queryKey: ["win-rate"],
    queryFn: () => fetch(`${BASE}/api/v1/system/memory/win-rate`).then((r) => r.json()),
    retry: false,
  });

  const risk = status?.risk_metrics || {};
  const fmtCurrency = (v: number) =>
    v?.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) ?? "0.00";

  return (
    <div className="min-h-screen bg-[#05070a] text-slate-100">
      <header className="border-b border-white/5 bg-[#0a0c10] px-6 py-3 flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Zap size={20} className="text-emerald-400" />
          <h1 className="text-lg font-black tracking-tight">STOCKINATOR</h1>
        </div>
        <nav className="flex gap-1 ml-6">
          {[
            { href: "/", label: "Dashboard" },
            { href: "/signals", label: "AI Signals" },
            { href: "/positions", label: "Positions" },
            { href: "/risk", label: "Risk" },
          ].map((l) => (
            <a key={l.href} href={l.href}
              className={`px-3 py-1.5 rounded text-[11px] font-bold uppercase tracking-widest ${
                l.href === "/risk" ? "bg-white/5 text-white" : "text-slate-500 hover:text-white"
              }`}>
              {l.label}
            </a>
          ))}
        </nav>
      </header>

      <div className="p-6 max-w-[1200px] mx-auto space-y-6">
        <div>
          <h2 className="text-2xl font-black tracking-tight flex items-center gap-2">
            <Shield size={22} className="text-amber-400" /> Risk Management
          </h2>
          <p className="text-sm text-slate-500 mt-1">Real-time risk controls and position limits</p>
        </div>

        {/* System Status */}
        <div className="grid grid-cols-2 gap-4">
          <div className={`rounded-lg border p-5 ${
            status?.trading_active
              ? "border-emerald-500/20 bg-emerald-500/5"
              : "border-rose-500/20 bg-rose-500/5"
          }`}>
            <div className="text-[9px] font-bold uppercase tracking-widest text-slate-500 mb-2">Trading Status</div>
            <div className={`text-2xl font-black italic ${status?.trading_active ? "text-emerald-400" : "text-rose-400"}`}>
              {status?.trading_active ? "ACTIVE" : "STOPPED"}
            </div>
            <div className="text-[10px] text-slate-500 mt-1">
              Mode: {status?.paper_trading ? "Paper" : "Live"} · Threshold: {status?.threshold}%
            </div>
          </div>
          <div className={`rounded-lg border p-5 ${
            status?.broker_connected
              ? "border-emerald-500/20 bg-emerald-500/5"
              : "border-amber-500/20 bg-amber-500/5"
          }`}>
            <div className="text-[9px] font-bold uppercase tracking-widest text-slate-500 mb-2">Broker Connection</div>
            <div className={`text-2xl font-black italic ${status?.broker_connected ? "text-emerald-400" : "text-amber-400"}`}>
              {status?.broker_connected ? "CONNECTED" : "DISCONNECTED"}
            </div>
            <div className="text-[10px] text-slate-500 mt-1">
              Cooldown: {status?.cooldown_minutes ?? 5} min
            </div>
          </div>
        </div>

        {/* Risk Metrics */}
        <div className="grid grid-cols-3 gap-4">
          {/* Daily PnL */}
          <div className="bg-[#0a0c10] border border-white/5 rounded-lg p-5">
            <div className="flex items-center gap-2 mb-3">
              <BarChart3 size={14} className="text-blue-400" />
              <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">Today's PnL</span>
            </div>
            <div className={`text-2xl font-black italic ${(risk.today_pnl || 0) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
              ₹{fmtCurrency(risk.today_pnl || 0)}
            </div>
            <div className="mt-3">
              <div className="flex justify-between text-[9px] text-slate-500 mb-1">
                <span>Daily Loss Used</span>
                <span>{(risk.daily_loss_used_pct || 0).toFixed(1)}%</span>
              </div>
              <div className="h-2 bg-[#1a1f26] rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${
                    (risk.daily_loss_used_pct || 0) > 80 ? "bg-rose-500" :
                    (risk.daily_loss_used_pct || 0) > 50 ? "bg-amber-500" : "bg-emerald-500"
                  }`}
                  style={{ width: `${Math.min(100, risk.daily_loss_used_pct || 0)}%` }}
                />
              </div>
              <div className="text-[9px] text-slate-600 mt-1">
                Limit: ₹{fmtCurrency(risk.max_daily_loss || 5000)}
              </div>
            </div>
          </div>

          {/* Open Positions */}
          <div className="bg-[#0a0c10] border border-white/5 rounded-lg p-5">
            <div className="flex items-center gap-2 mb-3">
              <Activity size={14} className="text-purple-400" />
              <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">Open Positions</span>
            </div>
            <div className="text-2xl font-black italic">{risk.open_positions ?? 0}</div>
            <div className="mt-3">
              <div className="flex justify-between text-[9px] text-slate-500 mb-1">
                <span>Capacity</span>
                <span>{risk.open_positions ?? 0} / {risk.max_open_positions ?? 5}</span>
              </div>
              <div className="h-2 bg-[#1a1f26] rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full bg-purple-500"
                  style={{ width: `${Math.min(100, ((risk.open_positions ?? 0) / (risk.max_open_positions ?? 5)) * 100)}%` }}
                />
              </div>
            </div>
          </div>

          {/* Risk Per Trade */}
          <div className="bg-[#0a0c10] border border-white/5 rounded-lg p-5">
            <div className="flex items-center gap-2 mb-3">
              <Target size={14} className="text-amber-400" />
              <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">Risk Per Trade</span>
            </div>
            <div className="text-2xl font-black italic text-amber-400">{risk.risk_per_trade_pct ?? 2}%</div>
            <div className="mt-3 text-[10px] text-slate-500 space-y-1">
              <div>Max Position: ₹{fmtCurrency(risk.max_position_size || 50000)}</div>
              <div>Method: ATR-based + Equity %</div>
            </div>
          </div>
        </div>

        {/* Learning Stats */}
        <div className="bg-[#0a0c10] border border-white/5 rounded-lg p-5">
          <div className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mb-4">Trading Performance</div>
          <div className="grid grid-cols-3 gap-6">
            <div>
              <div className="text-[10px] text-slate-500 mb-1">Total Trades</div>
              <div className="text-xl font-black italic">{winRate?.trades ?? 0}</div>
            </div>
            <div>
              <div className="text-[10px] text-slate-500 mb-1">Win Rate</div>
              <div className={`text-xl font-black italic ${(winRate?.win_rate ?? 0) >= 50 ? "text-emerald-400" : "text-rose-400"}`}>
                {winRate?.win_rate ?? 0}%
              </div>
            </div>
            <div>
              <div className="text-[10px] text-slate-500 mb-1">Avg PnL / Trade</div>
              <div className={`text-xl font-black italic ${(winRate?.avg_pnl ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                ₹{fmtCurrency(winRate?.avg_pnl ?? 0)}
              </div>
            </div>
          </div>
        </div>

        {/* Risk Rules */}
        <div className="bg-[#0a0c10] border border-white/5 rounded-lg p-5">
          <div className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mb-3">Active Risk Rules</div>
          <div className="space-y-2 text-[11px]">
            {[
              { rule: "Daily loss limit enforced", status: "active", icon: Shield },
              { rule: "Max open positions capped", status: "active", icon: Activity },
              { rule: "ATR-based position sizing", status: "active", icon: Target },
              { rule: "Brokerage + slippage cost check (₹50 min profit)", status: "active", icon: BarChart3 },
              { rule: "Cooldown period between trades", status: "active", icon: AlertTriangle },
              { rule: "Score threshold gating", status: "active", icon: TrendingUp },
            ].map((r, i) => (
              <div key={i} className="flex items-center gap-3 bg-black/30 rounded px-3 py-2">
                <r.icon size={12} className="text-emerald-400 flex-shrink-0" />
                <span className="flex-1">{r.rule}</span>
                <span className="text-[9px] font-bold text-emerald-400 uppercase">Active</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Risk;
