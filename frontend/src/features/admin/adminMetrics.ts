import { ApiError, authHeaders } from "../auth/auth";

const API_BASE = "/api/v1/admin/metrics";

export interface StageMetrics {
  request_count: number;
  error_count: number;
  error_rate: number;
  p50_latency_ms: number;
  p95_latency_ms: number;
  total_tokens: number;
}

export interface OperationalMetrics {
  window_minutes: number;
  by_stage: Record<string, StageMetrics>;
}

async function parseErrorDetail(response: Response): Promise<string> {
  try {
    const body = await response.json();
    return body.detail ?? "Something went wrong. Please try again.";
  } catch {
    return "Something went wrong. Please try again.";
  }
}

export async function getOperationalMetrics(windowMinutes: number): Promise<OperationalMetrics> {
  const response = await fetch(`${API_BASE}?window_minutes=${windowMinutes}`, {
    headers: authHeaders(),
  });
  if (!response.ok) {
    throw new ApiError(await parseErrorDetail(response), response.status);
  }
  return response.json();
}
