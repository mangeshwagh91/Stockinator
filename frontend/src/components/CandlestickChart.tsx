import React from 'react';
import {
  ComposedChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
  Line,
} from 'recharts';
import { Candle } from '@/services/api';

interface CandlestickChartProps {
  candles: Candle[];
  height?: number;
}

interface CandleBar {
  time: string;
  open: number;
  close: number;
  high: number;
  low: number;
  volume: number;
  isUp: boolean;
  // For custom bar shape: we use [low, high] as range and color each bar separately.
  // The Recharts Bar will show bodyLow–bodyHigh (open/close) and we overlay high-low as error.
  bodyLow: number;
  bodyHigh: number;
  wickLow: number;
  wickHigh: number;
  color: string;
}

// Custom candlestick bar using SVG
const CandlestickBar = (props: any) => {
  const { x, y, width, height, payload, yAxis } = props;
  if (!payload || !yAxis) return null;
  const { isUp, high, low, open, close } = payload;

  const upColor = '#10b981';
  const downColor = '#f43f5e';
  const color = isUp ? upColor : downColor;

  // Convert price values to pixel positions
  const toY = (price: number) => {
    const domain = yAxis.scale.domain();
    const range = yAxis.scale.range();
    const minP = domain[0], maxP = domain[1];
    const minY = range[1], maxY = range[0];
    return minY + ((price - minP) / (maxP - minP)) * (maxY - minY);
  };

  const bodyTop = toY(Math.max(open, close));
  const bodyBottom = toY(Math.min(open, close));
  const wickTop = toY(high);
  const wickBottom = toY(low);
  const cx = x + width / 2;
  const bodyHeight = Math.max(1, bodyBottom - bodyTop);

  return (
    <g>
      {/* Wick */}
      <line x1={cx} y1={wickTop} x2={cx} y2={wickBottom} stroke={color} strokeWidth={1} opacity={0.8} />
      {/* Body */}
      <rect
        x={x + 1}
        y={bodyTop}
        width={Math.max(1, width - 2)}
        height={bodyHeight}
        fill={isUp ? 'transparent' : color}
        stroke={color}
        strokeWidth={1}
        fillOpacity={isUp ? 0 : 0.85}
      />
    </g>
  );
};

// Custom tooltip
const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload || !payload.length) return null;
  const d = payload[0]?.payload;
  if (!d) return null;
  const fmt = (n: number) => n.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  return (
    <div className="bg-[#0a0c10] border border-white/5 rounded px-3 py-2 text-[11px] font-mono text-slate-300 space-y-0.5 shadow-xl">
      <div className="text-slate-500 mb-1">{d.time?.slice(0, 10)}</div>
      <div className="flex gap-3">
        <span className="text-slate-500">O</span><span>{fmt(d.open)}</span>
        <span className="text-slate-500">H</span><span className="text-emerald-400">{fmt(d.high)}</span>
      </div>
      <div className="flex gap-3">
        <span className="text-slate-500">L</span><span className="text-rose-400">{fmt(d.low)}</span>
        <span className="text-slate-500">C</span><span className={d.isUp ? 'text-emerald-400' : 'text-rose-400'}>{fmt(d.close)}</span>
      </div>
      <div className="text-slate-500 text-[10px] mt-1">Vol: {(d.volume / 1_000_000).toFixed(2)}M</div>
    </div>
  );
};

const CandlestickChart: React.FC<CandlestickChartProps> = ({ candles, height = 320 }) => {
  if (!candles || candles.length === 0) {
    return (
      <div className="flex items-center justify-center text-slate-600 text-[12px] font-semibold uppercase tracking-widest" style={{ height }}>
        No chart data
      </div>
    );
  }

  const data: CandleBar[] = candles.map((c) => ({
    ...c,
    isUp: c.close >= c.open,
    bodyLow: Math.min(c.open, c.close),
    bodyHigh: Math.max(c.open, c.close),
    wickLow: c.low,
    wickHigh: c.high,
    color: c.close >= c.open ? '#10b981' : '#f43f5e',
  }));

  const prices = data.flatMap((d) => [d.low, d.high]);
  const minP = Math.min(...prices);
  const maxP = Math.max(...prices);
  const padding = (maxP - minP) * 0.05;

  const maxVol = Math.max(...data.map((d) => d.volume));

  // X-axis tick: show every Nth label to avoid crowding
  const labelStep = Math.max(1, Math.floor(data.length / 8));

  const fmt = (n: number) =>
    n >= 1000 ? n.toLocaleString('en-IN', { maximumFractionDigits: 0 }) : n.toFixed(2);

  return (
    <div style={{ height }}>
      {/* Price chart */}
      <ResponsiveContainer width="100%" height="78%">
        <ComposedChart data={data} margin={{ top: 8, right: 8, left: 4, bottom: 0 }} barCategoryGap="20%">
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
          <XAxis
            dataKey="time"
            tickFormatter={(v, i) => (i % labelStep === 0 ? String(v).slice(5, 10) : '')}
            tick={{ fill: '#64748b', fontSize: 10, fontFamily: 'monospace' }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            domain={[minP - padding, maxP + padding]}
            tickFormatter={fmt}
            tick={{ fill: '#64748b', fontSize: 10, fontFamily: 'monospace' }}
            axisLine={false}
            tickLine={false}
            width={60}
            orientation="right"
          />
          <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'rgba(255,255,255,0.08)', strokeWidth: 1 }} />
          <Bar dataKey="close" shape={<CandlestickBar />} isAnimationActive={false}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </ComposedChart>
      </ResponsiveContainer>

      {/* Volume bars */}
      <ResponsiveContainer width="100%" height="22%">
        <ComposedChart data={data} margin={{ top: 0, right: 8, left: 4, bottom: 4 }} barCategoryGap="20%">
          <XAxis dataKey="time" hide />
          <YAxis tickFormatter={(v) => `${(v / 1_000_000).toFixed(0)}M`} tick={{ fill: '#475569', fontSize: 9, fontFamily: 'monospace' }} axisLine={false} tickLine={false} width={60} orientation="right" />
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
          <Bar dataKey="volume" isAnimationActive={false} radius={[2, 2, 0, 0]}>
            {data.map((entry, index) => (
              <Cell key={`vol-${index}`} fill={entry.isUp ? 'rgba(16,185,129,0.4)' : 'rgba(244,63,94,0.4)'} />
            ))}
          </Bar>
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

export default CandlestickChart;
