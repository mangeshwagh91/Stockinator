import React, { useState, useEffect } from 'react';
import { ChevronUp, ChevronDown, Activity } from 'lucide-react';
import { WatchlistSymbol, fetchChart, Candle } from '@/services/api';
import { useQuote } from '@/hooks/useQuote';
import TVChart from './TVChart';

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
const WS_BASE = BASE.replace(/^http/, 'ws');

interface StockDetailPanelProps {
  stock: WatchlistSymbol;
}

const StockDetailPanel: React.FC<StockDetailPanelProps> = ({ stock }) => {
  const { data: quote } = useQuote(stock.symbol);
  
  const [cycleResult, setCycleResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [chartLoading, setChartLoading] = useState(true);
  
  // High-frequency chart states
  const [candles, setCandles] = useState<Candle[]>([]);
  const [lastTick, setLastTick] = useState<any>(null);

  const [timeframe, setTimeframe] = useState('1D');

  const getTimeframeArgs = (tf: string): [string, string] => {
    switch (tf) {
      case '1m': return ['5d', '1m'];
      case '5m': return ['1mo', '5m'];
      case '15m': return ['1mo', '15m'];
      case '1H': return ['1mo', '60m'];
      case '1D': return ['1y', '1d'];
      case '1W': return ['5y', '1wk'];
      case '1M': return ['max', '1mo'];
      default: return ['1y', '1d'];
    }
  };

  // 1. Chart Data Fetch (Re-runs on symbol or timeframe change)
  useEffect(() => {
    let cancelled = false;
    setChartLoading(true);

    const [period, interval] = getTimeframeArgs(timeframe);

    fetchChart(stock.symbol, period, interval).then(d => {
      if (!cancelled) {
        setCandles(d.candles);
        setChartLoading(false);
      }
    }).catch(() => {
      if (!cancelled) setChartLoading(false);
    });

    return () => { cancelled = true; };
  }, [stock.symbol, timeframe]);

  // 2. Initial ML Cycle Fetch (Only runs on fresh symbol click, decoupled from chart)
  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    // Backend is now async, so this won't block the chart fetch!
    fetch(`${BASE}/api/v1/system/run-cycle/${stock.symbol}`, { method: 'POST' })
      .then(res => res.json())
      .then(data => {
        if (!cancelled) {
          setCycleResult(data);
          setLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) setLoading(false);
      });
      
    return () => { cancelled = true; };
  }, [stock.symbol]);

  // 2. Zero-Latency WebSocket Connection
  useEffect(() => {
    // We connect to the live streaming endpoint
    const ws = new WebSocket(`${WS_BASE}/api/v1/ws/live`);
    
    ws.onopen = () => {
      // Subscribe to this specific symbol
      ws.send(JSON.stringify({ type: 'subscribe', symbols: [stock.symbol.split('.')[0]] }));
    };
    
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'tick') {
           // We only care about ticks for the currently viewing symbol
           // The backend sends clean symbols like RELIANCE, so we compare without .NS
           const cleanStockSymbol = stock.symbol.split('.')[0];
           if (msg.symbol === cleanStockSymbol || msg.symbol === stock.symbol) {
              setLastTick(msg);
           }
        }
      } catch (err) {
        console.error("WS Parse error", err);
      }
    };

    return () => {
      ws.close();
    };
  }, [stock.symbol]);

  const isUp = (quote?.change ?? 0) >= 0;
  const fmtPrice = (p: number) =>
    p?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  return (
    <div className="flex flex-col h-full overflow-hidden bg-[#05070a]">

      {/* ── Top Info Bar ──────────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-white/5 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-black text-white italic tracking-tighter">{stock.symbol}</span>
              <span className={`text-[9px] font-black px-1.5 py-0.5 rounded uppercase border ${
                isUp ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                     : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
              }`}>{isUp ? 'BULL' : 'BEAR'}</span>
            </div>
            <div className="text-[10px] text-slate-500">{stock.name} · {stock.exchange}</div>
          </div>
          {quote && (
            <div className="border-l border-white/10 pl-3 ml-1">
              {/* Show the absolute live tick price if available, else fallback to quote */}
              <div className="text-lg font-black text-white italic">
                 {lastTick ? fmtPrice(lastTick.price) : fmtPrice(quote.price)}
              </div>
              <div className={`text-[11px] font-bold flex items-center gap-0.5 ${isUp ? 'text-emerald-400' : 'text-rose-400'}`}>
                {isUp ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
                {isUp ? '+' : ''}{fmtPrice(quote.change)} ({isUp ? '+' : ''}{quote.change_pct.toFixed(2)}%)
              </div>
            </div>
          )}
        </div>
        
        {/* Connection Blinker */}
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-500/5 border border-blue-500/10">
          <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
          <span className="text-[9px] font-bold text-blue-500 tracking-wider">HFT STREAM</span>
        </div>
      </div>

      {/* ── Timeframe Selector ────────────────────────────────────────── */}
      <div className="flex items-center gap-1 px-4 py-1.5 border-b border-white/5 bg-[#080a0e] flex-shrink-0">
        {['1m', '5m', '15m', '1H', '1D', '1W', '1M'].map(tf => (
          <button
            key={tf}
            onClick={() => setTimeframe(tf)}
            className={`px-2.5 py-1 rounded text-[11px] font-bold tracking-wide transition-colors ${
              timeframe === tf
                ? 'bg-blue-500 text-white'
                : 'text-slate-500 hover:text-slate-300 hover:bg-white/5'
            }`}
          >
            {tf}
          </button>
        ))}
      </div>

      {/* ── Chart Area (Lightweight Charts + Websocket Ticks) ──────────── */}
      <div className="flex-1 min-h-0 relative">
        {chartLoading ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-500">
               <Activity className="animate-spin mb-2" size={20} />
               <span className="text-[10px] uppercase tracking-widest font-bold">Connecting zero-latency stream...</span>
            </div>
        ) : (
            <TVChart key={stock.symbol} symbol={stock.symbol} candles={candles} lastTick={lastTick} />
        )}
      </div>

      {/* ── AI Signals Indicators Row ──────────────────────────────────── */}
      <div className="flex-shrink-0 border-t border-white/5 grid grid-cols-4 divide-x divide-white/5">
        <div className="px-4 py-2.5">
          <div className="text-[9px] font-black text-slate-600 uppercase tracking-widest mb-1">AI Success Score</div>
          {loading ? (
             <div className="text-xs text-slate-500 animate-pulse">Computing...</div>
          ) : (
            <div className="flex items-end gap-2">
              <span className={`text-xl font-black italic ${
                (cycleResult?.success_score ?? 0) >= 70 ? 'text-emerald-400' : 
                (cycleResult?.success_score ?? 0) >= 40 ? 'text-amber-400' : 'text-rose-400'
              }`}>{cycleResult?.success_score?.toFixed(1) ?? '—'}</span>
              <span className="text-[9px] text-slate-500 font-bold mb-0.5">{cycleResult?.action || 'HOLD'}</span>
            </div>
          )}
        </div>

        <div className="px-4 py-2.5">
          <div className="text-[9px] font-black text-slate-600 uppercase tracking-widest mb-1">ML / Algo Score</div>
          <div className="text-[11px] font-bold text-blue-400">ML: {cycleResult?.ml_score?.toFixed(1) ?? '—'}</div>
          <div className="text-[11px] font-bold text-purple-400">Algo: {cycleResult?.algo_score?.toFixed(1) ?? '—'}</div>
        </div>

        <div className="px-4 py-2.5">
          <div className="text-[9px] font-black text-slate-600 uppercase tracking-widest mb-1">News Sentiment</div>
          <div className={`text-base font-black italic ${
            (cycleResult?.news_sentiment ?? 50) > 60 ? 'text-emerald-400' : 
            (cycleResult?.news_sentiment ?? 50) < 40 ? 'text-rose-400' : 'text-amber-400'
          }`}>{cycleResult?.news_sentiment?.toFixed(0) ?? '—'}</div>
        </div>

        <div className="px-4 py-2.5">
          <div className="text-[9px] font-black text-slate-600 uppercase tracking-widest mb-1">Detected Patterns</div>
          <div className="text-[10px] text-slate-400 leading-snug">
             {loading ? 'Scanning...' : (cycleResult?.patterns?.length ? cycleResult.patterns.join(', ') : 'None')}
          </div>
        </div>
      </div>

    </div>
  );
};

export default StockDetailPanel;
