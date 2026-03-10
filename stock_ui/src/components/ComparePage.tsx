import { useState } from "react";
import { useCompareSession, LEVELS } from "../hooks/useCompareSession";
import { CompareColumn } from "./CompareColumn";

const EXAMPLE_QUERIES = [
  "Is NVDA fairly valued right now?",
  "What are the key risks for AAPL in 2026?",
  "Compare MSFT and GOOGL as long-term investments",
];

export function ComparePage() {
  const { columns, isRunning, run, reset } = useCompareSession();
  const [input, setInput] = useState("");

  const hasResults = LEVELS.some((l) => columns[l].status !== "idle");

  const handleSubmit = (text: string) => {
    const q = text.trim();
    if (!q || isRunning) return;
    setInput("");
    run(q);
  };

  return (
    <div className="compare-page">
      {/* ── Intro ─────────────────────────────────────────────── */}
      <div className="compare-intro">
        <h2 className="compare-intro-title">Reasoning Level Comparison</h2>
        <p className="compare-intro-sub">
          Ask the same question simultaneously at <strong>Low</strong>,{" "}
          <strong>Medium</strong>, and <strong>High</strong> reasoning effort.
          Watch GPT‑5.4 think harder in real time.
        </p>
      </div>

      {/* ── Input bar ─────────────────────────────────────────── */}
      <div className="compare-input-row">
        <input
          className="compare-input"
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSubmit(input)}
          placeholder="Ask any financial question…"
          disabled={isRunning}
        />
        <button
          className="compare-run-btn"
          onClick={() => handleSubmit(input)}
          disabled={isRunning || !input.trim()}
        >
          {isRunning ? "Running…" : "Compare ▶"}
        </button>
        {hasResults && !isRunning && (
          <button className="compare-reset-btn" onClick={reset}>
            Reset
          </button>
        )}
      </div>

      {/* ── Example chips ─────────────────────────────────────── */}
      {!hasResults && (
        <div className="compare-chips">
          {EXAMPLE_QUERIES.map((q) => (
            <button
              key={q}
              className="compare-chip"
              onClick={() => handleSubmit(q)}
              disabled={isRunning}
            >
              {q}
            </button>
          ))}
        </div>
      )}

      {/* ── 3-column grid ─────────────────────────────────────── */}
      {hasResults && (
        <div className="compare-grid">
          {LEVELS.map((level) => (
            <CompareColumn key={level} state={columns[level]} />
          ))}
        </div>
      )}
    </div>
  );
}
