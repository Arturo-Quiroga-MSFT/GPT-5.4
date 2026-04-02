/**
 * FomcPage — interactive FOMC minutes RAG analysis tab.
 *
 * Features:
 *   • Multi-turn chat grounded in FOMC meeting minutes
 *   • Source attribution table for each answer
 *   • Streaming analysis with reasoning summaries
 */

import { useEffect, useRef, useState } from "react";
import { useFomcSession, type FomcTurn, type FomcSource } from "../hooks/useFomcSession";
import { getFomcStatus, type FomcStatusResponse } from "../api/client";
import { AnalysisPanel } from "./AnalysisPanel";
import { ChatInput } from "./ChatInput";

const EXAMPLE_QUERIES = [
  "What was the Fed's stance on inflation throughout 2024?",
  "How did the FOMC view the labor market in their last few meetings?",
  "What drove the September 2024 rate cut decision?",
  "Compare the hawkish vs dovish tone across 2024 meetings",
];

function SourcesTable({ sources }: { sources: FomcSource[] }) {
  if (sources.length === 0) return null;
  return (
    <div className="fomc-sources">
      <p className="fomc-sources-label">Retrieved Sources</p>
      <table className="fomc-sources-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Meeting Date</th>
            <th>Relevance</th>
            <th>Preview</th>
          </tr>
        </thead>
        <tbody>
          {sources.map((s, i) => (
            <tr key={i}>
              <td className="fomc-src-num">{i + 1}</td>
              <td className="fomc-src-date">{s.date}</td>
              <td className="fomc-src-score">{(s.similarity * 100).toFixed(1)}%</td>
              <td className="fomc-src-preview">{s.preview}…</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function FomcMessage({ turn }: { turn: FomcTurn }) {
  return (
    <div className="chat-turn">
      <div className="user-bubble">{turn.userMessage}</div>
      <div className="ai-response">
        <SourcesTable sources={turn.sources} />
        {turn.reasoningText && (
          <div className="fomc-reasoning">
            <span className="fomc-reasoning-label">Reasoning</span>
            <p>{turn.reasoningText}</p>
          </div>
        )}
        {turn.analysisText && (
          <AnalysisPanel
            text={turn.analysisText}
            streaming={false}
            title="FOMC Analysis"
            accent="#00c896"
          />
        )}
        {turn.usage && (
          <div className="usage-footer">
            Tokens — input: {turn.usage.input_tokens.toLocaleString()}, output:{" "}
            {turn.usage.output_tokens.toLocaleString()} · {turn.elapsed?.toFixed(1)}s
          </div>
        )}
        {turn.error && <div className="error-box">{turn.error}</div>}
      </div>
    </div>
  );
}

export function FomcPage() {
  const { turns, streaming, isStreaming, sendMessage, reset } = useFomcSession();
  const bottomRef = useRef<HTMLDivElement>(null);
  const [status, setStatus] = useState<FomcStatusResponse | null>(null);

  const isEmpty = turns.length === 0 && !streaming;

  useEffect(() => {
    getFomcStatus().then(setStatus).catch(() => setStatus({ available: false, chunk_count: 0, meeting_count: 0 }));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns.length, streaming?.analysisText]);

  return (
    <>
      <div className="chat-messages">
        {isEmpty && (
          <div className="empty-state">
            <p className="empty-title">FOMC Minutes Analysis</p>
            <p className="empty-sub">
              Ask questions about U.S. monetary policy grounded in official Federal Reserve meeting minutes.
            </p>
            {status && (
              <p className="fomc-status-badge">
                {status.available ? (
                  <>
                    <span className="fomc-dot available" />
                    {status.meeting_count} meetings indexed · {status.chunk_count.toLocaleString()} chunks
                  </>
                ) : (
                  <>
                    <span className="fomc-dot unavailable" />
                    Vector store not available — run the FOMC indexer first
                  </>
                )}
              </p>
            )}
            <div className="example-section">
              <p className="example-section-label fomc-label">Example Questions</p>
              <div className="example-chips">
                {EXAMPLE_QUERIES.map((q) => (
                  <button key={q} className="example-chip fomc-chip" onClick={() => sendMessage(q)}>
                    {q}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Completed turns */}
        {turns.map((turn) => (
          <FomcMessage key={turn.id} turn={turn} />
        ))}

        {/* Streaming turn */}
        {streaming && (
          <div className="chat-turn">
            <div className="user-bubble">{streaming.userMessage}</div>
            <div className="ai-response">
              <div className="fomc-phase-badge">
                {streaming.phase === "retrieving" && "🔍 "}
                {streaming.phase === "analysing" && "🏦 "}
                {streaming.statusMessage}
              </div>
              <SourcesTable sources={streaming.sources} />
              {streaming.reasoningText && (
                <div className="fomc-reasoning">
                  <span className="fomc-reasoning-label">Reasoning</span>
                  <p>{streaming.reasoningText}</p>
                </div>
              )}
              {(streaming.analysisText || streaming.phase === "analysing") && (
                <AnalysisPanel
                  text={streaming.analysisText}
                  streaming={streaming.phase === "analysing"}
                  title="FOMC Analysis"
                  accent="#00c896"
                />
              )}
              {streaming.error && <div className="error-box">{streaming.error}</div>}
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Footer controls */}
      <div className="chat-footer">
        <div className="fomc-footer-row">
          {!isEmpty && (
            <button className="new-chat-btn" onClick={reset} disabled={isStreaming}>
              New chat
            </button>
          )}
        </div>
        <ChatInput
          onSend={sendMessage}
          disabled={isStreaming || (status !== null && !status.available)}
        />
      </div>
    </>
  );
}
