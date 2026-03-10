import type { ToolResult } from "../hooks/useAnalysisStream";

interface Props {
  data: ToolResult;
}

function fmt(n: number) {
  return n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtVol(n: number) {
  return n.toLocaleString("en-US");
}

export function StatsBar({ data }: Props) {
  const positive = data.pct_change >= 0;
  return (
    <div className="stats-bar">
      <div className="stat">
        <span className="stat-label">Open</span>
        <span className="stat-value">${fmt(data.open_price)}</span>
      </div>
      <div className="stat">
        <span className="stat-label">Close</span>
        <span className="stat-value">${fmt(data.latest_close)}</span>
      </div>
      <div className="stat">
        <span className="stat-label">High</span>
        <span className="stat-value high">${fmt(data.period_high)}</span>
      </div>
      <div className="stat">
        <span className="stat-label">Low</span>
        <span className="stat-value low">${fmt(data.period_low)}</span>
      </div>
      <div className="stat">
        <span className="stat-label">Change</span>
        <span className={`stat-value ${positive ? "positive" : "negative"}`}>
          {positive ? "+" : ""}
          {fmt(data.pct_change)}%
        </span>
      </div>
      <div className="stat">
        <span className="stat-label">Avg Vol</span>
        <span className="stat-value">{fmtVol(data.avg_volume)}</span>
      </div>
      <div className="stat">
        <span className="stat-label">Period</span>
        <span className="stat-value period">
          {data.period_start} → {data.period_end}
        </span>
      </div>
    </div>
  );
}
