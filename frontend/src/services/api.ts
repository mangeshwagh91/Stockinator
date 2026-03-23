const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export interface WatchlistSymbol {
  symbol: string;
  yf: string;
  name: string;
  exchange: string;
  segment: string;
}

export interface QuoteData {
  symbol: string;
  yf_symbol: string;
  price: number;
  prev_close: number;
  change: number;
  change_pct: number;
  timestamp: string;
}

export interface Candle {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface ChartData {
  symbol: string;
  yf_symbol: string;
  period: string;
  interval: string;
  count: number;
  candles: Candle[];
}

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`API error ${res.status}: ${res.statusText}`);
  return res.json() as Promise<T>;
}

export const fetchSymbols = () =>
  apiFetch<{ symbols: WatchlistSymbol[] }>('/api/v1/data/symbols').then(r => r.symbols);

export const fetchQuote = (symbol: string) =>
  apiFetch<QuoteData>(`/api/v1/data/quote/${encodeURIComponent(symbol)}`);

export const fetchChart = (symbol: string, period = '1mo', interval = '1d') =>
  apiFetch<ChartData>(`/api/v1/data/chart/${encodeURIComponent(symbol)}?period=${period}&interval=${interval}`);
