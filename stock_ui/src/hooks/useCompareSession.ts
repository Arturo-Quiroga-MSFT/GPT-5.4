/**
 * useCompareSession
 *
 * Manages a single comparison run across 3 reasoning levels.
 * Opens one SSE stream; routes events by their `level` field.
 */

import { useCallback, useState } from "react";
import { openCompareStream } from "../api/client";

export type ReasoningLevel = "low" | "medium" | "high";

export const LEVELS: ReasoningLevel[] = ["low", "medium", "high"];

export interface LevelState {
  level: ReasoningLevel;
  status: "idle" | "waiting" | "streaming" | "done" | "error";
  text: string;
  elapsed?: number;
  inputTokens?: number;
  outputTokens?: number;
  error?: string;
}

const emptyLevel = (level: ReasoningLevel): LevelState => ({
  level,
  status: "idle",
  text: "",
});

const initialState = (): Record<ReasoningLevel, LevelState> => ({
  low: emptyLevel("low"),
  medium: emptyLevel("medium"),
  high: emptyLevel("high"),
});

export function useCompareSession() {
  const [columns, setColumns] = useState<Record<ReasoningLevel, LevelState>>(initialState);
  const [isRunning, setIsRunning] = useState(false);
  const [lastQuery, setLastQuery] = useState<string>("");

  const updateLevel = (level: ReasoningLevel, patch: Partial<LevelState>) =>
    setColumns((prev) => ({
      ...prev,
      [level]: { ...prev[level], ...patch },
    }));

  const run = useCallback(async (message: string) => {
    setLastQuery(message);
    setColumns(initialState());
    setIsRunning(true);

    // Mark all levels as waiting
    setColumns({
      low: { ...emptyLevel("low"), status: "waiting" },
      medium: { ...emptyLevel("medium"), status: "waiting" },
      high: { ...emptyLevel("high"), status: "waiting" },
    });

    let res: Response;
    try {
      res = await openCompareStream({ message, levels: ["low", "medium", "high"] });
    } catch (e) {
      for (const level of LEVELS) {
        updateLevel(level, { status: "error", error: String(e) });
      }
      setIsRunning(false);
      return;
    }

    const reader = res.body!.getReader();
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
        const level = data.level as ReasoningLevel;
        if (!level) continue;

        switch (type) {
          case "cmp_start":
            updateLevel(level, { status: "waiting" });
            break;

          case "cmp_streaming":
            updateLevel(level, { status: "streaming" });
            break;

          case "cmp_delta":
            setColumns((prev) => ({
              ...prev,
              [level]: {
                ...prev[level],
                text: prev[level].text + ((data.delta as string) ?? ""),
              },
            }));
            break;

          case "cmp_done":
            updateLevel(level, {
              status: "done",
              elapsed: data.elapsed as number,
              inputTokens: data.input_tokens as number,
              outputTokens: data.output_tokens as number,
            });
            break;

          case "cmp_error":
            updateLevel(level, {
              status: "error",
              error: (data.message as string) ?? "Unknown error",
            });
            break;
        }
      }
    }

    setIsRunning(false);
  }, []);

  const reset = useCallback(() => {
    setColumns(initialState());
    setLastQuery("");
    setIsRunning(false);
  }, []);

  return { columns, isRunning, lastQuery, run, reset };
}
