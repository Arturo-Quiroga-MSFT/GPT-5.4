import { useCallback, useState } from "react";
import { openJudgeStream } from "../api/client";
import type { LevelState } from "../hooks/useCompareSession";

interface Props {
  query: string;
  columns: Record<string, LevelState>;
}

type JudgeStatus = "idle" | "running" | "done" | "error";

export function JudgePanel({ query, columns }: Props) {
  const [status, setStatus] = useState<JudgeStatus>("idle");
  const [text, setText] = useState("");
  const [elapsed, setElapsed] = useState<number | null>(null);
  const [tokens, setTokens] = useState<{ input: number; output: number } | null>(null);

  const analyse = useCallback(async () => {
    setText("");
    setElapsed(null);
    setTokens(null);
    setStatus("running");

    try {
      const res = await openJudgeStream({
        query,
        low_response: columns["low"].text,
        medium_response: columns["medium"].text,
        high_response: columns["high"].text,
      });

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
          try { parsed = JSON.parse(line.slice(6)); } catch { continue; }

          const { type, data } = parsed;
          switch (type) {
            case "judge_delta":
              setText((prev) => prev + ((data.delta as string) ?? ""));
              break;
            case "judge_done":
              setElapsed(data.elapsed as number);
              setTokens({ input: data.input_tokens as number, output: data.output_tokens as number });
              setStatus("done");
              break;
            case "error":
              setText((data.message as string) ?? "Unknown error");
              setStatus("error");
              break;
          }
        }
      }

    } catch (e) {
      setText(String(e));
      setStatus("error");
    }
  }, [query, columns]);

  const allDone = ["low", "medium", "high"].every((l) => columns[l]?.status === "done");
  if (!allDone) return null;

  return (
    <div className="judge-panel">
      <div className="judge-hdr">
        <div className="judge-hdr-left">
          <span className="judge-icon">🏆</span>
          <span className="judge-title">AI Judge</span>
          <span className="judge-sub">GPT‑5.4 scores and ranks all three responses</span>
        </div>
        <div className="judge-hdr-right">
          {status === "done" && elapsed != null && (
            <span className="judge-stat">⏱ {elapsed}s</span>
          )}
          {status === "done" && tokens && (
            <span className="judge-stat">↓ {tokens.output.toLocaleString()} tkn</span>
          )}
          {status !== "running" && (
            <button
              className="judge-run-btn"
              onClick={analyse}
            >
              {status === "idle" ? "Analyse & Rank ▶" : "Re‑analyse ↺"}
            </button>
          )}
          {status === "running" && (
            <span className="judge-running-badge">
              <span className="cmp-pulse">● Analysing…</span>
            </span>
          )}
        </div>
      </div>

      {(status === "running" || status === "done" || status === "error") && (
        <div className="judge-body">
          {status === "running" && !text && (
            <div className="cmp-skeleton" style={{ padding: "0.5rem 0" }}>
              <div className="cmp-skel-line" />
              <div className="cmp-skel-line short" />
              <div className="cmp-skel-line" />
            </div>
          )}
          {text && (
            <pre className={`judge-text${status === "error" ? " judge-text--error" : ""}`}>
              {text}
              {status === "running" && <span className="cmp-cursor" />}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
