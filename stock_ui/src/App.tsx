import "./App.css";
import { useEffect, useRef } from "react";
import { useChatSession } from "./hooks/useChatSession";
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

function App() {
  const { turns, streaming, isStreaming, sendMessage, reset } = useChatSession();
  const bottomRef = useRef<HTMLDivElement>(null);
  const isEmpty = turns.length === 0 && !streaming;

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
          <button className="new-chat-btn" onClick={reset} disabled={isStreaming}>
            New chat
          </button>
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
