import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Zap, History, TrendingUp, TrendingDown, Clock, CheckCircle2, XCircle } from "lucide-react";

const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const TradeLog = () => {
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["trades", "history", page],
    queryFn: () => fetch(`${BASE}/api/v1/trades?page=${page}&page_size=50`).then(r => r.json()),
    refetchInterval: 30000,
  });

  const trades = data?.trades || [];
  const fmtCurrency = (v: number) => typeof v === 'number' ? v.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "0.00";

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
            { href: "/news", label: "News" },
            { href: "/risk", label: "Risk" },
            { href: "/history", label: "Trade Log" },
          ].map((l) => (
            <a key={l.href} href={l.href}
              className={`px-3 py-1.5 rounded text-[11px] font-bold uppercase tracking-widest ${
                l.href === "/history" ? "bg-white/5 text-white" : "text-slate-500 hover:text-white"
              }`}>
              {l.label}
            </a>
          ))}
        </nav>
      </header>

      <div className="p-6 max-w-[1200px] mx-auto space-y-6">
        <div>
          <h2 className="text-2xl font-black tracking-tight flex items-center gap-2">
            <History size={22} className="text-purple-400" /> Trade History
          </h2>
          <p className="text-sm text-slate-500 mt-1">Comprehensive log of all agent-executed trades</p>
        </div>

        <div className="bg-[#0a0c10] border border-white/5 rounded-lg overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="bg-[#11141a] text-[10px] uppercase tracking-widest text-slate-500 border-b border-white/5">
              <tr>
                <th className="px-6 py-4 font-bold">Time</th>
                <th className="px-6 py-4 font-bold">Symbol</th>
                <th className="px-6 py-4 font-bold">Type</th>
                <th className="px-6 py-4 font-bold text-right">Qty</th>
                <th className="px-6 py-4 font-bold text-right">Entry</th>
                <th className="px-6 py-4 font-bold text-right">Exit</th>
                <th className="px-6 py-4 font-bold text-right">PnL</th>
                <th className="px-6 py-4 font-bold">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {isLoading ? (
                <tr><td colSpan={8} className="px-6 py-8 text-center text-slate-500">Loading trade history...</td></tr>
              ) : trades.length === 0 ? (
                <tr><td colSpan={8} className="px-6 py-8 text-center text-slate-500">No trades recorded yet.</td></tr>
              ) : (
                trades.map((trade: any) => {
                  const pnl = trade.profit_loss || 0;
                  const isProfit = pnl >= 0;
                  const isClosed = trade.status === "FILLED" || trade.status === "CLOSED";
                  return (
                    <tr key={trade.id} className="hover:bg-white/5 transition-colors">
                      <td className="px-6 py-4 text-slate-400 font-mono text-xs">
                        <div className="flex items-center gap-1.5">
                          <Clock size={12} />
                          {new Date(trade.created_at).toLocaleString("en-IN", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                        </div>
                      </td>
                      <td className="px-6 py-4 font-bold">{trade.symbol}</td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 rounded text-[10px] font-bold ${trade.trade_type === 'BUY' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'}`}>
                          {trade.trade_type}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right font-mono">{trade.quantity?.toFixed(2) || "--"}</td>
                      <td className="px-6 py-4 text-right font-mono">
                        {trade.entry_price ? `₹${fmtCurrency(trade.entry_price)}` : "--"}
                      </td>
                      <td className="px-6 py-4 text-right font-mono">
                         {trade.exit_price ? `₹${fmtCurrency(trade.exit_price)}` : "--"}
                      </td>
                      <td className="px-6 py-4 text-right">
                        {isClosed && trade.profit_loss !== null ? (
                          <>
                            <div className={`font-black italic ${isProfit ? 'text-emerald-400' : 'text-rose-400'} flex items-center justify-end gap-1`}>
                              {isProfit ? <TrendingUp size={14}/> : <TrendingDown size={14}/>}
                              ₹{fmtCurrency(Math.abs(pnl))}
                            </div>
                            <div className={`text-[10px] ${isProfit ? 'text-emerald-500' : 'text-rose-500'}`}>
                              {isProfit ? '+' : ''}{trade.profit_loss_percentage?.toFixed(2) || "0.00"}%
                            </div>
                          </>
                        ) : (
                          <span className="text-slate-600">--</span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-1.5 whitespace-nowrap">
                          {trade.status === 'FILLED' || trade.status === 'CLOSED' ? (
                            <><CheckCircle2 size={14} className="text-emerald-400"/> <span className="text-slate-300 text-xs">{trade.status}</span></>
                          ) : trade.status === 'CANCELLED' ? (
                            <><XCircle size={14} className="text-rose-400"/> <span className="text-slate-500 text-xs">{trade.status}</span></>
                          ) : (
                            <span className="text-amber-400 text-xs">{trade.status}</span>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
          <div className="px-6 py-4 bg-[#11141a] border-t border-white/5 flex items-center justify-between text-xs text-slate-500">
            <span>Showing page {page} of {Math.ceil((data?.total || 0) / 50) || 1}</span>
            <div className="flex gap-2">
              <button 
                disabled={page === 1}
                onClick={() => setPage(p => p - 1)}
                className="px-3 py-1 rounded bg-white/5 hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed">
                Previous
              </button>
              <button
                disabled={!data || trades.length < 50}
                onClick={() => setPage(p => p + 1)}
                className="px-3 py-1 rounded bg-white/5 hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed">
                Next
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TradeLog;
