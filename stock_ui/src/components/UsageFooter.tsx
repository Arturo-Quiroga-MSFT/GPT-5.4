import type { UsageInfo } from "../hooks/useAnalysisStream";

interface Props {
  usage: UsageInfo;
}

export function UsageFooter({ usage }: Props) {
  return (
    <div className="usage-footer">
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
