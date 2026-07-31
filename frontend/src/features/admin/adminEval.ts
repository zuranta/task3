import { ApiError, authHeaders } from "../auth/auth";

const API_BASE = "/api/v1/admin/eval";

export interface DatasetItem {
  id: string;
  question: string;
  expected_answer: string;
  expected_source_reference: string | null;
}

export interface NewDatasetItem {
  question: string;
  expected_answer: string;
  expected_source_reference: string | null;
}

export interface AggregateScore {
  correctness: number;
  relevance: number;
  groundedness: number;
}

export interface ComparisonRun {
  id: string;
  version_a_label: string;
  version_b_label: string;
  status: "running" | "completed" | "partial";
  aggregate_score_a: AggregateScore | null;
  aggregate_score_b: AggregateScore | null;
  winner: "a" | "b" | "tie" | null;
  started_at: string;
  completed_at: string | null;
}

async function parseErrorDetail(response: Response): Promise<string> {
  try {
    const body = await response.json();
    return body.detail ?? "Something went wrong. Please try again.";
  } catch {
    return "Something went wrong. Please try again.";
  }
}

export async function addDatasetItem(item: NewDatasetItem): Promise<DatasetItem> {
  const response = await fetch(`${API_BASE}/dataset-items`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(item),
  });
  if (!response.ok) {
    throw new ApiError(await parseErrorDetail(response), response.status);
  }
  return response.json();
}

export async function listDatasetItems(): Promise<DatasetItem[]> {
  const response = await fetch(`${API_BASE}/dataset-items`, { headers: authHeaders() });
  if (!response.ok) {
    throw new ApiError(await parseErrorDetail(response), response.status);
  }
  return response.json();
}

export async function deleteDatasetItems(ids: string[]): Promise<void> {
  const response = await fetch(`${API_BASE}/dataset-items`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ ids }),
  });
  if (!response.ok) {
    throw new ApiError(await parseErrorDetail(response), response.status);
  }
}

export async function startComparisonRun(
  versionALabel: string,
  versionBLabel: string,
): Promise<ComparisonRun> {
  const response = await fetch(`${API_BASE}/comparison-runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ version_a_label: versionALabel, version_b_label: versionBLabel }),
  });
  if (!response.ok) {
    throw new ApiError(await parseErrorDetail(response), response.status);
  }
  return response.json();
}

export async function listComparisonRuns(): Promise<ComparisonRun[]> {
  const response = await fetch(`${API_BASE}/comparison-runs`, { headers: authHeaders() });
  if (!response.ok) {
    throw new ApiError(await parseErrorDetail(response), response.status);
  }
  return response.json();
}

export async function getComparisonRun(runId: string): Promise<ComparisonRun> {
  const response = await fetch(`${API_BASE}/comparison-runs/${runId}`, {
    headers: authHeaders(),
  });
  if (!response.ok) {
    throw new ApiError(await parseErrorDetail(response), response.status);
  }
  return response.json();
}

export async function deleteComparisonRuns(ids: string[]): Promise<void> {
  const response = await fetch(`${API_BASE}/comparison-runs`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ ids }),
  });
  if (!response.ok) {
    throw new ApiError(await parseErrorDetail(response), response.status);
  }
}
