import React, { useEffect, useRef, useState } from 'react';
import {
  createChart,
  IChartApi,
  ISeriesApi,
  CandlestickData,
  HistogramData,
  Time,
  CrosshairMode,
  ColorType,
  LineSeries,
  LineData,
} from 'lightweight-charts';
import { Candle } from '@/services/api';

function toTime(ts: string): Time {
  const d = new Date(ts);
  if (isNaN(d.getTime())) return ts.slice(0, 10) as Time;
  return Math.floor(d.getTime() / 1000) as unknown as Time;
}

function candleToLW(c: Candle): CandlestickData {
  return { time: toTime(c.time), open: c.open, high: c.high, low: c.low, close: c.close };
}

function candleToVol(c: Candle, isUp: boolean): HistogramData {
  return {
    time: toTime(c.time),
    value: c.volume,
    color: isUp ? 'rgba(16,185,129,0.45)' : 'rgba(244,63,94,0.45)',
  };
}

interface Tick {
  symbol: string;
  price: number;
  volume: number;
  timestamp: string;
}

interface TVChartProps {
  symbol: string;
  candles: Candle[];
  lastTick: Tick | null;
}

const TVChart: React.FC<TVChartProps> = ({ symbol, candles, lastTick }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const vwapSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  
  // Track the most recent candle data to apply ticks cleanly
  const currentCandleRef = useRef<CandlestickData | null>(null);

  // 1. Initialize Chart
  useEffect(() => {
    if (!containerRef.current) return;
    const el = containerRef.current;

    const chart = createChart(el, {
      width: el.clientWidth,
      height: el.clientHeight || 420,
      layout: {
        background: { type: ColorType.Solid, color: '#05070a' },
        textColor: '#64748b',
        fontFamily: "'IBM Plex Mono', monospace",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: 'rgba(255,255,255,0.04)' },
        horzLines: { color: 'rgba(255,255,255,0.04)' },
      },
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: {
        borderColor: 'rgba(255,255,255,0.06)',
      },
      timeScale: {
        borderColor: 'rgba(255,255,255,0.06)',
        timeVisible: true,
        secondsVisible: true,
      },
    });

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#10b981', downColor: '#f43f5e',
      borderUpColor: '#10b981', borderDownColor: '#f43f5e',
      wickUpColor: '#10b981', wickDownColor: '#f43f5e',
    });

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;

    const ro = new ResizeObserver(() => {
      if (containerRef.current) {
        chart.applyOptions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight || 420,
        });
      }
    });
    ro.observe(containerRef.current);

    return () => {
      ro.disconnect();
      chart.remove();
      chartRef.current = null;
    };
  }, []);

  // 2. Set Initial Historical Data
  useEffect(() => {
    if (!candleSeriesRef.current || !candles.length) return;
    const lwCandles = candles.map(candleToLW);
    candleSeriesRef.current.setData(lwCandles);
    currentCandleRef.current = lwCandles[lwCandles.length - 1];
    
    // Smooth auto-fit
    setTimeout(() => chartRef.current?.timeScale().fitContent(), 50);
  }, [candles]);

  // 3. Process High-Frequency Ticks (Zero-Latency Painting)
  useEffect(() => {
    if (!lastTick || lastTick.symbol !== symbol || !candleSeriesRef.current) return;
    if (!currentCandleRef.current) return;

    // We mutate the last candle visually in true HFT style
    const t = currentCandleRef.current;
    
    // If the tick is significantly newer (e.g., crossing a minute boundary), 
    // we would normally create a new candle. For this zero-latency demo, 
    // we assume it updates the current active period's high/low/close instantly.
    const updatedCandle: CandlestickData = {
        time: t.time,
        open: t.open,
        high: Math.max(t.high, lastTick.price),
        low: Math.min(t.low, lastTick.price),
        close: lastTick.price
    };
    
    // Update chart natively
    candleSeriesRef.current.update(updatedCandle);
    currentCandleRef.current = updatedCandle;

  }, [lastTick, symbol]);

  return (
    <div
      ref={containerRef}
      style={{ width: '100%', height: '100%', position: 'relative' }}
      className="rounded-b-lg overflow-hidden border border-white/5"
    />
  );
};

// Import this locally since lightweight charts exports it uniquely
import { CandlestickSeries } from 'lightweight-charts';

export default TVChart;
