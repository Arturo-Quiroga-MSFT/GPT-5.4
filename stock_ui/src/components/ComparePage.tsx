import { useState } from "react";
import { useCompareSession, LEVELS } from "../hooks/useCompareSession";
import { CompareColumn } from "./CompareColumn";
import { JudgePanel } from "./JudgePanel";

const EXAMPLE_QUERIES = [
  "Is NVDA fairly valued right now?",
  "What are the key risks for AAPL in 2026?",
  "Compare MSFT and GOOGL as long-term investments",
];

export function ComparePage() {
  const { columns, isRunning, lastQuery, run, reset } = useCompareSession();
  const [input, setInput] = useState("");
  const [judgeText, setJudgeText] = useState("");

  const hasResults = LEVELS.some((l) => columns[l].status !== "idle");
  const allDone = LEVELS.every((l) => columns[l].status === "done");

  const handleSubmit = (text: string) => {
    const q = text.trim();
    if (!q || isRunning) return;
    setInput("");
    setJudgeText("");
    run(q);
  };

  const handleReset = () => {
    setJudgeText("");
    reset();
  };

  const saveToDisk = () => {
    const now = new Date();
    const ts = now.toISOString().replace("T", " ").slice(0, 19);
    const fileTs = now.toISOString().replace(/[^0-9]/g, "").slice(0, 15);
    const emoji: Record<string, string> = { low: "🟢", medium: "🟡", high: "🔴" };
    const label: Record<string, string> = { low: "Low", medium: "Medium", high: "High" };

    const sections = LEVELS.map((level) => {
      const col = columns[level];
      const stats = [
        col.elapsed != null ? `Elapsed: ${col.elapsed}s` : null,
        col.inputTokens != null ? `Input: ${col.inputTokens.toLocaleString()} tokens` : null,
        col.outputTokens != null ? `Output: ${col.outputTokens.toLocaleString()} tokens` : null,
      ].filter(Boolean).join(" | ");
      return [
        `## ${emoji[level]} ${label[level]} Reasoning`,
        stats ? `*${stats}*` : "",
        "",
        col.text || "*(no response)*",
      ].join("\n");
    }).join("\n\n---\n\n");

    const judgeSection = judgeText
      ? `\n\n---\n\n## 🏆 AI Judge Analysis\n\n${judgeText}`
      : "";

    const md = [
      "# GPT-5.4 Reasoning Level Comparison",
      `**Date:** ${ts}`,
      `**Query:** ${lastQuery}`,
      "",
      "---",
      "",
      sections,
      judgeSection,
    ].join("\n");

    const blob = new Blob([md], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `comparison_${fileTs}.md`;
    a.click();
    URL.revokeObjectURL(url);
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
          <button className="compare-reset-btn" onClick={handleReset}>
            Reset
          </button>
        )}
        {allDone && (
          <button className="compare-save-btn" onClick={saveToDisk}>
            💾 Save Results
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

      {/* ── Judge panel (appears when all 3 done) ─────────────── */}
      <JudgePanel query={lastQuery} columns={columns} onJudgeText={setJudgeText} />
    </div>
  );
}
