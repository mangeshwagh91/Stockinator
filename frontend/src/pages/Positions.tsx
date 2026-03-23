import React, { useState, useEffect, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Zap, Briefcase, TrendingUp, TrendingDown, Globe2, Map as GeoMap, BarChart3, ArrowUpRight, Clock, Activity } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from "recharts";

const BASE = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

const LiveClock: React.FC = () => {
  const [time, setTime] = useState(() => new Date().toUTCString().slice(17, 25));
  useEffect(() => {
    const id = setInterval(() => setTime(new Date().toUTCString().slice(17, 25)), 1000);
    return () => clearInterval(id);
  }, []);
  return (
    <div className="hidden md:flex items-center gap-2 text-slate-500 border-l border-white/10 pl-4 h-6">
      <Clock size={12} />
      <span className="text-[11px] font-mono font-semibold tracking-wide">{time} UTC</span>
    </div>
  );
};

const Positions = () => {
  const { data: openData, isLoading } = useQuery({
    queryKey: ["positions", "open"],
    queryFn: () => fetch(`${BASE}/api/v1/trades/positions/open?asset_type=stock`).then(r => r.json()),
    refetchInterval: 15000,
  });

  const { data: accountInfo } = useQuery({
    queryKey: ["account", "info"],
    queryFn: () => fetch(`${BASE}/api/v1/trades/account/info?asset_type=stock`).then(r => r.json()),
    refetchInterval: 30000,
  });

  const { data: stats } = useQuery({
    queryKey: ["trades", "stats"],
    queryFn: () => fetch(`${BASE}/api/v1/trades/summary/stats`).then(r => r.json()),
    refetchInterval: 30000,
  });

  const { data: tradesData } = useQuery({
    queryKey: ["trades", "history", "all"],
    queryFn: () => fetch(`${BASE}/api/v1/trades?page=1&page_size=100`).then(r => r.json()),
    refetchInterval: 30000,
  });

  const positions = openData?.positions || [];
  const account = accountInfo?.account || null;

  const fmtCurrency = (v: number) => v?.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) ?? "0.00";

  const chartData = useMemo(() => {
    if (!tradesData?.trades) return [];
    const sorted = [...tradesData.trades].sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
    let cumulative = 0;
    return sorted.map(t => {
      cumulative += (t.profit_loss || 0);
      return {
        date: new Date(t.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        pnl: cumulative
      };
    });
  }, [tradesData]);

  // Gradient conditional colors based on net PnL
  const currentNet = chartData.length > 0 ? chartData[chartData.length - 1].pnl : 0;
  const isNetPositive = currentNet >= 0;
  const strokeColor = isNetPositive ? "#10b981" : "#f43f5e";

  return (
    <div className="min-h-screen bg-[#05070a] text-slate-100 font-sans flex flex-col overflow-hidden">
      {/* ── Header ── */}
      <header className="h-14 border-b border-white/5 bg-[#0a0c10] flex items-center justify-between px-4 sticky top-0 z-50">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-600 rounded flex items-center justify-center shadow-[0_0_15px_rgba(37,99,235,0.3)]">
              <Zap size={18} className="text-white fill-white" />
            </div>
            <div className="flex flex-col leading-none">
              <span className="text-xs font-black tracking-widest text-white uppercase">GEOTRADE</span>
              <span className="text-[10px] font-semibold text-slate-500 tracking-tight mt-0.5 uppercase">TRADER v2.0</span>
            </div>
          </div>
          <div className="hidden md:flex flex-col border-l border-white/10 pl-6 h-8 justify-center">
            <span className="text-[10px] font-semibold text-slate-500 tracking-widest uppercase mb-0.5">GLOBAL TENSION INDEX (GTI)</span>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold text-white leading-none">71.4</span>
              <span className="text-[11px] font-semibold text-orange-400 flex items-center gap-0.5">
                <ArrowUpRight size={10} /> +2.1
              </span>
              <div className="px-1.5 py-0.5 rounded bg-orange-500/10 text-[10px] font-bold text-orange-400 tracking-tight uppercase border border-orange-500/20 ml-1">
                ELEVATED
              </div>
            </div>
          </div>
        </div>

        <div className="hidden lg:flex items-center gap-0.5 p-0.5 rounded-lg bg-black/40 border border-white/5 shadow-inner">
          <Link to="/" className="px-4 py-1.5 rounded-md text-[11px] font-semibold tracking-wide text-slate-400 hover:text-white transition-all uppercase flex items-center gap-2">
            <Globe2 size={12} /> EARTH PULSE
          </Link>
          <button className="px-4 py-1.5 rounded-md text-[11px] font-semibold tracking-wide text-slate-400 hover:text-white transition-all uppercase flex items-center gap-2">
            <GeoMap size={12} /> GEO MAP
          </button>
          <Link to="/signals" className="px-4 py-1.5 rounded-md text-[11px] font-semibold tracking-wide text-slate-400 hover:text-white transition-all uppercase flex items-center gap-2">
            <BarChart3 size={12} /> AI SIGNALS
          </Link>
          <Link to="/positions" className="px-5 py-1.5 rounded-md text-[11px] font-bold tracking-wide bg-[#1a1f26] text-white border border-white/10 shadow-lg uppercase flex items-center gap-2">
            <Briefcase size={12} className="text-blue-400" /> PORTFOLIO
          </Link>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/5 border border-emerald-500/10">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-[11px] font-semibold text-emerald-500 tracking-wide uppercase">LIVE</span>
          </div>
          <LiveClock />
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto p-8 relative">
        <div className="max-w-[1200px] mx-auto space-y-8 relative z-10">
          <div>
            <h2 className="text-2xl font-black tracking-tighter flex items-center gap-2 text-white">
              <Briefcase size={22} className="text-blue-500 hidden sm:block" /> LIVE PORTFOLIO
            </h2>
            <p className="text-[13px] font-semibold text-[#64748b] tracking-wide mt-1 uppercase">Real-time open positions and performance metrics</p>
          </div>

          {/* Account Info Cards */}
          {account && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-[#0a0c10] border border-white/5 rounded-xl p-5 shadow-[0_8px_30px_rgba(0,0,0,0.5)]">
                <div className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.15em] mb-2 flex items-center gap-1.5">
                  <div className="w-1 h-1 rounded-full bg-blue-500" /> Total Equity
                </div>
                <div className="text-3xl font-black tracking-tight text-white">₹{fmtCurrency(parseFloat(account.equity || "0"))}</div>
              </div>
              <div className="bg-[#0a0c10] border border-white/5 rounded-xl p-5 shadow-[0_8px_30px_rgba(0,0,0,0.5)]">
                <div className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.15em] mb-2 flex items-center gap-1.5">
                  <div className="w-1 h-1 rounded-full bg-emerald-500" /> Cash Balance
                </div>
                <div className="text-3xl font-black tracking-tight text-slate-200">₹{fmtCurrency(parseFloat(account.cash || "0"))}</div>
              </div>
              <div className="bg-[#0a0c10] border border-white/5 rounded-xl p-5 shadow-[0_8px_30px_rgba(0,0,0,0.5)]">
                <div className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.15em] mb-2 flex items-center gap-1.5">
                  <div className="w-1 h-1 rounded-full bg-orange-500" /> Buying Power
                </div>
                <div className="text-3xl font-black tracking-tight text-slate-200">₹{fmtCurrency(parseFloat(account.buying_power || "0"))}</div>
              </div>
              <div className="bg-[#0a0c10] border border-emerald-500/20 rounded-xl p-5 shadow-[0_0_20px_rgba(16,185,129,0.05)] relative overflow-hidden">
                <div className="absolute -right-4 -top-4 text-emerald-500/10"><Briefcase size={80} /></div>
                <div className="text-[10px] font-bold text-emerald-500 uppercase tracking-[0.15em] mb-2 relative z-10">Account Status</div>
                <div className="text-xl font-black tracking-widest text-emerald-400 mt-2 relative z-10 flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"/>
                  {account.status || "ACTIVE"}
                </div>
              </div>
            </div>
          )}

          {/* Performance Analytics Section */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Chart Area */}
            <div className="lg:col-span-2 bg-[#0a0c10] border border-white/5 rounded-xl p-5 shadow-[0_8px_30px_rgba(0,0,0,0.5)]">
               <h3 className="text-[11px] font-bold text-slate-400 uppercase tracking-[0.1em] mb-4 flex items-center gap-2"><Activity size={14}/> Cumulative Returns (Recent History)</h3>
               <div className="h-[220px] w-full">
                  {!chartData.length ? (
                    <div className="h-full w-full flex items-center justify-center text-[10px] uppercase tracking-widest text-slate-600">No trade history available to chart</div>
                  ) : (
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                        <defs>
                          <linearGradient id="colorPnl" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor={strokeColor} stopOpacity={0.4}/>
                            <stop offset="95%" stopColor={strokeColor} stopOpacity={0}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                        <XAxis dataKey="date" stroke="#64748b" fontSize={10} tickLine={false} axisLine={false} minTickGap={30} />
                        <YAxis stroke="#64748b" fontSize={10} tickLine={false} axisLine={false} tickFormatter={(value) => `₹${value}`} />
                        <RechartsTooltip 
                          contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px', fontSize: '12px', fontWeight: 'bold' }}
                          itemStyle={{ color: strokeColor }}
                          formatter={(value: number) => [`₹${value.toFixed(2)}`, 'Nav']}
                        />
                        <Area type="monotone" dataKey="pnl" stroke={strokeColor} strokeWidth={2} fillOpacity={1} fill="url(#colorPnl)" />
                      </AreaChart>
                    </ResponsiveContainer>
                  )}
               </div>
            </div>

            {/* Stats Grid */}
            <div className="bg-[#0a0c10] border border-white/5 rounded-xl p-5 shadow-[0_8px_30px_rgba(0,0,0,0.5)] flex flex-col gap-4">
               <h3 className="text-[11px] font-bold text-slate-400 uppercase tracking-[0.1em] mb-1">Trade Statistics (30d)</h3>
               
               <div className="grid grid-cols-2 gap-3">
                 <div className="bg-[#11141a] p-3 rounded-lg border border-white/5">
                   <div className="text-[9px] font-semibold text-slate-500 uppercase tracking-widest mb-1">Win Rate</div>
                   <div className="text-lg font-black text-white">{stats?.win_rate?.toFixed(1) || "0.0"}%</div>
                 </div>
                 <div className="bg-[#11141a] p-3 rounded-lg border border-white/5">
                   <div className="text-[9px] font-semibold text-slate-500 uppercase tracking-widest mb-1">Total Trades</div>
                   <div className="text-lg font-black text-white">{stats?.total_trades || 0}</div>
                 </div>
                 <div className="bg-[#11141a] p-3 rounded-lg border border-white/5">
                   <div className="text-[9px] font-semibold text-slate-500 uppercase tracking-widest mb-1">Best Trade</div>
                   <div className="text-sm font-black text-emerald-400 tracking-tight">₹{fmtCurrency(stats?.best_trade || 0)}</div>
                 </div>
                 <div className="bg-[#11141a] p-3 rounded-lg border border-white/5">
                   <div className="text-[9px] font-semibold text-slate-500 uppercase tracking-widest mb-1">Worst Trade</div>
                   <div className="text-sm font-black text-rose-400 tracking-tight">₹{fmtCurrency(stats?.worst_trade || 0)}</div>
                 </div>
               </div>
               
               <div className="mt-auto pt-4 border-t border-white/5">
                 <div className="flex justify-between items-end">
                   <div>
                     <div className="text-[9px] font-semibold text-slate-500 uppercase tracking-widest mb-1">Net Realized PnL</div>
                     <div className={`text-2xl font-black ${(stats?.total_profit_loss || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {(stats?.total_profit_loss || 0) >= 0 ? '+' : '-'}₹{fmtCurrency(Math.abs(stats?.total_profit_loss || 0))}
                     </div>
                   </div>
                 </div>
               </div>
            </div>
          </div>

          {/* Positions Table */}
          <div className="bg-[#0a0c10] border border-white/5 rounded-xl overflow-hidden shadow-[0_8px_30px_rgba(0,0,0,0.5)]">
            <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between">
               <span className="text-[11px] font-bold text-slate-400 uppercase tracking-[0.1em]">Open Assets</span>
               <span className="text-[10px] font-mono text-slate-600">{positions.length} ACTIVE</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm whitespace-nowrap">
                <thead className="bg-[#11141a] text-[10px] uppercase tracking-widest text-[#64748b]">
                  <tr>
                    <th className="px-6 py-4 font-bold">Symbol</th>
                    <th className="px-6 py-4 font-bold">Side</th>
                    <th className="px-6 py-4 font-bold text-right">Qty</th>
                    <th className="px-6 py-4 font-bold text-right">Entry Price</th>
                    <th className="px-6 py-4 font-bold text-right">Current Price</th>
                    <th className="px-6 py-4 font-bold text-right">Market Value</th>
                    <th className="px-6 py-4 font-bold text-right">Unrealized PnL</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {isLoading ? (
                    <tr><td colSpan={7} className="px-6 py-12 text-center text-[12px] font-semibold tracking-widest text-slate-500 uppercase">Loading live positions...</td></tr>
                  ) : positions.length === 0 ? (
                    <tr><td colSpan={7} className="px-6 py-12 text-center text-[12px] font-semibold tracking-widest text-slate-500 uppercase">No open positions. System is waiting for signals.</td></tr>
                  ) : (
                    positions.map((pos: any, i: number) => {
                      const pnl = parseFloat(pos.unrealized_pl || 0);
                      const pnlPct = parseFloat(pos.unrealized_plpc || 0) * 100;
                      const isProfit = pnl >= 0;
                      return (
                        <tr key={i} className="hover:bg-white/2 transition-colors">
                          <td className="px-6 py-4 font-black tracking-tight text-white">{pos.symbol}</td>
                          <td className="px-6 py-4">
                            <span className={`px-2 py-1 rounded text-[10px] font-bold tracking-wider ${pos.side === 'long' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'}`}>
                              {pos.side ? pos.side.toUpperCase() : "LONG"}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-right font-mono font-medium text-slate-300">{parseFloat(pos.qty || "0").toFixed(2)}</td>
                          <td className="px-6 py-4 text-right font-mono font-medium text-slate-400">₹{fmtCurrency(parseFloat(pos.avg_entry_price || "0"))}</td>
                          <td className="px-6 py-4 text-right font-mono font-bold text-white">₹{fmtCurrency(parseFloat(pos.current_price || "0"))}</td>
                          <td className="px-6 py-4 text-right font-mono font-medium text-blue-300">₹{fmtCurrency(parseFloat(pos.market_value || "0"))}</td>
                          <td className="px-6 py-4 text-right">
                            <div className={`font-black italic flex items-center justify-end gap-1 ${isProfit ? 'text-emerald-400' : 'text-rose-400'}`}>
                              {isProfit ? <TrendingUp size={14}/> : <TrendingDown size={14}/>}
                              {isProfit ? '+' : '-'}₹{fmtCurrency(Math.abs(pnl))}
                            </div>
                            <div className={`text-[10px] font-bold mt-0.5 ${isProfit ? 'text-emerald-500' : 'text-rose-500'}`}>
                              {isProfit ? '+' : ''}{pnlPct.toFixed(2)}%
                            </div>
                          </td>
                        </tr>
                      )
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>
      
      {/* Background glow effects */}
      <div className="fixed -bottom-40 -right-40 w-96 h-96 bg-blue-600/10 rounded-full blur-[100px] pointer-events-none" />
      <div className="fixed -top-40 -left-40 w-96 h-96 bg-emerald-600/5 rounded-full blur-[100px] pointer-events-none" />
    </div>
  );
};

export default Positions;
