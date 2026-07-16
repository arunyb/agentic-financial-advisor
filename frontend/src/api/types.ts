export type RiskTolerance = "conservative" | "moderate" | "aggressive";

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

export interface RiskProfile {
  tolerance: RiskTolerance;
  time_horizon_years: number;
  monthly_investment_capacity: number;
  questionnaire_score: number;
  updated_at: string;
}

export interface Holding {
  id: string;
  ticker: string;
  asset_class: string;
  quantity: number;
  avg_cost: number;
  current_price: number;
}

export interface Portfolio {
  id: string;
  name: string;
  created_at: string;
  holdings: Holding[];
}

export interface AgentStep {
  agent: string;
  summary: string;
  detail?: Record<string, unknown>;
}

export interface ChatResponse {
  session_id: string;
  reply: string;
  agent_trace: AgentStep[];
  citations: string[];
}
