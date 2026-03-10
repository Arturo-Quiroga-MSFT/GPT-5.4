/**
 * API client — thin wrapper over the FastAPI backend.
 */

export const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export interface AnalyseRequest {
  ticker: string;
  days: number;
}

export interface ChatRequest {
  message: string;
  previous_response_id?: string;
}

/** Open the SSE stream for the structured analyse endpoint (kept for compat). */
export async function openAnalysisStream(req: AnalyseRequest): Promise<Response> {
  const res = await fetch(`${API_BASE}/api/analyse`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res;
}

/** Open the SSE stream for the free-form chat endpoint. */
export async function openChatStream(req: ChatRequest): Promise<Response> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res;
}
