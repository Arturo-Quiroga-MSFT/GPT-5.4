/**
 * API client — thin wrapper over the FastAPI backend.
 *
 * The streaming endpoint returns a text/event-stream where each line is:
 *   data: {"type": "<event>", "data": {...}}
 *
 * The hook (useAnalysisStream) consumes the raw fetch stream; this module
 * just holds the base URL so it is configured in one place.
 */

export const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export interface AnalyseRequest {
  ticker: string;
  days: number;
}

/** Open the SSE stream and return the raw Response (caller reads body). */
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
