/**
 * useFomcSession
 *
 * Manages the FOMC RAG chat session:
 *   - `turns`     — completed turns (user question + AI analysis)
 *   - `streaming` — the turn currently being streamed
 *   - `sources`   — retrieved FOMC source excerpts for the current query
 *   - `sendMessage(text)` — sends a new FOMC question
 *   - `reset()`   — clears history
 */

import { useCallback, useRef, useState } from "react";
import { openFomcChatStream } from "../api/client";

export interface FomcSource {
  date: string;
  similarity: number;
  preview: string;
}

export interface FomcTurn {
  id: string;
  userMessage: string;
  sources: FomcSource[];
  analysisText: string;
  reasoningText: string;
  usage?: { input_tokens: number; output_tokens: number; total_tokens: number };
  elapsed?: number;
  error?: string;
}

export type FomcPhase = "idle" | "retrieving" | "analysing" | "done" | "error";

export interface FomcStreamingState {
  userMessage: string;
  phase: FomcPhase;
  statusMessage: string;
  sources: FomcSource[];
  analysisText: string;
  reasoningText: string;
  error?: string;
}

export function useFomcSession() {
  const [turns, setTurns] = useState<FomcTurn[]>([]);
  const [streaming, setStreaming] = useState<FomcStreamingState | null>(null);
  const [lastResponseId, setLastResponseId] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const isStreaming = streaming !== null;

  const sendMessage = useCallback(
    async (text: string) => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      const turnStart = Date.now();

      setStreaming({
        userMessage: text,
        phase: "retrieving",
        statusMessage: "Searching FOMC minutes…",
        sources: [],
        analysisText: "",
        reasoningText: "",
      });

      let res: Response;
      try {
        res = await openFomcChatStream({
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

      let accSources: FomcSource[] = [];
      let accAnalysis = "";
      let accReasoning = "";

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

            case "fomc_sources":
              accSources = data.sources as FomcSource[];
              setStreaming((s) =>
                s ? { ...s, sources: accSources, phase: "analysing", statusMessage: "Analyzing…" } : null
              );
              break;

            case "analysis_start":
              setStreaming((s) =>
                s ? { ...s, phase: "analysing", statusMessage: "Generating analysis…" } : null
              );
              break;

            case "analysis_delta":
              accAnalysis += data.delta as string;
              setStreaming((s) =>
                s ? { ...s, analysisText: accAnalysis } : null
              );
              break;

            case "reasoning_delta":
              accReasoning += data.delta as string;
              setStreaming((s) =>
                s ? { ...s, reasoningText: accReasoning } : null
              );
              break;

            case "done": {
              const elapsed = (Date.now() - turnStart) / 1000;
              const responseId = data.response_id as string;
              const usage = data.usage as {
                input_tokens: number;
                output_tokens: number;
                total_tokens: number;
              };

              setLastResponseId(responseId);

              const completedTurn: FomcTurn = {
                id: responseId ?? crypto.randomUUID(),
                userMessage: text,
                sources: accSources,
                analysisText: accAnalysis,
                reasoningText: accReasoning,
                usage,
                elapsed,
              };

              setTurns((prev) => [...prev, completedTurn]);
              setStreaming(null);
              break;
            }

            case "error":
              setStreaming((s) =>
                s
                  ? { ...s, phase: "error", error: (data.message as string) ?? "Unknown error" }
                  : null
              );
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
  }, []);

  return { turns, streaming, isStreaming, sendMessage, reset };
}
