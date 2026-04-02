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

export interface CompareRequest {
  message: string;
  levels?: string[];
}

/** Open the multiplexed SSE stream for the reasoning-level comparison endpoint. */
export async function openCompareStream(req: CompareRequest): Promise<Response> {
  const res = await fetch(`${API_BASE}/api/compare`, {
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

export interface JudgeRequest {
  query: string;
  low_response: string;
  medium_response: string;
  high_response: string;
}

/** Open the SSE stream for the meta-analysis judge endpoint. */
export async function openJudgeStream(req: JudgeRequest): Promise<Response> {
  const res = await fetch(`${API_BASE}/api/judge`, {
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


// ── FOMC endpoints ───────────────────────────────────────────────────

export interface FomcChatRequest {
  message: string;
  previous_response_id?: string;
}

export interface FomcStatusResponse {
  available: boolean;
  chunk_count: number;
  meeting_count: number;
}

/** Check FOMC vector store availability. */
export async function getFomcStatus(): Promise<FomcStatusResponse> {
  const res = await fetch(`${API_BASE}/api/fomc/status`);
  if (!res.ok) {
    throw new Error(`API error ${res.status}`);
  }
  return res.json();
}

/** Open the SSE stream for the FOMC RAG chat endpoint. */
export async function openFomcChatStream(req: FomcChatRequest): Promise<Response> {
  const res = await fetch(`${API_BASE}/api/fomc/chat`, {
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
