"""
Stock data service.

Provides the get_stock_history and get_fundamentals tools used by the LLM,
plus their TOOLS / TOOL_DISPATCH definitions.
"""

import json
from datetime import date, timedelta

import yfinance as yf


# ── Tool schemas (registered with the model) ──────────────────────────
TOOLS = [
    {
        "type": "function",
        "name": "get_stock_history",
        "description": (
            "Retrieve daily OHLCV (open, high, low, close, volume) price history "
            "for a stock ticker over the last N calendar days."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker symbol, e.g. AAPL, MSFT, TSLA",
                },
                "days": {
                    "type": "integer",
                    "description": "Number of calendar days of history to retrieve (e.g. 30)",
                },
            },
            "required": ["ticker", "days"],
        },
    },
    {
        "type": "function",
        "name": "get_chart_indicators",
        "description": (
            "Compute technical indicators for a stock ticker over the last N calendar days "
            "and return them as overlay data for an existing chart. "
            "Supports SMAs (e.g. 20, 50, 200), EMA (e.g. 20), Bollinger Bands, "
            "and key support/resistance levels. "
            "Use this when the user asks to add indicators, SMAs, EMAs, Bollinger Bands, "
            "support/resistance, or any overlay to a chart that is already on screen."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker symbol, e.g. AAPL, MSFT, TSLA",
                },
                "days": {
                    "type": "integer",
                    "description": "Number of calendar days of history (should match the existing chart)",
                },
                "indicators": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "List of indicators to compute. Examples: "
                        "'sma_20', 'sma_50', 'sma_200', 'ema_20', "
                        "'bollinger_20', 'support_resistance'"
                    ),
                },
            },
            "required": ["ticker", "days", "indicators"],
        },
    },
    {
        "type": "function",
        "name": "get_fundamentals",
        "description": (
            "Retrieve fundamental financial data for a stock ticker: valuation ratios, "
            "profitability metrics, growth figures, balance-sheet health, dividend info, "
            "and analyst consensus. Use this for questions about company value, earnings, "
            "margins, debt, or whether a stock looks cheap or expensive."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker symbol, e.g. AAPL, MSFT, TSLA",
                },
            },
            "required": ["ticker"],
        },
    },
]


# ── Helper: safely round a number or return None ──────────────────────
def _r(val, digits: int = 2):
    try:
        return round(float(val), digits) if val is not None else None
    except (TypeError, ValueError):
        return None


def _pct(val):
    """Convert a 0-1 fraction to a percentage, rounded to 2 dp."""
    try:
        return round(float(val) * 100, 2) if val is not None else None
    except (TypeError, ValueError):
        return None


# ── Tool implementations ──────────────────────────────────────────────
def get_stock_history(args: dict) -> str:
    """Fetch OHLCV history from Yahoo Finance and return it as a JSON string."""
    ticker = args["ticker"].upper()
    days = int(args["days"])
    end = date.today()
    start = end - timedelta(days=days)
    try:
        df = yf.download(
            ticker,
            start=start.isoformat(),
            end=end.isoformat(),
            auto_adjust=True,
            progress=False,
        )
        if df.empty:
            return json.dumps({"ticker": ticker, "error": "No data returned. Check the ticker symbol."})

        records = []
        for ts, row in df.iterrows():
            records.append(
                {
                    "date": ts.strftime("%Y-%m-%d"),
                    "open": round(float(row["Open"].iloc[0]), 2),
                    "high": round(float(row["High"].iloc[0]), 2),
                    "low": round(float(row["Low"].iloc[0]), 2),
                    "close": round(float(row["Close"].iloc[0]), 2),
                    "volume": int(row["Volume"].iloc[0]),
                }
            )

        closes = [r["close"] for r in records]
        return json.dumps(
            {
                "ticker": ticker,
                "period_start": records[0]["date"],
                "period_end": records[-1]["date"],
                "trading_days": len(records),
                "open_price": records[0]["open"],
                "latest_close": records[-1]["close"],
                "period_high": max(r["high"] for r in records),
                "period_low": min(r["low"] for r in records),
                "avg_volume": int(sum(r["volume"] for r in records) / len(records)),
                "pct_change": round((closes[-1] - closes[0]) / closes[0] * 100, 2),
                "daily_closes": {r["date"]: r["close"] for r in records},
            }
        )
    except Exception as e:
        return json.dumps({"ticker": ticker, "error": str(e)})


