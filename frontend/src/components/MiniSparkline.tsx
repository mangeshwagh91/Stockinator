import React from 'react';
import { AreaChart, Area, ResponsiveContainer, Tooltip } from 'recharts';
import { Candle } from '@/services/api';

interface MiniSparklineProps {
  candles: Candle[];
  isPositive: boolean;
  height?: number;
}

const MiniSparkline: React.FC<MiniSparklineProps> = ({ candles, isPositive, height = 40 }) => {
  if (!candles || candles.length === 0) {
    return <div style={{ height }} className="flex items-center justify-center text-slate-600 text-[10px]">NO DATA</div>;
  }

  const data = candles.map((c) => ({ v: c.close }));
  const color = isPositive ? '#10b981' : '#f43f5e';

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 2, right: 0, left: 0, bottom: 2 }}>
        <defs>
          <linearGradient id={`spark-${isPositive ? 'g' : 'r'}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={color} stopOpacity={0.3} />
            <stop offset="95%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <Area
          type="monotone"
          dataKey="v"
          stroke={color}
          strokeWidth={1.5}
          fill={`url(#spark-${isPositive ? 'g' : 'r'})`}
          dot={false}
          isAnimationActive={false}
        />
        <Tooltip
          contentStyle={{ background: '#0a0c10', border: '1px solid rgba(255,255,255,0.05)', borderRadius: 4, fontSize: 10, padding: '2px 6px' }}
          itemStyle={{ color: '#f8fafc' }}
          formatter={(v: number) => [v.toLocaleString('en-IN', { maximumFractionDigits: 2 }), '']}
          labelFormatter={() => ''}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
};

export default MiniSparkline;
