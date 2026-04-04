import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowUpRight,
  ArrowDownRight,
  BarChart3,
  Briefcase,
  Clock,
  Globe2,
  Map as GeoMap,
  Search,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  Zap,
  RefreshCw,
} from 'lucide-react';
import { WatchlistSymbol } from '@/services/api';
import { useSymbols } from '@/hooks/useSymbols';
import { useQuote } from '@/hooks/useQuote';
import { useChart } from '@/hooks/useChart';
import MiniSparkline from './MiniSparkline';
import StockDetailPanel from './StockDetailPanel';

// ─── Small card with live quote + sparkline ───────────────────────────────────
const AssetCard: React.FC<{
  stock: WatchlistSymbol;
  isSelected: boolean;
  onClick: () => void;
}> = ({ stock, isSelected, onClick }) => {
  const { data: quote } = useQuote(stock.symbol);
  const { data: chartData } = useChart(stock.symbol, '1mo', '1d');

  const isUp = (quote?.change ?? 0) >= 0;
  const priceFmt = (n: number) =>
    n.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  return (
    <div
      onClick={onClick}
      className={`p-4 border rounded-md transition-all cursor-pointer ${
        isSelected
          ? 'bg-[#0f1218] border-blue-500/50 shadow-[0_4px_20px_rgba(37,99,235,0.12)]'
          : 'bg-transparent border-white/5 hover:border-white/10 hover:bg-white/2'
      }`}
    >
      {/* Top row: symbol + badge + confidence */}
      <div className="flex justify-between items-start mb-2">
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-black tracking-tighter text-white italic truncate">{stock.symbol}</span>
            <span
              className={`text-[9px] font-bold px-1.5 py-0.5 rounded italic flex-shrink-0 ${
                isUp
                  ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20'
                  : 'bg-rose-500/10 text-rose-500 border border-rose-500/20'
              }`}
            >
              {isUp ? 'BULL' : 'BEAR'}
            </span>
          </div>
          <div className="text-[10px] font-medium text-slate-500 uppercase mt-0.5 truncate">{stock.exchange} · {stock.segment}</div>
        </div>
        <div className="text-right flex-shrink-0 ml-2">
          {quote ? (
            <>
              <div className="text-[13px] font-black text-white italic">{priceFmt(quote.price)}</div>
              <div className={`text-[10px] font-bold flex items-center justify-end gap-0.5 ${isUp ? 'text-emerald-400' : 'text-rose-400'}`}>
                {isUp ? <ArrowUpRight size={10} /> : <ArrowDownRight size={10} />}
                {isUp ? '+' : ''}{quote.change_pct.toFixed(2)}%
              </div>
            </>
          ) : (
            <div className="text-[11px] font-mono text-slate-600">—</div>
          )}
        </div>
      </div>

      {/* Sparkline */}
      <div className="my-2">
        <MiniSparkline candles={chartData?.candles ?? []} isPositive={isUp} height={36} />
      </div>

      {/* Full name */}
      <div className="text-[10px] font-medium text-slate-500 italic truncate">{stock.name}</div>
    </div>
  );
};

// ─── Unique segments extracted from watchlist ─────────────────────────────────
const extractSegments = (symbols: WatchlistSymbol[]): string[] => {
  const seen = new Set<string>();
  const result: string[] = ['All'];
  symbols.forEach((s) => {
    if (!seen.has(s.segment)) {
      seen.add(s.segment);
      result.push(s.segment);
    }
  });
  return result;
};

// ─── Live UTC clock ───────────────────────────────────────────────────────────
const LiveClock: React.FC = () => {
  const [time, setTime] = useState(() => new Date().toUTCString().slice(17, 25));
  useEffect(() => {
    const id = setInterval(() => setTime(new Date().toUTCString().slice(17, 25)), 1000);
    return () => clearInterval(id);
  }, []);
  return (
    <div className="flex items-center gap-2 text-slate-500 border-l border-white/10 pl-4 h-6">
      <Clock size={12} />
      <span className="text-[11px] font-mono font-semibold tracking-wide">{time} UTC</span>
    </div>
  );
};

