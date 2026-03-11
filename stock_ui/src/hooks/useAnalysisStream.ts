/**
 * useAnalysisStream
 *
 * Consumes the SSE stream from POST /api/analyse and maps each event type
 * onto a typed state object.  The caller gets a single `state` value and a
 * `run` function to trigger a new analysis.
 *
 * Event phases (in order):
 *   status → tool_call → tool_result → analysis_start → analysis_delta* →
 *   analysis_done → followup_start → [followup_tool_call → followup_tool_result]* →
 *   followup_text → done | error
 */

import { useCallback, useRef, useState } from "react";
import { openAnalysisStream, type AnalyseRequest } from "../api/client";

export interface ToolResult {
  ticker: string;
  period_start: string;
  period_end: string;
  trading_days: number;
  open_price: number;
  latest_close: number;
  period_high: number;
  period_low: number;
  avg_volume: number;
  pct_change: number;
  daily_closes: Record<string, number>;
  /** Indicator overlays merged in from a follow-up chart_overlay event */
  overlays?: ChartOverlays;
}

export interface SmaOverlay {
  type: "sma";
  period: number;
  data: Record<string, number>;
}

export interface EmaOverlay {
  type: "ema";
  period: number;
  data: Record<string, number>;
}

export interface BollingerOverlay {
  type: "bollinger";
  period: number;
  mid: Record<string, number>;
  upper: Record<string, number>;
  lower: Record<string, number>;
}

export interface SupportResistanceOverlay {
  type: "support_resistance";
  resistance: number[];
  support: number[];
}

export type ChartOverlay = SmaOverlay | EmaOverlay | BollingerOverlay | SupportResistanceOverlay;
export type ChartOverlays = Record<string, ChartOverlay>;

export interface ChartOverlayResult {
  ticker: string;
  overlays: ChartOverlays;
}

export interface UsageInfo {
  total_input_tokens: number;
  total_output_tokens: number;
}

export type StreamPhase =
  | "idle"
  | "calling"
  | "fetching_data"
  | "analysing"
  | "followup"
  | "done"
  | "error";

export interface AnalysisState {
  phase: StreamPhase;
  statusMessage: string;
  toolResult: ToolResult | null;
  analysisText: string;
  followupText: string;
  usage: UsageInfo | null;
  error: string | null;
  /** Tracks any additional ticker fetched during follow-up (e.g. a comparison) */
  followupToolResult: ToolResult | null;
}

const INITIAL_STATE: AnalysisState = {
  phase: "idle",
  statusMessage: "",
  toolResult: null,
  analysisText: "",
  followupText: "",
  usage: null,
  error: null,
  followupToolResult: null,
};

export function useAnalysisStream() {
  const [state, setState] = useState<AnalysisState>(INITIAL_STATE);
  const abortRef = useRef<AbortController | null>(null);

  const run = useCallback(async (req: AnalyseRequest) => {
    // Cancel any in-flight request
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setState({ ...INITIAL_STATE, phase: "calling", statusMessage: "Initiating…" });

    let response: Response;
    try {
      response = await openAnalysisStream(req);
    } catch (e) {
      setState((s) => ({ ...s, phase: "error", error: String(e) }));
      return;
    }

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        let parsed: { type: string; data: Record<string, unknown> };
        try {
          parsed = JSON.parse(line.slice(6));
        } catch {
          continue;
        }

        const { type, data } = parsed;

        switch (type) {
          case "status":
            setState((s) => ({
              ...s,
              phase: "calling",
              statusMessage: (data.message as string) ?? "",
            }));
            break;

          case "tool_call":
            setState((s) => ({
              ...s,
              phase: "fetching_data",
              statusMessage: `Calling ${data.name}(${JSON.stringify(data.args)})…`,
            }));
            break;

          case "tool_result":
            setState((s) => ({
              ...s,
              toolResult: data as unknown as ToolResult,
            }));
            break;

          case "analysis_start":
            setState((s) => ({ ...s, phase: "analysing", analysisText: "" }));
            break;

          case "analysis_delta":
            setState((s) => ({
              ...s,
              analysisText: s.analysisText + ((data.delta as string) ?? ""),
            }));
            break;

          case "analysis_done":
            break;

          case "followup_start":
            setState((s) => ({
              ...s,
              phase: "followup",
              statusMessage: "Running follow-up analysis…",
            }));
            break;

          case "followup_tool_call":
            setState((s) => ({
              ...s,
              statusMessage: `Follow-up: calling ${data.name}…`,
            }));
            break;

          case "followup_tool_result":
            setState((s) => ({
              ...s,
              followupToolResult: data as unknown as ToolResult,
            }));
            break;

          case "followup_text":
            setState((s) => ({
              ...s,
              followupText: (data.text as string) ?? "",
            }));
            break;

          case "done":
            setState((s) => ({
              ...s,
              phase: "done",
              usage: data.usage as unknown as UsageInfo,
            }));
            break;

          case "error":
            setState((s) => ({
              ...s,
              phase: "error",
              error: (data.message as string) ?? "Unknown error",
            }));
            break;
        }
      }
    }
  }, []);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setState(INITIAL_STATE);
  }, []);

  return { state, run, reset };
}
