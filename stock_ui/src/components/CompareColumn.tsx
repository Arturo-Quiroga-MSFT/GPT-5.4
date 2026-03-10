import type { LevelState } from "../hooks/useCompareSession";

interface Props {
  state: LevelState;
}

const LEVEL_META: Record<string, { label: string; color: string; glow: string }> = {
  low:    { label: "Low",    color: "#2ecc71", glow: "rgba(46,204,113,0.35)" },
  medium: { label: "Medium", color: "#f39c12", glow: "rgba(243,156,18,0.35)" },
  high:   { label: "High",   color: "#e74c3c", glow: "rgba(231,76,60,0.35)"  },
};

export function CompareColumn({ state }: Props) {
  const meta = LEVEL_META[state.level] ?? { label: state.level, color: "#7b61ff", glow: "rgba(123,97,255,0.35)" };
  const { status, text, elapsed, inputTokens, outputTokens, error } = state;

  return (
    <div className="cmp-column">
      {/* Header */}
      <div className="cmp-col-hdr" style={{ "--col-color": meta.color, "--col-glow": meta.glow } as React.CSSProperties}>
        <span className="cmp-col-badge" style={{ background: meta.color }}>{meta.label}</span>
        <span className="cmp-col-title">Reasoning</span>
        <span className={`cmp-col-status cmp-status--${status}`}>
          {status === "waiting"   && "Waiting…"}
          {status === "streaming" && <span className="cmp-pulse">● Streaming</span>}
          {status === "done"      && `✓ ${elapsed}s`}
          {status === "error"     && "✗ Error"}
          {status === "idle"      && ""}
        </span>
      </div>

      {/* Body */}
      <div className="cmp-col-body">
        {status === "idle" && (
          <p className="cmp-idle-txt">Enter a query above to start.</p>
        )}
        {status === "waiting" && (
          <div className="cmp-skeleton">
            <div className="cmp-skel-line" />
            <div className="cmp-skel-line short" />
            <div className="cmp-skel-line" />
            <div className="cmp-skel-line short" />
          </div>
        )}
        {(status === "streaming" || status === "done") && text && (
          <p className="cmp-response-text">
            {text}
            {status === "streaming" && <span className="cmp-cursor" />}
          </p>
        )}
        {status === "error" && (
          <p className="cmp-error-txt">{error}</p>
        )}
      </div>

      {/* Footer stats */}
      {status === "done" && (
        <div className="cmp-col-footer">
          <span className="cmp-stat">⏱ {elapsed}s</span>
          <span className="cmp-stat">↑ {inputTokens?.toLocaleString()} tkn</span>
          <span className="cmp-stat">↓ {outputTokens?.toLocaleString()} tkn</span>
        </div>
      )}
    </div>
  );
}
