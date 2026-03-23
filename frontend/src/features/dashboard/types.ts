export interface WorkflowSummary {
  motive: string;
  cycle: string[];
  agents: string[];
  timestamp: string;
}

export interface SystemDecisionRequest {
  symbol: string;
  last_price: number;
  bullish_patterns: number;
  bearish_patterns: number;
  xgboost_probability: number;
  news_sentiment: number;
  expected_profit: number;
  cost_estimate: number;
  daily_pnl: number;
  open_positions: number;
  cooldown_elapsed: boolean;
  position_size_within_limits: boolean;
}

export interface SystemDecisionResponse {
  snapshot: {
    symbol: string;
    price: number;
    sentiment: number;
    timestamp: string;
  };
  indicator_consensus: {
    score: number;
    bullish_patterns: number;
    bearish_patterns: number;
  };
  prediction: {
    success_score: number;
    confidence_low: number;
    confidence_high: number;
  };
  risk: {
    halted: boolean;
    max_loss_used: number;
    open_positions: number;
    max_open_positions: number;
  };
  decision: {
    action: string;
    reason: string;
  };
}
