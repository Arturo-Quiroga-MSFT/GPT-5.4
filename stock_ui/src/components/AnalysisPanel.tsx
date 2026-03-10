/**
 * Renders streaming analysis text with a blinking cursor while the stream
 * is active.  Preserves line breaks by splitting on newlines.
 */
interface Props {
  text: string;
  streaming: boolean;
  title: string;
  accent?: string;
}

export function AnalysisPanel({ text, streaming, title, accent = "#00b4d8" }: Props) {
  if (!text && !streaming) return null;

  const lines = text.split("\n");

  return (
    <div className="analysis-panel" style={{ borderColor: accent }}>
      <h3 className="panel-title" style={{ color: accent }}>
        {title}
      </h3>
      <div className="panel-body">
        {lines.map((line, i) => (
          <span key={i}>
            {line}
            {i < lines.length - 1 && <br />}
          </span>
        ))}
        {streaming && <span className="cursor" />}
      </div>
    </div>
  );
}
