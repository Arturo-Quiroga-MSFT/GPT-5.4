/**
 * Renders streaming analysis text with a blinking cursor while the stream
 * is active. Parses markdown pipe tables into real <table> elements and
 * renders **bold** text inline.
 */
interface Props {
  text: string;
  streaming: boolean;
  title: string;
  accent?: string;
}

// Detect a table separator row like |---|---|
const isSeparator = (line: string) => /^\|[\s\-|:]+\|$/.test(line.trim());
// Detect a table data row (starts and ends with |)
const isTableRow = (line: string) => /^\|.+\|$/.test(line.trim());

function parseCells(line: string): string[] {
  return line
    .trim()
    .replace(/^\||\|$/g, "")
    .split("|")
    .map((c) => c.trim());
}

/** Inline renderer: **bold** */
function renderInline(text: string, key: number) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return (
    <span key={key}>
      {parts.map((part, i) =>
        part.startsWith("**") && part.endsWith("**")
          ? <strong key={i}>{part.slice(2, -2)}</strong>
          : part
      )}
    </span>
  );
}

type Block =
  | { kind: "text"; lines: string[] }
  | { kind: "table"; headers: string[]; rows: string[][] };

function parseBlocks(text: string): Block[] {
  const lines = text.split("\n");
  const blocks: Block[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    // Look-ahead: table starts when current line is a row and next is separator
    if (
      isTableRow(line) &&
      i + 1 < lines.length &&
      isSeparator(lines[i + 1])
    ) {
      const headers = parseCells(line);
      i += 2; // skip header + separator
      const rows: string[][] = [];
      while (i < lines.length && isTableRow(lines[i])) {
        rows.push(parseCells(lines[i]));
        i++;
      }
      blocks.push({ kind: "table", headers, rows });
    } else {
      // Accumulate into a text block
      if (blocks.length === 0 || blocks[blocks.length - 1].kind !== "text") {
        blocks.push({ kind: "text", lines: [] });
      }
      (blocks[blocks.length - 1] as { kind: "text"; lines: string[] }).lines.push(line);
      i++;
    }
  }
  return blocks;
}

export function AnalysisPanel({ text, streaming, title, accent = "#00b4d8" }: Props) {
  if (!text && !streaming) return null;

  const blocks = parseBlocks(text);

  return (
    <div className="analysis-panel" style={{ borderColor: accent }}>
      <h3 className="panel-title" style={{ color: accent }}>
        {title}
      </h3>
      <div className="panel-body">
        {blocks.map((block, bi) => {
          if (block.kind === "table") {
            return (
              <div key={bi} className="md-table-wrapper">
                <table className="md-table">
                  <thead>
                    <tr>
                      {block.headers.map((h, hi) => (
                        <th key={hi}>{renderInline(h, hi)}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {block.rows.map((row, ri) => (
                      <tr key={ri}>
                        {row.map((cell, ci) => (
                          <td key={ci}>{renderInline(cell, ci)}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            );
          }
          // Text block
          return (
            <span key={bi}>
              {block.lines.map((line, li) => (
                <span key={li}>
                  {renderInline(line, li)}
                  {li < block.lines.length - 1 && <br />}
                </span>
              ))}
            </span>
          );
        })}
        {streaming && <span className="cursor" />}
      </div>
    </div>
  );
}
