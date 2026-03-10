"""
Stock data service.

Provides the get_stock_history tool used by the LLM and its TOOLS / TOOL_DISPATCH
definitions so the same tool spec can be registered with the model and called
locally without duplication.
"""

import json
from datetime import date, timedelta

import yfinance as yf


# ── Tool schema (registered with the model) ───────────────────────────
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
    }
]


# ── Tool implementation ───────────────────────────────────────────────
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


TOOL_DISPATCH: dict = {"get_stock_history": get_stock_history}
