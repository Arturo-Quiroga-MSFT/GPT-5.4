/**
 * FundamentalsCard — renders the get_fundamentals tool result as a structured card.
 *
 * Sections:
 *   Company info • Valuation • Profitability • Growth • Financial health • Dividends • Analyst
 */

export interface FundamentalsResult {
  ticker: string;
  name?: string;
  sector?: string;
  industry?: string;
  market_cap?: number;
  currency?: string;
  // Valuation
  pe_trailing?: number;
  pe_forward?: number;
  peg_ratio?: number;
  price_to_book?: number;
  price_to_sales?: number;
  ev_to_ebitda?: number;
  ev_to_revenue?: number;
  // Profitability
  gross_margin?: number;
  operating_margin?: number;
  net_margin?: number;
  roe?: number;
  roa?: number;
  // Growth
  revenue_growth_yoy?: number;
  earnings_growth_yoy?: number;
  eps_trailing?: number;
  eps_forward?: number;
  // Financial health
  debt_to_equity?: number;
  current_ratio?: number;
  quick_ratio?: number;
  free_cash_flow?: number;
  total_cash?: number;
  total_debt?: number;
  // Dividends
  dividend_yield?: number;
  payout_ratio?: number;
  // Analyst
  analyst_recommendation?: string;
  analyst_mean_rating?: number;
  analyst_count?: number;
  target_low?: number;
  target_mean?: number;
  target_high?: number;
  current_price?: number;
  // 52-week
  week52_high?: number;
  week52_low?: number;
  beta?: number;
}

interface Props {
  data: FundamentalsResult;
}

