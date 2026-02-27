// Mock data for the trading dashboard

export interface SymbolData {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  score: number;
  signal: "STRONG_BUY" | "BUY" | "NEUTRAL" | "SELL" | "STRONG_SELL";
  volume: string;
}

export interface Indicator {
  name: string;
  value: number;
  signal: "bullish" | "bearish" | "neutral";
  category: "trend" | "momentum" | "volatility" | "volume";
}

export interface NewsItem {
  id: string;
  headline: string;
  source: string;
  time: string;
  sentiment: number; // -10 to +10
  impact: "low" | "medium" | "high";
  relevantSymbols: string[];
  eventType: string;
}

export interface Position {
  symbol: string;
  side: "LONG" | "SHORT";
  entryPrice: number;
  currentPrice: number;
  quantity: number;
  pnl: number;
  pnlPercent: number;
  stopLoss: number;
  takeProfit: number;
}

export interface Trade {
  id: string;
  symbol: string;
  side: "BUY" | "SELL";
  price: number;
  quantity: number;
  pnl: number;
  cost: number;
  time: string;
  score: number;
}

export const watchlist: SymbolData[] = [
  { symbol: "RELIANCE", name: "Reliance Industries", price: 2847.50, change: 32.15, changePercent: 1.14, score: 87, signal: "STRONG_BUY", volume: "12.4M" },
  { symbol: "TCS", name: "Tata Consultancy", price: 3956.20, change: -18.40, changePercent: -0.46, score: 42, signal: "SELL", volume: "5.2M" },
  { symbol: "INFY", name: "Infosys Ltd", price: 1623.80, change: 8.90, changePercent: 0.55, score: 71, signal: "BUY", volume: "8.7M" },
  { symbol: "HDFCBANK", name: "HDFC Bank", price: 1712.35, change: -5.20, changePercent: -0.30, score: 55, signal: "NEUTRAL", volume: "15.1M" },
  { symbol: "BTC/USD", name: "Bitcoin", price: 67432.18, change: 1243.50, changePercent: 1.88, score: 92, signal: "STRONG_BUY", volume: "32.1B" },
  { symbol: "ETH/USD", name: "Ethereum", price: 3521.44, change: -42.30, changePercent: -1.19, score: 38, signal: "SELL", volume: "14.8B" },
];

export const indicators: Indicator[] = [
  { name: "RSI (14)", value: 68.4, signal: "bullish", category: "momentum" },
  { name: "MACD", value: 12.3, signal: "bullish", category: "trend" },
  { name: "SMA (50)", value: 2810.0, signal: "bullish", category: "trend" },
  { name: "EMA (20)", value: 2835.2, signal: "bullish", category: "trend" },
  { name: "ADX", value: 28.7, signal: "bullish", category: "trend" },
  { name: "Stochastic", value: 72.1, signal: "neutral", category: "momentum" },
  { name: "CCI", value: 145.2, signal: "bearish", category: "momentum" },
  { name: "Bollinger", value: 2.1, signal: "neutral", category: "volatility" },
  { name: "ATR", value: 45.3, signal: "neutral", category: "volatility" },
  { name: "OBV", value: 1.24, signal: "bullish", category: "volume" },
];

export const newsItems: NewsItem[] = [
  { id: "1", headline: "RBI holds repo rate steady at 6.5%, signals accommodative stance", source: "Reuters", time: "2m ago", sentiment: 6, impact: "high", relevantSymbols: ["HDFCBANK", "RELIANCE"], eventType: "Policy" },
  { id: "2", headline: "Reliance Jio announces 5G expansion to 200 new cities", source: "Moneycontrol", time: "15m ago", sentiment: 8, impact: "high", relevantSymbols: ["RELIANCE"], eventType: "Expansion" },
  { id: "3", headline: "Bitcoin ETF sees record inflows of $1.2B in single day", source: "Bloomberg", time: "28m ago", sentiment: 9, impact: "high", relevantSymbols: ["BTC/USD", "ETH/USD"], eventType: "Market Flow" },
  { id: "4", headline: "TCS warns of slower growth in European banking sector", source: "Economic Times", time: "45m ago", sentiment: -5, impact: "medium", relevantSymbols: ["TCS", "INFY"], eventType: "Earnings" },
  { id: "5", headline: "Global semiconductor shortage expected to ease by Q3", source: "CNBC", time: "1h ago", sentiment: 4, impact: "medium", relevantSymbols: ["INFY", "TCS"], eventType: "Industry" },
  { id: "6", headline: "Ethereum faces regulatory scrutiny from SEC", source: "CoinDesk", time: "1h ago", sentiment: -7, impact: "high", relevantSymbols: ["ETH/USD"], eventType: "Regulation" },
];

export const openPositions: Position[] = [
  { symbol: "RELIANCE", side: "LONG", entryPrice: 2815.00, currentPrice: 2847.50, quantity: 50, pnl: 1625.00, pnlPercent: 1.15, stopLoss: 2787.00, takeProfit: 2920.00 },
  { symbol: "BTC/USD", side: "LONG", entryPrice: 66200.00, currentPrice: 67432.18, quantity: 0.5, pnl: 616.09, pnlPercent: 1.86, stopLoss: 65500.00, takeProfit: 70000.00 },
  { symbol: "ETH/USD", side: "SHORT", entryPrice: 3580.00, currentPrice: 3521.44, quantity: 5, pnl: 292.80, pnlPercent: 1.64, stopLoss: 3650.00, takeProfit: 3400.00 },
];

export const recentTrades: Trade[] = [
  { id: "T001", symbol: "RELIANCE", side: "BUY", price: 2815.00, quantity: 50, pnl: 0, cost: 50, time: "09:32 AM", score: 85 },
  { id: "T002", symbol: "BTC/USD", side: "BUY", price: 66200.00, quantity: 0.5, pnl: 0, cost: 50, time: "08:15 AM", score: 91 },
  { id: "T003", symbol: "INFY", side: "SELL", price: 1640.00, quantity: 100, pnl: 1250, cost: 50, time: "Yesterday", score: 78 },
  { id: "T004", symbol: "TCS", side: "SELL", price: 3980.00, quantity: 30, pnl: -420, cost: 50, time: "Yesterday", score: 45 },
  { id: "T005", symbol: "ETH/USD", side: "SELL", price: 3580.00, quantity: 5, pnl: 0, cost: 50, time: "10:05 AM", score: 82 },
];

export const equityCurve = Array.from({ length: 30 }, (_, i) => ({
  day: `Day ${i + 1}`,
  equity: 1000000 + Math.floor(Math.random() * 50000 - 10000) * (1 + i * 0.02) + i * 3000,
  benchmark: 1000000 + i * 1500 + Math.floor(Math.random() * 10000 - 5000),
}));

export const scoreHistory = Array.from({ length: 24 }, (_, i) => ({
  time: `${String(i).padStart(2, "0")}:00`,
  RELIANCE: Math.floor(50 + Math.random() * 45),
  "BTC/USD": Math.floor(40 + Math.random() * 55),
  TCS: Math.floor(30 + Math.random() * 40),
}));

export const riskMetrics = {
  dailyPnL: 2533.89,
  dailyPnLPercent: 0.25,
  maxDailyLoss: -20000,
  currentDailyLoss: -420,
  maxPositions: 5,
  currentPositions: 3,
  capitalUsed: 342150,
  totalCapital: 1000000,
  brokeragePaid: 250,
  tradesCount: 5,
};
