import { useEffect, useRef } from "react";

export interface ThoughtStep {
  id: number;
  text: string;
}

interface Props {
  steps: ThoughtStep[];
  isStreaming: boolean;
  onClose: () => void;
  open: boolean;
}

export function ThoughtPanel({ steps, isStreaming, onClose, open }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [steps.length]);

  return (
    <div className={`thought-panel${open ? " open" : ""}`}>
      <div className="thought-panel-hdr">
        <div className="thought-panel-hdr-left">
          <span className="thought-panel-lamp">⚡</span>
          <span className="thought-panel-title">Thought Process</span>
          {isStreaming && <span className="thought-live-badge">LIVE</span>}
        </div>
        <button className="thought-close" onClick={onClose} aria-label="Close panel">
          ✕
        </button>
      </div>

      <div className="thought-body">
        {steps.length === 0 ? (
          <p className="thought-idle">
            Ask a question to watch GPT‑5.4 think in real time.
          </p>
        ) : (
          <>
            {steps.map((step, idx) => {
              const isLast = idx === steps.length - 1;
              const active = isStreaming && isLast;
              return (
                <div
                  key={step.id}
                  className={`thought-step${active ? " thought-step--active" : ""}`}
                >
                  <span className="thought-dot" />
                  <span className="thought-step-txt">{step.text}</span>
                </div>
              );
            })}
          </>
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
