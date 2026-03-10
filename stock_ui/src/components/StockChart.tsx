import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from "recharts";
import type { ToolResult } from "../hooks/useAnalysisStream";

interface Props {
  data: ToolResult;
  title?: string;
}

export function StockChart({ data, title }: Props) {
  const positive = data.pct_change >= 0;
  const lineColor = positive ? "#2ecc71" : "#e74c3c";

  const chartData = Object.entries(data.daily_closes).map(([date, close]) => ({
    date,
    close,
    // Short label for X axis (e.g. "Jan 09")
    label: new Date(date + "T12:00:00Z").toLocaleDateString("en-US", {
      month: "short",
      day: "2-digit",
    }),
  }));

  const prices = chartData.map((d) => d.close);
  const yMin = Math.floor(Math.min(...prices) * 0.99);
  const yMax = Math.ceil(Math.max(...prices) * 1.01);

  // Show every ~5th label to avoid crowding
  const step = Math.max(1, Math.floor(chartData.length / 8));
  const tickIndices = new Set(chartData.filter((_, i) => i % step === 0).map((d) => d.date));

  return (
    <div className="chart-wrapper">
      {title && <h3 className="chart-title">{title}</h3>}
      <ResponsiveContainer width="100%" height={280}>
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
            formatter={(value) => [`$${Number(value).toFixed(2)}`, "Close"]}
          />
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
          <Line
            type="monotone"
            dataKey="close"
            stroke={lineColor}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
