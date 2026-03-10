import "./App.css";
import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Routes, Route, NavLink } from "react-router-dom";
import { useChatSession, type CompletedTurn } from "./hooks/useChatSession";
import { ChatMessage } from "./components/ChatMessage";
import { ChatInput } from "./components/ChatInput";
import { StatsBar } from "./components/StatsBar";
import { StockChart } from "./components/StockChart";
import { AnalysisPanel } from "./components/AnalysisPanel";
import { StatusBadge } from "./components/StatusBadge";
import { FundamentalsCard } from "./components/FundamentalsCard";
import { ThoughtPanel } from "./components/ThoughtPanel";
import { ComparePage } from "./components/ComparePage";

const TECHNICAL_PROMPTS = [
  "Analyse MSFT for the last 60 days",
  "How has AAPL performed over the past 90 days?",
  "Show me NVDA's price history for 30 days",
];

const FUNDAMENTAL_PROMPTS = [
  "Give me a full fundamental analysis of MSFT",
  "Is AAPL cheap right now?",
  "What do analysts think about NVDA?",
];

function fmt(n: number) {
  return n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtLarge(n: number | undefined): string {
  if (n == null) return "—";
  if (Math.abs(n) >= 1e12) return `$${(n / 1e12).toFixed(2)}T`;
  if (Math.abs(n) >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
  if (Math.abs(n) >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
  return `$${n.toLocaleString()}`;
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

    if (turn.fundamentalsResult) {
      const f = turn.fundamentalsResult;
      lines.push(`## ${f.ticker} — Fundamentals${f.name ? ` (${f.name})` : ""}`);
      lines.push("");
      if (f.sector || f.industry) lines.push(`**Sector:** ${[f.sector, f.industry].filter(Boolean).join(" · ")}`);
      if (f.market_cap != null) lines.push(`**Market cap:** ${fmtLarge(f.market_cap)}`);
      lines.push("");
      lines.push(`| Metric | Value |`);
      lines.push(`|--------|-------|`);
      if (f.pe_trailing != null) lines.push(`| P/E (trailing) | ${f.pe_trailing} |`);
      if (f.pe_forward != null) lines.push(`| P/E (forward) | ${f.pe_forward} |`);
      if (f.peg_ratio != null) lines.push(`| PEG ratio | ${f.peg_ratio} |`);
      if (f.price_to_book != null) lines.push(`| P/B | ${f.price_to_book} |`);
      if (f.ev_to_ebitda != null) lines.push(`| EV/EBITDA | ${f.ev_to_ebitda} |`);
      if (f.gross_margin != null) lines.push(`| Gross margin | ${f.gross_margin.toFixed(1)}% |`);
      if (f.net_margin != null) lines.push(`| Net margin | ${f.net_margin.toFixed(1)}% |`);
      if (f.roe != null) lines.push(`| ROE | ${f.roe.toFixed(1)}% |`);
      if (f.revenue_growth_yoy != null) lines.push(`| Revenue growth YoY | ${f.revenue_growth_yoy >= 0 ? "+" : ""}${f.revenue_growth_yoy.toFixed(2)}% |`);
      if (f.earnings_growth_yoy != null) lines.push(`| Earnings growth YoY | ${f.earnings_growth_yoy >= 0 ? "+" : ""}${f.earnings_growth_yoy.toFixed(2)}% |`);
      if (f.debt_to_equity != null) lines.push(`| Debt/Equity | ${f.debt_to_equity} |`);
      if (f.current_ratio != null) lines.push(`| Current ratio | ${f.current_ratio} |`);
      if (f.dividend_yield != null) lines.push(`| Dividend yield | ${f.dividend_yield.toFixed(2)}% |`);
      if (f.analyst_recommendation) lines.push(`| Analyst rec. | **${f.analyst_recommendation.toUpperCase()}** (${f.analyst_count ?? "?"} analysts) |`);
      if (f.target_mean != null) lines.push(`| Price target (mean) | $${f.target_mean} |`);
      if (f.current_price != null && f.target_mean != null) {
        const upside = ((f.target_mean - f.current_price) / f.current_price) * 100;
        lines.push(`| Implied upside | ${upside >= 0 ? "+" : ""}${upside.toFixed(1)}% |`);
      }
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

function ChatPageContent() {
  const { turns, streaming, thoughtSteps, isStreaming, sendMessage, reset } = useChatSession();
  const bottomRef = useRef<HTMLDivElement>(null);
  const [showThoughts, setShowThoughts] = useState(false);
  const [portalTarget, setPortalTarget] = useState<HTMLElement | null>(null);
  const isEmpty = turns.length === 0 && !streaming;

  // Find the portal slot in the header once mounted
  useEffect(() => {
    setPortalTarget(document.getElementById("chat-header-portal"));
  }, []);

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
    <>
      {/* ── Inject chat actions into the header portal ──────── */}
      {portalTarget && createPortal(
        <div className="chat-header-actions">
          <button
            className={`thoughts-toggle-btn${showThoughts ? " active" : ""}`}
            onClick={() => setShowThoughts((v) => !v)}
            title={showThoughts ? "Hide thought process" : "Show thought process"}
          >
            ⚡ Thoughts
          </button>
          {!isEmpty && (
            <>
              <button className="save-chat-btn" onClick={saveChat} disabled={isStreaming || turns.length === 0}>
                Save chat ↓
              </button>
              <button className="new-chat-btn" onClick={reset} disabled={isStreaming}>
                New chat
              </button>
            </>
          )}
        </div>,
        portalTarget
      )}

      {/* ── Message area ─────────────────────────────────────── */}
      <div className="chat-messages">
        {isEmpty && (
          <div className="empty-state">
            <p className="empty-title">Ask about any stock</p>
            <p className="empty-sub">
              I'll fetch real-time price data, analyse trends, and dig into fundamentals for you.
            </p>
            <div className="example-section">
              <p className="example-section-label">Technical</p>
              <div className="example-chips">
                {TECHNICAL_PROMPTS.map((p) => (
                  <button key={p} className="example-chip" onClick={() => sendMessage(p)}>
                    {p}
                  </button>
                ))}
              </div>
            </div>
            <div className="example-section">
              <p className="example-section-label fundamental">Fundamental</p>
              <div className="example-chips">
                {FUNDAMENTAL_PROMPTS.map((p) => (
                  <button key={p} className="example-chip fundamental-chip" onClick={() => sendMessage(p)}>
                    {p}
                  </button>
                ))}
              </div>
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
              {streaming.fundamentalsResult && <FundamentalsCard data={streaming.fundamentalsResult} />}
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

      {/* ── Thought Process Panel ────────────────────────────── */}
      <ThoughtPanel
        steps={thoughtSteps}
        isStreaming={isStreaming}
        onClose={() => setShowThoughts(false)}
        open={showThoughts}
      />

      {/* ── Input ────────────────────────────────────────────── */}
      <div className="chat-footer">
        <ChatInput onSend={sendMessage} disabled={isStreaming} />
      </div>
    </>
  );
}

function App() {
  return (
    <div className="chat-app">
      {/* ── Header ───────────────────────────────────────────────── */}
      <header className="chat-header">
        <div className="chat-header-left">
          <h1>Stock Analysis</h1>
          <span className="subtitle">GPT-5.4 via Azure OpenAI</span>
        </div>
        <nav className="tab-bar">
          <NavLink to="/" end className={({ isActive }) => `tab-link${isActive ? " active" : ""}`}>
            💬 Chat
          </NavLink>
          <NavLink to="/compare" className={({ isActive }) => `tab-link${isActive ? " active" : ""}`}>
            ⚡ Compare
          </NavLink>
        </nav>
        {/* Chat-page actions are rendered inside ChatPageContent */}
        <div id="chat-header-portal" />
      </header>

      {/* ── Routed pages ─────────────────────────────────────────── */}
      <Routes>
        <Route path="/" element={<ChatPageContent />} />
        <Route path="/compare" element={<ComparePage />} />
      </Routes>
    </div>
  );
}

export default App;