def get_fundamentals(args: dict) -> str:
    """Fetch fundamental data from Yahoo Finance and return it as a JSON string."""
    ticker = args["ticker"].upper()
    try:
        t = yf.Ticker(ticker)
        info = t.info or {}

        if not info or info.get("quoteType") is None:
            return json.dumps({"ticker": ticker, "error": "No fundamental data found. Check the ticker symbol."})

        result: dict = {"ticker": ticker}

        # ── Company info ───────────────────────────────────────────────
        result["name"] = info.get("longName") or info.get("shortName")
        result["sector"] = info.get("sector")
        result["industry"] = info.get("industry")
        result["market_cap"] = info.get("marketCap")
        result["currency"] = info.get("currency", "USD")

        # ── Valuation ──────────────────────────────────────────────────
        result["pe_trailing"] = _r(info.get("trailingPE"))
        result["pe_forward"] = _r(info.get("forwardPE"))
        result["peg_ratio"] = _r(info.get("pegRatio"))
        result["price_to_book"] = _r(info.get("priceToBook"))
        result["price_to_sales"] = _r(info.get("priceToSalesTrailing12Months"))
        result["ev_to_ebitda"] = _r(info.get("enterpriseToEbitda"))
        result["ev_to_revenue"] = _r(info.get("enterpriseToRevenue"))

        # ── Profitability ──────────────────────────────────────────────
        result["gross_margin"] = _pct(info.get("grossMargins"))
        result["operating_margin"] = _pct(info.get("operatingMargins"))
        result["net_margin"] = _pct(info.get("profitMargins"))
        result["roe"] = _pct(info.get("returnOnEquity"))
        result["roa"] = _pct(info.get("returnOnAssets"))

        # ── Growth ─────────────────────────────────────────────────────
        result["revenue_growth_yoy"] = _pct(info.get("revenueGrowth"))
        result["earnings_growth_yoy"] = _pct(info.get("earningsGrowth"))
        result["eps_trailing"] = _r(info.get("trailingEps"))
        result["eps_forward"] = _r(info.get("forwardEps"))

        # ── Financial health ───────────────────────────────────────────
        result["debt_to_equity"] = _r(info.get("debtToEquity"))
        result["current_ratio"] = _r(info.get("currentRatio"))
        result["quick_ratio"] = _r(info.get("quickRatio"))
        result["free_cash_flow"] = info.get("freeCashflow")
        result["total_cash"] = info.get("totalCash")
        result["total_debt"] = info.get("totalDebt")

        # ── Dividends ──────────────────────────────────────────────────
        result["dividend_yield"] = _pct(info.get("dividendYield"))
        result["payout_ratio"] = _pct(info.get("payoutRatio"))
        result["ex_dividend_date"] = info.get("exDividendDate")

        # ── Analyst consensus ──────────────────────────────────────────
        result["analyst_recommendation"] = info.get("recommendationKey")
        result["analyst_mean_rating"] = _r(info.get("recommendationMean"))
        result["analyst_count"] = info.get("numberOfAnalystOpinions")
        result["target_low"] = _r(info.get("targetLowPrice"))
        result["target_mean"] = _r(info.get("targetMeanPrice"))
        result["target_high"] = _r(info.get("targetHighPrice"))
        result["current_price"] = _r(info.get("currentPrice") or info.get("regularMarketPrice"))

        # ── 52-week range ──────────────────────────────────────────────
        result["week52_high"] = _r(info.get("fiftyTwoWeekHigh"))
        result["week52_low"] = _r(info.get("fiftyTwoWeekLow"))
        result["beta"] = _r(info.get("beta"))

        return json.dumps(result)
    except Exception as e:
        return json.dumps({"ticker": ticker, "error": str(e)})