function fmtNum(n: number | undefined, digits = 2): string {
  if (n == null) return "—";
  return n.toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

function fmtPct(n: number | undefined): string {
  if (n == null) return "—";
  return `${n >= 0 ? "+" : ""}${n.toFixed(2)}%`;
}

function fmtLarge(n: number | undefined): string {
  if (n == null) return "—";
  if (Math.abs(n) >= 1e12) return `$${(n / 1e12).toFixed(2)}T`;
  if (Math.abs(n) >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
  if (Math.abs(n) >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
  return `$${n.toLocaleString()}`;
}

function Row({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <div className="fund-row">
      <span className="fund-label">{label}</span>
      <span className="fund-value" style={accent ? { color: accent } : undefined}>{value}</span>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="fund-section">
      <div className="fund-section-title">{title}</div>
      {children}
    </div>
  );
}

const REC_COLOR: Record<string, string> = {
  buy: "#2ecc71",
  "strong buy": "#27ae60",
  hold: "#f39c12",
  sell: "#e74c3c",
  "strong sell": "#c0392b",
  underperform: "#e67e22",
  outperform: "#2ecc71",
  overweight: "#2ecc71",
  underweight: "#e74c3c",
  neutral: "#95a5a6",
};

export function FundamentalsCard({ data }: Props) {
  const recColor = data.analyst_recommendation
    ? (REC_COLOR[data.analyst_recommendation.toLowerCase()] ?? "#7b99d4")
    : undefined;

  const upside =
    data.target_mean != null && data.current_price != null && data.current_price > 0
      ? ((data.target_mean - data.current_price) / data.current_price) * 100
      : undefined;

  return (
    <div className="fundamentals-card">
      {/* ── Company header ── */}
      <div className="fund-header">
        <span className="fund-ticker">{data.ticker}</span>
        {data.name && <span className="fund-name">{data.name}</span>}
        {(data.sector || data.industry) && (
          <span className="fund-sector">
            {[data.sector, data.industry].filter(Boolean).join(" · ")}
          </span>
        )}
        {data.market_cap != null && (
          <span className="fund-mktcap">Market cap: {fmtLarge(data.market_cap)}</span>
        )}
      </div>

      <div className="fund-grid">
        {/* ── Valuation ── */}
        <Section title="Valuation">
          <Row label="P/E (trailing)" value={fmtNum(data.pe_trailing)} />
          <Row label="P/E (forward)" value={fmtNum(data.pe_forward)} />
          <Row label="PEG ratio" value={fmtNum(data.peg_ratio)} />
          <Row label="P/B" value={fmtNum(data.price_to_book)} />
          <Row label="P/S" value={fmtNum(data.price_to_sales)} />
          <Row label="EV/EBITDA" value={fmtNum(data.ev_to_ebitda)} />
          <Row label="EV/Revenue" value={fmtNum(data.ev_to_revenue)} />
        </Section>

        {/* ── Profitability ── */}
        <Section title="Profitability">
          <Row label="Gross margin" value={data.gross_margin != null ? `${data.gross_margin.toFixed(1)}%` : "—"} />
          <Row label="Operating margin" value={data.operating_margin != null ? `${data.operating_margin.toFixed(1)}%` : "—"} />
          <Row label="Net margin" value={data.net_margin != null ? `${data.net_margin.toFixed(1)}%` : "—"} />
          <Row label="ROE" value={data.roe != null ? `${data.roe.toFixed(1)}%` : "—"} />
          <Row label="ROA" value={data.roa != null ? `${data.roa.toFixed(1)}%` : "—"} />
        </Section>

        {/* ── Growth ── */}
        <Section title="Growth">
          <Row
            label="Revenue YoY"
            value={fmtPct(data.revenue_growth_yoy)}
            accent={data.revenue_growth_yoy != null ? (data.revenue_growth_yoy >= 0 ? "#2ecc71" : "#e74c3c") : undefined}
          />
          <Row
            label="Earnings YoY"
            value={fmtPct(data.earnings_growth_yoy)}
            accent={data.earnings_growth_yoy != null ? (data.earnings_growth_yoy >= 0 ? "#2ecc71" : "#e74c3c") : undefined}
          />
          <Row label="EPS (trailing)" value={data.eps_trailing != null ? `$${fmtNum(data.eps_trailing)}` : "—"} />
          <Row label="EPS (forward)" value={data.eps_forward != null ? `$${fmtNum(data.eps_forward)}` : "—"} />
        </Section>

        {/* ── Financial health ── */}
        <Section title="Financial Health">
          <Row label="Debt / Equity" value={fmtNum(data.debt_to_equity)} />
          <Row label="Current ratio" value={fmtNum(data.current_ratio)} />
          <Row label="Quick ratio" value={fmtNum(data.quick_ratio)} />
          <Row label="Free cash flow" value={fmtLarge(data.free_cash_flow)} />
          <Row label="Total cash" value={fmtLarge(data.total_cash)} />
          <Row label="Total debt" value={fmtLarge(data.total_debt)} />
        </Section>

        {/* ── 52-week & Beta ── */}
        <Section title="52-Week Range">
          <Row label="52w High" value={data.week52_high != null ? `$${fmtNum(data.week52_high)}` : "—"} />
          <Row label="52w Low" value={data.week52_low != null ? `$${fmtNum(data.week52_low)}` : "—"} />
          <Row label="Beta" value={fmtNum(data.beta)} />
          {data.dividend_yield != null && (
            <Row label="Dividend yield" value={`${data.dividend_yield.toFixed(2)}%`} />
          )}
          {data.payout_ratio != null && (
            <Row label="Payout ratio" value={`${data.payout_ratio.toFixed(1)}%`} />
          )}
        </Section>

        {/* ── Analyst ── */}
        <Section title="Analyst Consensus">
          {data.analyst_recommendation && (
            <Row
              label="Recommendation"
              value={data.analyst_recommendation.toUpperCase()}
              accent={recColor}
            />
          )}
          {data.analyst_count != null && (
            <Row label="# Analysts" value={String(data.analyst_count)} />
          )}
          {data.current_price != null && (
            <Row label="Current price" value={`$${fmtNum(data.current_price)}`} />
          )}
          {data.target_mean != null && (
            <Row label="Price target (mean)" value={`$${fmtNum(data.target_mean)}`} />
          )}
          {data.target_low != null && data.target_high != null && (
            <Row label="Target range" value={`$${fmtNum(data.target_low)} – $${fmtNum(data.target_high)}`} />
          )}
          {upside != null && (
            <Row
              label="Implied upside"
              value={fmtPct(upside)}
              accent={upside >= 0 ? "#2ecc71" : "#e74c3c"}
            />
          )}
        </Section>
      </div>
    </div>
  );
}
