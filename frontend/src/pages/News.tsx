import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Zap, Newspaper, TrendingUp, TrendingDown, Clock,
  RefreshCw, Globe, Search
} from "lucide-react";

const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

interface NewsArticle {
  title: string;
  source: string;
  url?: string;
  publishedAt?: string;
  sentiment?: number;
  symbol?: string;
}

const News = () => {
  const [search, setSearch] = useState("");

  // Fetch news from backend
  const { data: news, refetch, isLoading } = useQuery({
    queryKey: ["news"],
    queryFn: async () => {
      // Try fetching from our backend news endpoint; fallback to empty
      try {
        const res = await fetch(`${BASE}/api/v1/data/news`);
        if (res.ok) return await res.json();
      } catch {}
      // Show demo data if endpoint doesn't exist yet
      return {
        articles: [
          { title: "Nifty 50 rallies 200 points on strong FII buying", source: "Economic Times", sentiment: 78, symbol: "NIFTY50", publishedAt: new Date().toISOString() },
          { title: "RBI keeps repo rate unchanged at 6.5%", source: "Moneycontrol", sentiment: 55, publishedAt: new Date().toISOString() },
          { title: "HDFC Bank Q3 results beat estimates, net profit up 35%", source: "Livemint", sentiment: 85, symbol: "HDFCBANK", publishedAt: new Date().toISOString() },
          { title: "Crude oil surges above $80/barrel on OPEC+ cuts", source: "Reuters", sentiment: 30, publishedAt: new Date().toISOString() },
          { title: "IT sector faces headwinds as US tech spending slows", source: "Business Standard", sentiment: 28, symbol: "TCS", publishedAt: new Date().toISOString() },
          { title: "Adani Group stocks surge 5% after Supreme Court verdict", source: "NDTV Profit", sentiment: 72, symbol: "ADANIENT", publishedAt: new Date().toISOString() },
          { title: "Reliance Jio announces new 5G plans, stock gains", source: "Economic Times", sentiment: 68, symbol: "RELIANCE", publishedAt: new Date().toISOString() },
          { title: "Auto sales data: Maruti leads, Tata Motors gains market share", source: "CNBC-TV18", sentiment: 65, symbol: "MARUTI", publishedAt: new Date().toISOString() },
          { title: "Pharma sector outlook positive on drug approvals", source: "Moneycontrol", sentiment: 62, symbol: "SUNPHARMA", publishedAt: new Date().toISOString() },
          { title: "Banking sector under pressure as NPA concerns rise", source: "Business Standard", sentiment: 32, symbol: "BANKNIFTY", publishedAt: new Date().toISOString() },
        ],
      };
    },
    refetchInterval: 30000,
  });

  const articles: NewsArticle[] = news?.articles || [];
  const filtered = articles.filter(
    (a) =>
      !search || a.title.toLowerCase().includes(search.toLowerCase()) ||
      a.symbol?.toLowerCase().includes(search.toLowerCase())
  );

  const getSentimentColor = (s: number) =>
    s >= 60 ? "text-emerald-400" : s <= 40 ? "text-rose-400" : "text-amber-400";
  const getSentimentLabel = (s: number) =>
    s >= 70 ? "BULLISH" : s >= 55 ? "POSITIVE" : s <= 30 ? "BEARISH" : s <= 45 ? "NEGATIVE" : "NEUTRAL";

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
          ].map((l) => (
            <a key={l.href} href={l.href}
              className={`px-3 py-1.5 rounded text-[11px] font-bold uppercase tracking-widest ${
                l.href === "/news" ? "bg-white/5 text-white" : "text-slate-500 hover:text-white"
              }`}>
              {l.label}
            </a>
          ))}
        </nav>
      </header>

      <div className="p-6 max-w-[1200px] mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-black tracking-tight flex items-center gap-2">
              <Newspaper size={22} className="text-cyan-400" /> Market News Feed
            </h2>
            <p className="text-sm text-slate-500 mt-1">Real-time news with AI sentiment analysis</p>
          </div>
          <button onClick={() => refetch()}
            className="flex items-center gap-1 px-3 py-1.5 rounded bg-white/5 text-[10px] font-bold uppercase tracking-widest text-slate-400 hover:text-white">
            <RefreshCw size={12} /> Refresh
          </button>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600" size={14} />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search news by keyword or symbol..."
            className="w-full pl-9 pr-4 py-2.5 bg-[#0a0c10] border border-white/5 rounded-lg text-[12px] text-white placeholder-slate-600 focus:outline-none focus:border-white/10"
          />
        </div>

        {/* Sentiment Overview */}
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: "Bullish", count: filtered.filter((a) => (a.sentiment ?? 50) >= 60).length, color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/20" },
            { label: "Neutral", count: filtered.filter((a) => (a.sentiment ?? 50) > 40 && (a.sentiment ?? 50) < 60).length, color: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/20" },
            { label: "Bearish", count: filtered.filter((a) => (a.sentiment ?? 50) <= 40).length, color: "text-rose-400", bg: "bg-rose-500/10", border: "border-rose-500/20" },
          ].map((s) => (
            <div key={s.label} className={`${s.bg} border ${s.border} rounded-lg p-4 flex items-center justify-between`}>
              <div>
                <div className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">{s.label}</div>
                <div className={`text-xl font-black italic mt-1 ${s.color}`}>{s.count}</div>
              </div>
              {s.label === "Bullish" ? <TrendingUp size={20} className={s.color} /> :
               s.label === "Bearish" ? <TrendingDown size={20} className={s.color} /> :
               <Globe size={20} className={s.color} />}
            </div>
          ))}
        </div>

        {/* Articles */}
        <div className="space-y-2">
          {filtered.map((article, i) => (
            <div key={i} className="bg-[#0a0c10] border border-white/5 rounded-lg p-4 hover:border-white/10 transition-colors group">
              <div className="flex justify-between items-start gap-4">
                <div className="flex-1">
                  <h3 className="text-[13px] font-bold text-slate-200 group-hover:text-white leading-snug">
                    {article.title}
                  </h3>
                  <div className="flex items-center gap-3 mt-2 text-[10px] text-slate-500">
                    <span>{article.source}</span>
                    {article.symbol && (
                      <span className="px-1.5 py-0.5 bg-white/5 rounded text-[9px] font-bold text-slate-400">
                        {article.symbol}
                      </span>
                    )}
                    {article.publishedAt && (
                      <span className="flex items-center gap-1">
                        <Clock size={10} />
                        {new Date(article.publishedAt).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}
                      </span>
                    )}
                  </div>
                </div>
                {article.sentiment !== undefined && (
                  <div className="flex flex-col items-end flex-shrink-0">
                    <div className={`text-lg font-black italic ${getSentimentColor(article.sentiment)}`}>
                      {article.sentiment}
                    </div>
                    <div className={`text-[9px] font-bold ${getSentimentColor(article.sentiment)}`}>
                      {getSentimentLabel(article.sentiment)}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default News;
