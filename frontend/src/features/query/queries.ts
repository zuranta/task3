import { ApiError, authHeaders } from "../auth/auth";

const API_BASE = "/api/v1";

export interface Citation {
  document_id: string;
  document_filename: string;
  location_label: string;
  source_removed: boolean;
}

export interface ResponseMetadata {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  context_window_utilization: number;
}

export interface Answer {
  status: "answered" | "no_answer_found";
  answer_text: string | null;
  citations: Citation[];
  metadata: ResponseMetadata;
}

export interface QueryRecord {
  id: string;
  question: string;
  status: "answered" | "no_answer_found" | "failed";
  answer: Answer | null;
  created_at: string;
}

async function parseErrorDetail(response: Response): Promise<string> {
  try {
    const body = await response.json();
    return body.detail ?? "Something went wrong. Please try again.";
  } catch {
    return "Something went wrong. Please try again.";
  }
}

export async function askQuestion(question: string): Promise<QueryRecord> {
  const response = await fetch(`${API_BASE}/queries`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ question }),
  });
  if (!response.ok) {
    throw new ApiError(await parseErrorDetail(response), response.status);
  }
  return response.json();
}

export async function listQueryHistory(): Promise<QueryRecord[]> {
  const response = await fetch(`${API_BASE}/queries`, { headers: authHeaders() });
  if (!response.ok) {
    throw new ApiError(await parseErrorDetail(response), response.status);
  }
  return response.json();
}

export async function getQuery(queryId: string): Promise<QueryRecord> {
  const response = await fetch(`${API_BASE}/queries/${queryId}`, { headers: authHeaders() });
  if (!response.ok) {
    throw new ApiError(await parseErrorDetail(response), response.status);
  }
  return response.json();
}
