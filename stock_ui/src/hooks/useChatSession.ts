/**
 * useChatSession
 *
 * Manages the full multi-turn chat experience:
 *   - `turns`   — array of completed turns (user message + AI response)
 *   - `streaming` — the turn currently being streamed (null when idle)
 *   - `sendMessage(text)` — sends a new message, chaining via previous_response_id
 *   - `reset()` — clears all history and starts fresh
 */

import { useCallback, useRef, useState } from "react";
import { openChatStream } from "../api/client";
// Re-use the canonical type definitions so all components stay in sync.
import type { ToolResult, UsageInfo, StreamPhase, ChartOverlayResult, ChartOverlays } from "./useAnalysisStream";
import type { FundamentalsResult } from "../components/FundamentalsCard";
import type { ThoughtStep } from "../components/ThoughtPanel";

export interface CompletedTurn {
  id: string;
  userMessage: string;
  toolResult?: ToolResult;
  fundamentalsResult?: FundamentalsResult;
  analysisText: string;
  usage?: UsageInfo;
  elapsed?: number;  // seconds, wall-clock for the full turn
  error?: string;
}

export interface StreamingState {
  userMessage: string;
  phase: StreamPhase;
  statusMessage: string;
  toolResult?: ToolResult;
  fundamentalsResult?: FundamentalsResult;
  analysisText: string;
  error?: string;
}

export function useChatSession() {
  const [turns, setTurns] = useState<CompletedTurn[]>([]);
  const [streaming, setStreaming] = useState<StreamingState | null>(null);
  const [lastResponseId, setLastResponseId] = useState<string | null>(null);
  const [thoughtSteps, setThoughtSteps] = useState<ThoughtStep[]>([]);
  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (text: string) => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      const turnStart = Date.now();

      setStreaming({
        userMessage: text,
        phase: "calling",
        statusMessage: "Initiating…",
        analysisText: "",
      });

      let res: Response;
      try {
        res = await openChatStream({
          message: text,
          previous_response_id: lastResponseId ?? undefined,
        });
      } catch (e) {
        setStreaming((s) => (s ? { ...s, phase: "error", error: String(e) } : null));
        return;
      }

      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      // Local accumulators for this turn
      let accToolResult: ToolResult | undefined;
      let accFundamentalsResult: FundamentalsResult | undefined;
      let accAnalysisText = "";
      let accThoughtSteps: ThoughtStep[] = [];
      setThoughtSteps([]);

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
              setStreaming((s) =>
                s ? { ...s, statusMessage: (data.message as string) ?? "" } : null
              );
              break;

            case "tool_call":
              setStreaming((s) =>
                s
                  ? {
                      ...s,
                      phase: "fetching_data",
                      statusMessage: `Fetching ${(data.args as Record<string, string>).ticker ?? "data"}…`,
                    }
                  : null
              );
              break;

            case "tool_result":
              accToolResult = data as unknown as ToolResult;
              setStreaming((s) =>
                s ? { ...s, toolResult: data as unknown as ToolResult } : null
              );
              break;

            case "fundamentals_result":
              accFundamentalsResult = data as unknown as FundamentalsResult;
              setStreaming((s) =>
                s ? { ...s, fundamentalsResult: data as unknown as FundamentalsResult } : null
              );
              break;

            case "thinking_step": {
              const step: ThoughtStep = {
                id: accThoughtSteps.length,
                text: (data.text as string) ?? "",
              };
              accThoughtSteps = [...accThoughtSteps, step];
              setThoughtSteps([...accThoughtSteps]);
              break;
            }

            case "analysis_start":
              setStreaming((s) => (s ? { ...s, phase: "analysing", analysisText: "" } : null));
              break;

            case "analysis_delta": {
              const delta = (data.delta as string) ?? "";
              accAnalysisText += delta;
              setStreaming((s) =>
                s ? { ...s, analysisText: s.analysisText + delta } : null
              );
              break;
            }

            case "chart_overlay": {
              // Merge overlay data into the most recent turn that has a toolResult
              // for the same ticker — this updates the existing chart in-place.
              const overlayResult = data as unknown as ChartOverlayResult;
              const newOverlays: ChartOverlays = overlayResult.overlays ?? {};
              setTurns((prev) => {
                const idx = [...prev].reverse().findIndex(
                  (t) => t.toolResult && t.toolResult.ticker === overlayResult.ticker
                );
                if (idx === -1) return prev;
                const realIdx = prev.length - 1 - idx;
                const updated = [...prev];
                updated[realIdx] = {
                  ...updated[realIdx],
                  toolResult: {
                    ...updated[realIdx].toolResult!,
                    overlays: {
                      ...(updated[realIdx].toolResult!.overlays ?? {}),
                      ...newOverlays,
                    },
                  },
                };
                return updated;
              });
              break;
            }

            case "analysis_done":
              break;

            case "done": {
              const responseId = (data.response_id as string) ?? null;
              const usage = data.usage as UsageInfo;
              const elapsed = Math.round((Date.now() - turnStart) / 100) / 10;
              setLastResponseId(responseId);
              setTurns((prev) => [
                ...prev,
                {
                  id: responseId ?? String(Date.now()),
                  userMessage: text,
                  toolResult: accToolResult,
                  fundamentalsResult: accFundamentalsResult,
                  analysisText: accAnalysisText,
                  usage,
                  elapsed,
                },
              ]);
              setStreaming(null);
              break;
            }

            case "error":
              setTurns((prev) => [
                ...prev,
                {
                  id: String(Date.now()),
                  userMessage: text,
                  toolResult: accToolResult,
                  fundamentalsResult: accFundamentalsResult,
                  analysisText: accAnalysisText,
                  error: (data.message as string) ?? "Unknown error",
                },
              ]);
              setStreaming(null);
              break;
          }
        }
      }
    },
    [lastResponseId]
  );

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setTurns([]);
    setStreaming(null);
    setLastResponseId(null);
    setThoughtSteps([]);
  }, []);

  return {
    turns,
    streaming,
    thoughtSteps,
    lastResponseId,
    isStreaming: streaming !== null,
    sendMessage,
    reset,
  };
}