// ─── Main Page ────────────────────────────────────────────────────────────────
const AISignalsPage: React.FC = () => {
  const { data: symbols, isLoading, isError, refetch } = useSymbols();
  const [selectedSymbol, setSelectedSymbol] = useState<WatchlistSymbol | null>(null);
  const [selectedSegment, setSelectedSegment] = useState('All');
  const [search, setSearch] = useState('');

  // Auto-select first symbol when list loads
  useEffect(() => {
    if (symbols && symbols.length > 0 && !selectedSymbol) {
      setSelectedSymbol(symbols[0]);
    }
  }, [symbols, selectedSymbol]);

  const segments = useMemo(() => extractSegments(symbols ?? []), [symbols]);

  const filtered = useMemo(() => {
    if (!symbols) return [];
    const q = search.trim().toLowerCase();
    return symbols.filter((s) => {
      const matchSeg = selectedSegment === 'All' || s.segment === selectedSegment;
      const matchSearch = !q || s.symbol.toLowerCase().includes(q) || s.name.toLowerCase().includes(q);
      return matchSeg && matchSearch;
    });
  }, [symbols, selectedSegment, search]);

  return (
    <div className="h-screen bg-[#05070a] text-[#f8fafc] font-sans flex flex-col overflow-hidden">
      {/* ── Header ── */}
      <header className="h-14 border-b border-white/5 bg-[#0a0c10] flex items-center justify-between px-4 sticky top-0 z-50">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-600 rounded flex items-center justify-center shadow-[0_0_15px_rgba(37,99,235,0.3)]">
              <Zap size={18} className="text-white fill-white" />
            </div>
            <div className="flex flex-col leading-none">
              <span className="text-xs font-black tracking-widest text-white uppercase">STOCKINATOR</span>
              <span className="text-[10px] font-semibold text-slate-500 tracking-tight mt-0.5 uppercase">TRADER v2.0</span>
            </div>
          </div>
          <div className="flex flex-col border-l border-white/10 pl-6 h-8 justify-center">
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

        <div className="flex items-center gap-0.5 p-0.5 rounded-lg bg-black/40 border border-white/5 shadow-inner">
          <Link
            to="/"
            className="px-4 py-1.5 rounded-md text-[11px] font-semibold tracking-wide text-slate-400 hover:text-white transition-all uppercase flex items-center gap-2"
          >
            <Globe2 size={12} /> EARTH PULSE
          </Link>
          <button className="px-4 py-1.5 rounded-md text-[11px] font-semibold tracking-wide text-slate-400 hover:text-white transition-all uppercase flex items-center gap-2">
            <GeoMap size={12} /> GEO MAP
          </button>
          <button className="px-5 py-1.5 rounded-md text-[11px] font-bold tracking-wide bg-[#1a1f26] text-white border border-white/10 shadow-lg uppercase flex items-center gap-2">
            <BarChart3 size={12} className="text-blue-400" /> AI SIGNALS
          </button>
          <Link to="/positions" className="px-4 py-1.5 rounded-md text-[11px] font-semibold tracking-wide text-slate-400 hover:text-white transition-all uppercase flex items-center gap-2">
            <Briefcase size={12} /> PORTFOLIO
          </Link>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/5 border border-emerald-500/10">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-[11px] font-semibold text-emerald-500 tracking-wide uppercase">LIVE</span>
          </div>
          <LiveClock />
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* ── Sidebar: segments ── */}
        <aside className="w-48 border-r border-white/5 bg-[#0a0c10] flex flex-col py-4 flex-shrink-0">
          <div className="px-4 mb-4">
            <span className="text-[10px] font-bold text-slate-500 tracking-[0.18em] uppercase">Market Segments</span>
          </div>
          <div className="flex-1 overflow-y-auto custom-scrollbar px-3 space-y-0.5">
            {segments.map((seg) => (
              <button
                key={seg}
                onClick={() => setSelectedSegment(seg)}
                className={`w-full text-left px-3 py-2 rounded-md text-[11px] font-semibold tracking-tight transition-all ${
                  selectedSegment === seg
                    ? 'bg-[#1a1f26] text-white border border-white/5 shadow-sm'
                    : 'text-slate-500 hover:text-slate-300 hover:bg-white/2'
                }`}
              >
                {seg}
              </button>
            ))}
          </div>
        </aside>

        {/* ── Asset List ── */}
        <div className="w-[260px] border-r border-white/5 bg-[#080a0e] flex flex-col flex-shrink-0">
          {/* Search */}
          <div className="p-3 border-b border-white/5 flex gap-2 items-center">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600" size={12} />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search symbol or name..."
                className="w-full bg-black/40 border border-white/5 rounded pl-9 pr-4 py-2 text-[12px] text-white placeholder:text-slate-500 font-medium focus:outline-none focus:border-blue-500/30 transition-colors"
              />
            </div>
            <button
              onClick={() => refetch()}
              className="p-2 rounded border border-white/5 text-slate-500 hover:text-white hover:border-white/10 transition-all"
              title="Refresh"
            >
              <RefreshCw size={12} />
            </button>
          </div>

          {/* Count */}
          <div className="px-4 py-2 border-b border-white/5 flex items-center justify-between">
            <span className="text-[10px] font-semibold text-slate-600 uppercase tracking-widest">
              {filtered.length} symbol{filtered.length !== 1 ? 's' : ''}
            </span>
            {isError && (
              <span className="flex items-center gap-1 text-[10px] text-rose-400">
                <AlertCircle size={10} /> Backend offline
              </span>
            )}
          </div>

          {/* List */}
          <div className="flex-1 overflow-y-auto custom-scrollbar p-2 space-y-1.5">
            {isLoading ? (
              // Skeleton
              Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="p-4 border border-white/5 rounded-md space-y-2 animate-pulse">
                  <div className="h-3 bg-white/5 rounded w-24" />
                  <div className="h-8 bg-white/3 rounded" />
                  <div className="h-2 bg-white/3 rounded w-16" />
                </div>
              ))
            ) : isError ? (
              <div className="p-6 text-center space-y-3">
                <AlertCircle size={28} className="text-slate-600 mx-auto" />
                <p className="text-[11px] text-slate-500 uppercase tracking-wide">Backend offline</p>
                <p className="text-[10px] text-slate-600">Start the FastAPI server to load live data</p>
                <button
                  onClick={() => refetch()}
                  className="text-[10px] px-3 py-1.5 rounded border border-white/10 text-slate-400 hover:text-white transition-all"
                >
                  Retry
                </button>
              </div>
            ) : filtered.length === 0 ? (
              <div className="p-6 text-center text-slate-600 text-[11px] uppercase tracking-wide">No results</div>
            ) : (
              filtered.map((stock) => (
                <AssetCard
                  key={stock.symbol}
                  stock={stock}
                  isSelected={selectedSymbol?.symbol === stock.symbol}
                  onClick={() => setSelectedSymbol(stock)}
                />
              ))
            )}
          </div>
        </div>

        {/* ── Detail Panel ── */}
        <main className="flex-1 bg-[#05070a] overflow-hidden">
          {selectedSymbol ? (
            <StockDetailPanel stock={selectedSymbol} />
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-slate-600 space-y-3">
              <TrendingUp size={40} className="opacity-30" />
              <p className="text-[12px] uppercase tracking-widest font-semibold">Select a symbol to view chart</p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default AISignalsPage;
