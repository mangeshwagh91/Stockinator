import React, { useState } from "react";
import { Link } from "react-router-dom";
import { 
  Globe2, 
  BarChart3, 
  Zap, 
  ArrowUpRight, 
  Wifi,
  Lock,
  Briefcase,
  Map as GeoMap,
  X,
  Clock
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import GlobeScene from "./GlobeScene";

const GeotradeDashboard = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-black text-[#f8fafc] overflow-hidden font-inter selection:bg-blue-500/30 selection:text-white flex border-4 border-[#1e293b]/20">
      
      {/* 5. Star Background: Multi-layered for depth andparallax-like movement */}
      <div className="fixed inset-0 pointer-events-none bg-[#010101]" style={{ zIndex: -2 }}>
        {/* Layer 1: Small, dense, slow background stars */}
        {[...Array(300)].map((_, i) => (
          <div
            key={`s1-${i}`}
            className="absolute rounded-full bg-white animate-star-slow" 
            style={{
              top: `${Math.random() * 100}%`,
              left: `${Math.random() * 100}%`,
              width: '1px',
              height: '1px',
              opacity: Math.random() * 0.4 + 0.1,
              animationDuration: `${Math.random() * 80 + 100}s`,
              animationDelay: `${Math.random() * -100}s`
            }}
          />
        ))}
        {/* Layer 2: Larger, faster foreground stars */}
        {[...Array(100)].map((_, i) => (
          <div
            key={`s2-${i}`}
            className="absolute rounded-full bg-white opacity-40 animate-star-fast" 
            style={{
              top: `${Math.random() * 100}%`,
              left: `${Math.random() * 100}%`,
              width: `${Math.random() * 1.5 + 1}px`,
              height: `${Math.random() * 1.5 + 1}px`,
              animationDuration: `${Math.random() * 40 + 60}s`,
              animationDelay: `${Math.random() * -60}s`
            }}
          />
        ))}
        <style dangerouslySetInnerHTML={{ __html: `
          @keyframes star-flow-bg {
            0% { transform: translateY(0) translateX(0); opacity: 0; }
            10% { opacity: 0.3; }
            90% { opacity: 0.3; }
            100% { transform: translateY(-200px) translateX(-50px); opacity: 0; }
          }
          @keyframes star-flow-fg {
            0% { transform: translateY(0) translateX(0); opacity: 0; }
            5% { opacity: 0.6; }
            95% { opacity: 0.6; }
            100% { transform: translateY(-400px) translateX(-100px); opacity: 0; }
          }
          .animate-star-slow {
            animation: star-flow-bg linear infinite;
          }
          .animate-star-fast {
            animation: star-flow-fg linear infinite;
          }
        `}} />
      </div>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col relative w-full overflow-hidden">
        
        {/* Header - Unified with AI Signals navbar */}
        <header className="h-14 border-b border-white/5 bg-[#0a0c10] flex items-center justify-between px-4 sticky top-0 z-50">
          <div className="flex items-center gap-12">
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
                  <ArrowUpRight size={12} /> +2.1
                </span>
                <div className="px-1.5 py-0.5 rounded bg-orange-500/10 text-[10px] font-bold text-orange-400 tracking-tight uppercase border border-orange-500/20 ml-1">
                  ELEVATED
                </div>
              </div>
            </div>
          </div>

          <div className="hidden lg:flex items-center gap-0.5 p-0.5 rounded-lg bg-black/40 border border-white/5 shadow-inner">
            <Link to="/" className="px-4 py-1.5 rounded-md text-[11px] font-bold tracking-wide bg-[#1a1f26] text-white border border-white/10 shadow-lg uppercase flex items-center gap-2">
              <Globe2 size={12} className="text-blue-400" /> EARTH PULSE
            </Link>
            <button className="px-4 py-1.5 rounded-md text-[11px] font-semibold tracking-wide text-slate-400 hover:text-white transition-all uppercase flex items-center gap-2">
              <GeoMap size={12} /> GEO MAP
            </button>
            <Link to="/signals" className="px-5 py-1.5 rounded-md text-[11px] font-semibold tracking-wide text-slate-400 hover:text-white transition-all uppercase flex items-center gap-2">
              <BarChart3 size={12} /> AI SIGNALS
            </Link>
            <button className="px-4 py-1.5 rounded-md text-[11px] font-semibold tracking-wide text-slate-400 hover:text-white transition-all uppercase flex items-center gap-2">
              <Briefcase size={12} /> PORTFOLIO
            </button>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/5 border border-emerald-500/10">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[11px] font-semibold text-emerald-500 tracking-wide uppercase">LIVE - 2 feeds</span>
            </div>
            <div className="hidden md:flex items-center gap-2 text-slate-500 border-l border-white/10 pl-4 h-6">
              <Clock size={12} />
              <span className="text-[11px] font-mono font-semibold tracking-wide">05:59:24 UTC</span>
            </div>
            <button onClick={() => setMobileMenuOpen(true)} className="lg:hidden text-slate-300 hover:text-white transition-colors" aria-label="Open menu">
              <Zap size={16} />
            </button>
          </div>
        </header>

        <section className="flex-1 relative flex flex-col overflow-hidden bg-[#010101]">
          {/* Dashboard UI Overlay (Globe Index and Stability) - Simplified per request */}
          <div className="absolute left-8 top-8 z-30 pointer-events-none">
            <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}>
              <h2 className="text-xs font-semibold tracking-[0.22em] text-[#64748b] mb-2">GLOBAL TRADE INDEX</h2>
              <div className="flex items-baseline gap-4">
                <h1 className="text-5xl font-bold tracking-tight text-white">8,422.31</h1>
                <span className="text-emerald-500 text-sm font-bold flex items-center gap-1 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">
                  <ArrowUpRight size={14} /> +2.4%
                </span>
              </div>
            </motion.div>
          </div>

          <div className="absolute left-8 bottom-8 z-30 pointer-events-none w-[320px]">
            <div className="bg-black/40 backdrop-blur-xl border-t-white/20 border-x-white/10 border-b-white/5 p-5 rounded-2xl border border-white/10 pointer-events-auto">
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-semibold tracking-[0.18em] text-[#64748b]">INDEX STABILITY</span>
                <span className="text-xs font-semibold text-emerald-500">OPTIMAL</span>
              </div>
              <div className="h-2 w-full bg-[#1e293b]/30 rounded-full overflow-hidden mb-6 border border-white/5">
                <motion.div initial={{ width: 0 }} animate={{ width: "88%" }} className="h-full bg-gradient-to-r from-blue-600 to-emerald-500" />
              </div>
              <div className="grid grid-cols-2 gap-8">
                <div>
                  <div className="text-[11px] font-semibold tracking-[0.08em] text-[#475569] mb-2 uppercase">VOLATILITY</div>
                  <div className="text-sm font-bold text-slate-200 tracking-tight">0.124 VIX</div>
                </div>
                <div>
                  <div className="text-[11px] font-semibold tracking-[0.08em] text-[#475569] mb-2 uppercase">LIQUIDITY</div>
                  <div className="text-sm font-bold text-slate-200 tracking-tight">HIGH (AA+)</div>
                </div>
              </div>
            </div>
          </div>

          {/* Full-width Globe Area */}
          <div className="flex-1 relative bg-transparent flex items-center justify-center p-0 m-0 w-full h-full">
             <div className="w-[80vw] h-[80vh] absolute bg-blue-500/5 rounded-full blur-[200px] -z-10 animate-pulse" />
             <div className="w-full h-full relative z-20">
               <GlobeScene />
             </div>
          </div>
        </section>

        {/* Cinematic Footer */}
        <footer className="h-10 border-t border-white/5 bg-black/40 backdrop-blur-xl flex items-center justify-between px-8 z-40 text-[11px] font-semibold text-[#475569] tracking-[0.14em]">
          <div className="flex gap-8">
            <span className="flex items-center gap-1.5"><Wifi size={10} className="text-emerald-500" /> STATUS: OPERATIONAL</span>
            <span className="flex items-center gap-1.5"><Lock size={10} /> ENCRYPTION: AES-256-GCM</span>
          </div>
          <div className="flex items-center gap-6">
            <span className="text-blue-500/80">LATENCY: 12ms</span>
            <span className="text-white/20">COORD: 40.7128 N, 74.0060 W</span>
          </div>
        </footer>
      </main>

      {/* Mobile Menu Overlay */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div 
            initial={{ opacity: 0, x: -100 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -100 }}
            className="fixed inset-0 z-[100] bg-black/35 backdrop-blur-xl lg:hidden p-8"
          >
            <div className="flex justify-between items-center mb-12">
              <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                <Zap className="text-white" size={20} />
              </div>
              <button onClick={() => setMobileMenuOpen(false)} className="text-slate-400"><X size={32}/></button>
            </div>
            <div className="flex flex-col gap-8">
              {['OVERVIEW', 'MARKETS', 'ANALYTICS', 'AI OPS', 'ASSETS'].map((t) => (
                <a key={t} className="text-2xl font-black tracking-tighter hover:text-blue-500 transition-colors">{t}</a>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default GeotradeDashboard;