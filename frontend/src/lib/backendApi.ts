const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

import type {
  SystemDecisionRequest,
  SystemDecisionResponse,
  WorkflowSummary,
} from "@/features/dashboard/types";

export interface BackendHealth {
  status: string;
  database: string;
  influxdb: string;
  redis: string;
}

export interface SystemStatus {
  trading_active: boolean;
  paper_trading: boolean;
  threshold: number;
  cooldown_minutes: number;
  risk_metrics: {
    today_pnl?: number;
    open_positions?: number;
    max_open_positions?: number;
    daily_loss_used_pct?: number;
  };
  broker_connected: boolean;
}

export interface PriceTick {
  symbol: string;
  price: number;
  timestamp: string;
}

const fetchJson = async <T>(path: string): Promise<T> => {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return (await response.json()) as T;
};

export const backendApi = {
  getHealth: () => fetchJson<BackendHealth>("/health"),
  getSystemStatus: () => fetchJson<SystemStatus>("/api/v1/control/status"),
  getWorkflowSummary: () => fetchJson<WorkflowSummary>("/api/v1/system/workflow"),
  evaluateDecision: async (payload: SystemDecisionRequest): Promise<SystemDecisionResponse> => {
    const response = await fetch(`${API_BASE}/api/v1/system/decision`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Request failed: ${response.status}`);
    }

    return (await response.json()) as SystemDecisionResponse;
  },
  getPrice: (symbol: string, assetType: "stock" | "crypto" = "stock") =>
    fetchJson<PriceTick>(`/api/v1/data/price/${encodeURIComponent(symbol)}?asset_type=${assetType}`),
};
