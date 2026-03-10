import type { StreamPhase } from "../hooks/useAnalysisStream";

interface Props {
  phase: StreamPhase;
  message: string;
}

const PHASE_LABELS: Record<StreamPhase, string> = {
  idle: "",
  calling: "Calling model",
  fetching_data: "Fetching data",
  analysing: "Generating analysis",
  followup: "Running follow-up",
  done: "Complete",
  error: "Error",
};

const PHASE_COLORS: Record<StreamPhase, string> = {
  idle: "transparent",
  calling: "#f39c12",
  fetching_data: "#3498db",
  analysing: "#00b4d8",
  followup: "#f1c40f",
  done: "#2ecc71",
  error: "#e74c3c",
};

export function StatusBadge({ phase, message }: Props) {
  if (phase === "idle") return null;
  return (
    <div className="status-badge" style={{ borderColor: PHASE_COLORS[phase] }}>
      {phase !== "done" && phase !== "error" && (
        <span className="spinner" style={{ borderTopColor: PHASE_COLORS[phase] }} />
      )}
      <span style={{ color: PHASE_COLORS[phase] }}>{PHASE_LABELS[phase]}</span>
      {message && phase !== "done" && (
        <span className="status-message">{message}</span>
      )}
    </div>
  );
}
