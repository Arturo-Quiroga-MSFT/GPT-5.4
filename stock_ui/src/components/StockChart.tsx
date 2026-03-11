import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { ToolResult } from "../hooks/useAnalysisStream";

interface Props {
  data: ToolResult;
  title?: string;
}

// Colours assigned to overlay lines in order
const OVERLAY_COLOURS = ["#f39c12", "#9b59b6", "#1abc9c", "#e67e22", "#3498db", "#e91e63"];

// Nice display labels
function overlayLabel(key: string): string {
  const m = key.match(/^(sma|ema)_(\d+)$/);
  if (m) return `${m[1].toUpperCase()} ${m[2]}`;
  if (key.startsWith("bollinger_")) return `BB ${key.split("_")[1]}`;
  if (key === "support_resistance") return "S/R";
  return key;
}

export function StockChart({ data, title }: Props) {
  const positive = data.pct_change >= 0;
  const lineColor = positive ? "#2ecc71" : "#e74c3c";
  const overlays = data.overlays ?? {};

  // Merge all overlay line-series data into chartData points
  // Merge all overlay line-series data into chartData points
  type ChartPoint = { date: string; close: number; label: string } & Record<string, string | number | null>;
  const chartData: ChartPoint[] = Object.entries(data.daily_closes).map(([date, close]) => {
    const point: ChartPoint = {
      date,
      close,
      label: new Date(date + "T12:00:00Z").toLocaleDateString("en-US", {
        month: "short",
        day: "2-digit",
      }),
    };
    for (const [key, overlay] of Object.entries(overlays)) {
      if (overlay.type === "sma" || overlay.type === "ema") {
        point[key] = overlay.data[date] ?? null;
      } else if (overlay.type === "bollinger") {
        point[`${key}_mid`] = overlay.mid[date] ?? null;
        point[`${key}_upper`] = overlay.upper[date] ?? null;
        point[`${key}_lower`] = overlay.lower[date] ?? null;
      }
    }
    return point;
  });

  // Collect all price values (including overlays) for auto y-domain
  const allPrices: number[] = chartData.flatMap((d) =>
    Object.entries(d)
      .filter(([k]) => k !== "date" && k !== "label")
      .map(([, v]) => v as unknown as unknown as number)
      .filter((v) => typeof v === "number" && isFinite(v))
  );
  const yMin = Math.floor(Math.min(...allPrices) * 0.99);
  const yMax = Math.ceil(Math.max(...allPrices) * 1.01);

  // Show every ~5th label to avoid crowding
  const step = Math.max(1, Math.floor(chartData.length / 8));
  const tickIndices = new Set(chartData.filter((_, i) => i % step === 0).map((d) => d.date as string));

  // Assign colours to line overlays
  const lineOverlayKeys = Object.entries(overlays)
    .filter(([, o]) => o.type === "sma" || o.type === "ema")
    .map(([k]) => k);
  const bollingerOverlayKeys = Object.keys(overlays).filter(
    (k) => overlays[k].type === "bollinger"
  );

  // Support / resistance reference lines
  const srOverlay = overlays["support_resistance"];
  const resistanceLevels = srOverlay?.type === "support_resistance" ? srOverlay.resistance : [];
  const supportLevels = srOverlay?.type === "support_resistance" ? srOverlay.support : [];

  const hasOverlays = Object.keys(overlays).length > 0;

  return (
    <div className="chart-wrapper">
      {title && <h3 className="chart-title">{title}</h3>}
      <ResponsiveContainer width="100%" height={hasOverlays ? 320 : 280}>
        <LineChart data={chartData} margin={{ top: 8, right: 24, bottom: 8, left: 16 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2a3a" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11, fill: "#888" }}
            tickFormatter={(v) =>
              tickIndices.has(v)
                ? new Date(v + "T12:00:00Z").toLocaleDateString("en-US", {
                    month: "short",
                    day: "2-digit",
                  })
                : ""
            }
          />
          <YAxis
            domain={[yMin, yMax]}
            tick={{ fontSize: 11, fill: "#888" }}
            tickFormatter={(v: number) => `$${v.toFixed(0)}`}
            width={58}
          />
          <Tooltip
            contentStyle={{ background: "#1e1e2e", border: "1px solid #333", borderRadius: 6 }}
            labelFormatter={(label) => label}
            formatter={(value, name) => {
              const n = name as string;
              const label = n === "close" ? "Close" : overlayLabel(n.replace(/_mid$|_upper$|_lower$/, (s) => {
                if (s === "_mid") return " Mid";
                if (s === "_upper") return " Upper";
                if (s === "_lower") return " Lower";
                return s;
              }));
              return [`$${Number(value).toFixed(2)}`, label];
            }}
          />
          {hasOverlays && <Legend wrapperStyle={{ fontSize: 11, paddingTop: 4 }} formatter={(v) => overlayLabel(v)} />}

          {/* Period high / low reference lines */}
          <ReferenceLine
            y={data.period_high}
            stroke="#2ecc71"
            strokeDasharray="4 2"
            label={{ value: `High $${data.period_high.toFixed(2)}`, fill: "#2ecc71", fontSize: 10, position: "insideTopRight" }}
          />
          <ReferenceLine
            y={data.period_low}
            stroke="#e74c3c"
            strokeDasharray="4 2"
            label={{ value: `Low $${data.period_low.toFixed(2)}`, fill: "#e74c3c", fontSize: 10, position: "insideBottomRight" }}
          />

          {/* Support / Resistance reference lines */}
          {resistanceLevels.map((lvl, i) => (
            <ReferenceLine
              key={`res_${i}`}
              y={lvl}
              stroke="#f39c12"
              strokeDasharray="6 3"
              label={{ value: `R $${lvl.toFixed(2)}`, fill: "#f39c12", fontSize: 9, position: "insideTopLeft" }}
            />
          ))}
          {supportLevels.map((lvl, i) => (
            <ReferenceLine
              key={`sup_${i}`}
              y={lvl}
              stroke="#3498db"
              strokeDasharray="6 3"
              label={{ value: `S $${lvl.toFixed(2)}`, fill: "#3498db", fontSize: 9, position: "insideBottomLeft" }}
            />
          ))}

          {/* Bollinger Band lines */}
          {bollingerOverlayKeys.map((key, ci) => {
            const color = OVERLAY_COLOURS[ci % OVERLAY_COLOURS.length];
            return [
              <Line key={`${key}_upper`} type="monotone" dataKey={`${key}_upper`} stroke={color}
                strokeWidth={1} strokeDasharray="4 2" dot={false} name={`${key}_upper`} />,
              <Line key={`${key}_mid`} type="monotone" dataKey={`${key}_mid`} stroke={color}
                strokeWidth={1.5} dot={false} name={`${key}_mid`} />,
              <Line key={`${key}_lower`} type="monotone" dataKey={`${key}_lower`} stroke={color}
                strokeWidth={1} strokeDasharray="4 2" dot={false} name={`${key}_lower`} />,
            ];
          })}

          {/* SMA / EMA lines */}
          {lineOverlayKeys.map((key, i) => (
            <Line
              key={key}
              type="monotone"
              dataKey={key}
              stroke={OVERLAY_COLOURS[(bollingerOverlayKeys.length + i) % OVERLAY_COLOURS.length]}
              strokeWidth={1.5}
              dot={false}
              name={key}
              connectNulls
            />
          ))}

          {/* Main price line — rendered last so it sits on top */}
          <Line
            type="monotone"
            dataKey="close"
            stroke={lineColor}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
            name="close"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
