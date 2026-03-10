import "./App.css";
import { useCallback, useEffect, useRef } from "react";
import { useChatSession, type CompletedTurn } from "./hooks/useChatSession";
import { ChatMessage } from "./components/ChatMessage";
import { ChatInput } from "./components/ChatInput";
import { StatsBar } from "./components/StatsBar";
import { StockChart } from "./components/StockChart";
import { AnalysisPanel } from "./components/AnalysisPanel";
import { StatusBadge } from "./components/StatusBadge";

const EXAMPLE_PROMPTS = [
  "Analyse MSFT for the last 60 days",
  "How has AAPL performed over the past 90 days?",
  "Show me NVDA's price history for 30 days",
];

function fmt(n: number) {
  return n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function turnsToMarkdown(turns: CompletedTurn[]): string {
  const date = new Date().toLocaleDateString("en-US", {
    year: "numeric", month: "long", day: "numeric",
  });
  const lines: string[] = [
    "# Stock Analysis — Chat Export",
    `_Exported on ${date}_`,
    "",
    "---",
    "",
  ];

  for (const turn of turns) {
    lines.push(`## You`);
    lines.push("");
    lines.push(`> ${turn.userMessage}`);
    lines.push("");

    if (turn.error) {
      lines.push(`**Error:** ${turn.error}`);
      lines.push("");
    }

    if (turn.toolResult) {
      const t = turn.toolResult;
      lines.push(`## ${t.ticker} — Market Data`);
      lines.push("");
      lines.push(`| Metric | Value |`);
      lines.push(`|--------|-------|`);
      lines.push(`| Period | ${t.period_start} → ${t.period_end} |`);
      lines.push(`| Trading days | ${t.trading_days} |`);
      lines.push(`| Open | $${fmt(t.open_price)} |`);
      lines.push(`| Latest close | $${fmt(t.latest_close)} |`);
      lines.push(`| Period high | $${fmt(t.period_high)} |`);
      lines.push(`| Period low | $${fmt(t.period_low)} |`);
      lines.push(`| Change | ${t.pct_change >= 0 ? "+" : ""}${fmt(t.pct_change)}% |`);
      lines.push(`| Avg daily volume | ${t.avg_volume.toLocaleString()} |`);
      lines.push("");
    }

    if (turn.analysisText) {
      lines.push(`## Analysis`);
      lines.push("");
      lines.push(turn.analysisText.trim());
      lines.push("");
    }

    if (turn.usage) {
      lines.push(
        `_Tokens — input: ${turn.usage.total_input_tokens.toLocaleString()}, ` +
        `output: ${turn.usage.total_output_tokens.toLocaleString()}, ` +
        `total: ${(turn.usage.total_input_tokens + turn.usage.total_output_tokens).toLocaleString()}_`
      );
      lines.push("");
    }

    lines.push("---");
    lines.push("");
  }

  return lines.join("\n");
}

function App() {
  const { turns, streaming, isStreaming, sendMessage, reset } = useChatSession();
  const bottomRef = useRef<HTMLDivElement>(null);
  const isEmpty = turns.length === 0 && !streaming;

  const saveChat = useCallback(() => {
    if (turns.length === 0) return;
    const md = turnsToMarkdown(turns);
    const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    const dateStr = new Date().toISOString().slice(0, 10);
    a.href = url;
    a.download = `stock-analysis-${dateStr}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }, [turns]);

  // Auto-scroll to bottom as new content arrives
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns.length, streaming?.analysisText]);

  return (
    <div className="chat-app">
      {/* ── Header ───────────────────────────────────────────────── */}
      <header className="chat-header">
        <div className="chat-header-left">
          <h1>Stock Analysis</h1>
          <span className="subtitle">GPT-5.4 via Azure OpenAI</span>
        </div>
        {!isEmpty && (
          <div className="chat-header-actions">
            <button className="save-chat-btn" onClick={saveChat} disabled={isStreaming || turns.length === 0}>
              Save chat ↓
            </button>
            <button className="new-chat-btn" onClick={reset} disabled={isStreaming}>
              New chat
            </button>
          </div>
        )}
      </header>

      {/* ── Message area ─────────────────────────────────────────── */}
      <div className="chat-messages">
        {isEmpty && (
          <div className="empty-state">
            <p className="empty-title">Ask about any stock</p>
            <p className="empty-sub">
              I'll fetch real-time price data and analyse the trend for you.
            </p>
            <div className="example-chips">
              {EXAMPLE_PROMPTS.map((p) => (
                <button key={p} className="example-chip" onClick={() => sendMessage(p)}>
                  {p}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Completed turns */}
        {turns.map((turn) => (
          <ChatMessage key={turn.id} turn={turn} />
        ))}

        {/* Streaming turn */}
        {streaming && (
          <div className="chat-turn">
            <div className="user-bubble">{streaming.userMessage}</div>
            <div className="ai-response">
              <StatusBadge phase={streaming.phase} message={streaming.statusMessage} />
              {streaming.toolResult && <StatsBar data={streaming.toolResult} />}
              {streaming.toolResult && (
                <StockChart
                  data={streaming.toolResult}
                  title={`${streaming.toolResult.ticker} — Daily Close`}
                />
              )}
              {(streaming.analysisText || streaming.phase === "analysing") && (
                <AnalysisPanel
                  text={streaming.analysisText}
                  streaming={streaming.phase === "analysing"}
                  title="Analysis"
                  accent="#00b4d8"
                />
              )}
              {streaming.error && <div className="error-box">{streaming.error}</div>}
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* ── Input ────────────────────────────────────────────────── */}
      <div className="chat-footer">
        <ChatInput onSend={sendMessage} disabled={isStreaming} />
      </div>
    </div>
  );
}

export default App;