def get_chart_indicators(args: dict) -> str:
    """Compute technical indicator overlays and return them as structured JSON."""
    ticker = args["ticker"].upper()
    days = int(args["days"])
    indicators: list[str] = args.get("indicators", [])
    # Fetch a wider window so rolling averages are warm at the start of the period
    extra_days = 250
    end = date.today()
    start = end - timedelta(days=days + extra_days)
    try:
        df = yf.download(
            ticker,
            start=start.isoformat(),
            end=end.isoformat(),
            auto_adjust=True,
            progress=False,
        )
        if df.empty:
            return json.dumps({"ticker": ticker, "error": "No data returned."})

        closes_series = df["Close"].squeeze()
        highs_series = df["High"].squeeze()
        lows_series = df["Low"].squeeze()

        # Trim to the requested window for output
        cutoff = end - timedelta(days=days)
        mask = df.index.date >= cutoff
        dates_in_window = [ts.strftime("%Y-%m-%d") for ts in df.index[mask]]

        result: dict = {"ticker": ticker, "overlays": {}}

        for ind in indicators:
            ind = ind.lower().strip()

            # ── SMA ───────────────────────────────────────────────────────
            if ind.startswith("sma_"):
                period = int(ind.split("_")[1])
                sma = closes_series.rolling(period).mean()
                sma_trimmed = sma[mask]
                result["overlays"][ind] = {
                    "type": "sma",
                    "period": period,
                    "data": {
                        ts.strftime("%Y-%m-%d"): round(float(v), 2)
                        for ts, v in zip(df.index[mask], sma_trimmed)
                        if not (v != v)  # drop NaN
                    },
                }

            # ── EMA ───────────────────────────────────────────────────────
            elif ind.startswith("ema_"):
                period = int(ind.split("_")[1])
                ema = closes_series.ewm(span=period, adjust=False).mean()
                ema_trimmed = ema[mask]
                result["overlays"][ind] = {
                    "type": "ema",
                    "period": period,
                    "data": {
                        ts.strftime("%Y-%m-%d"): round(float(v), 2)
                        for ts, v in zip(df.index[mask], ema_trimmed)
                        if not (v != v)
                    },
                }

            # ── Bollinger Bands ───────────────────────────────────────────
            elif ind.startswith("bollinger_"):
                period = int(ind.split("_")[1])
                mid = closes_series.rolling(period).mean()
                std = closes_series.rolling(period).std()
                upper = mid + 2 * std
                lower = mid - 2 * std
                result["overlays"][ind] = {
                    "type": "bollinger",
                    "period": period,
                    "mid": {
                        ts.strftime("%Y-%m-%d"): round(float(v), 2)
                        for ts, v in zip(df.index[mask], mid[mask])
                        if not (v != v)
                    },
                    "upper": {
                        ts.strftime("%Y-%m-%d"): round(float(v), 2)
                        for ts, v in zip(df.index[mask], upper[mask])
                        if not (v != v)
                    },
                    "lower": {
                        ts.strftime("%Y-%m-%d"): round(float(v), 2)
                        for ts, v in zip(df.index[mask], lower[mask])
                        if not (v != v)
                    },
                }

            # ── Support / Resistance ──────────────────────────────────────
            elif ind == "support_resistance":
                window_highs = highs_series[mask]
                window_lows = lows_series[mask]
                # Simple pivot-based levels: top 3 highs and bottom 3 lows
                sorted_highs = sorted(window_highs.dropna().tolist(), reverse=True)
                sorted_lows = sorted(window_lows.dropna().tolist())
                resistance_levels = [round(v, 2) for v in sorted_highs[:3]]
                support_levels = [round(v, 2) for v in sorted_lows[:3]]
                result["overlays"]["support_resistance"] = {
                    "type": "support_resistance",
                    "resistance": resistance_levels,
                    "support": support_levels,
                }

        result["dates_in_window"] = dates_in_window
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"ticker": ticker, "error": str(e)})


TOOL_DISPATCH: dict = {
    "get_stock_history": get_stock_history,
    "get_fundamentals": get_fundamentals,
    "get_chart_indicators": get_chart_indicators,
}
