import type { UsageInfo } from "../hooks/useAnalysisStream";

interface Props {
  usage: UsageInfo;
  elapsed?: number;
}

export function UsageFooter({ usage, elapsed }: Props) {
  return (
    <div className="usage-footer">
      {elapsed != null && (
        <span className="usage-elapsed">⏱ <strong>{elapsed}s</strong></span>
      )}
      <span>Tokens used:</span>
      <span>
        Input: <strong>{usage.total_input_tokens.toLocaleString()}</strong>
      </span>
      <span>
        Output: <strong>{usage.total_output_tokens.toLocaleString()}</strong>
      </span>
      <span>
        Total:{" "}
        <strong>
          {(usage.total_input_tokens + usage.total_output_tokens).toLocaleString()}
        </strong>
      </span>
    </div>
  );
}
