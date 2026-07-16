import { api, tokenStore } from "./client";
import type { ChatResponse, Portfolio, RiskProfile, User } from "./types";

export async function register(email: string, fullName: string, password: string): Promise<User> {
  const resp = await api.post("/auth/register", { email, full_name: fullName, password });
  return resp.data;
}

export async function login(email: string, password: string): Promise<void> {
  const resp = await api.post("/auth/login", { email, password });
  tokenStore.set(resp.data.access_token, resp.data.refresh_token);
}

export function logout(): void {
  tokenStore.clear();
}

export async function getMe(): Promise<User> {
  const resp = await api.get("/users/me");
  return resp.data;
}

export async function getRiskProfile(): Promise<RiskProfile> {
  const resp = await api.get("/users/me/risk-profile");
  return resp.data;
}

export async function updateRiskProfile(payload: Omit<RiskProfile, "updated_at">): Promise<RiskProfile> {
  const resp = await api.put("/users/me/risk-profile", payload);
  return resp.data;
}

export async function listPortfolios(): Promise<Portfolio[]> {
  const resp = await api.get("/portfolios");
  return resp.data;
}

export async function createPortfolio(payload: {
  name: string;
  holdings: Omit<Portfolio["holdings"][number], "id">[];
}): Promise<Portfolio> {
  const resp = await api.post("/portfolios", payload);
  return resp.data;
}

export async function deletePortfolio(id: string): Promise<void> {
  await api.delete(`/portfolios/${id}`);
}

export async function sendChatMessage(message: string, sessionId?: string): Promise<ChatResponse> {
  const resp = await api.post("/chat", { message, session_id: sessionId });
  return resp.data;
}
