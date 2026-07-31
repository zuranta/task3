import { ApiError, authHeaders } from "../auth/auth";

const API_BASE = "/api/v1";

export interface PassageSummary {
  location_label: string;
  content: string;
}

async function parseErrorDetail(response: Response): Promise<string> {
  try {
    const body = await response.json();
    return body.detail ?? "Something went wrong. Please try again.";
  } catch {
    return "Something went wrong. Please try again.";
  }
}

export async function getDocumentPassages(documentId: string): Promise<PassageSummary[]> {
  const response = await fetch(`${API_BASE}/documents/${documentId}/passages`, {
    headers: authHeaders(),
  });
  if (!response.ok) {
    throw new ApiError(await parseErrorDetail(response), response.status);
  }
  return response.json();
}
