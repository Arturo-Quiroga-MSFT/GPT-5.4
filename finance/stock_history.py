#!/usr/bin/env python3
"""
stock_history.py — Stock price history via GPT-5.4 + tool calling

GPT-5.4 drives the conversation: it calls `get_stock_history` to fetch
OHLCV data for a user-supplied ticker over a user-supplied number of days,
then returns a rich analysis (trend, highs/lows, volatility, summary).

Usage:
    python stock_history.py
"""

import json
import sys
import os
from time import sleep
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import yfinance as yf
from config import DEPLOYMENT, get_client
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
client = get_client()

# ── Tool definition ───────────────────────────────────────────────────
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
    ticker = args["ticker"].upper()
    days = int(args["days"])
    end = date.today()
    start = end - timedelta(days=days)
    try:
        df = yf.download(ticker, start=start.isoformat(), end=end.isoformat(),
                         auto_adjust=True, progress=False)
        if df.empty:
            return json.dumps({"ticker": ticker, "error": "No data returned. Check the ticker symbol."})

        records = []
        for ts, row in df.iterrows():
            records.append({
                "date": ts.strftime("%Y-%m-%d"),
                "open":   round(float(row["Open"].iloc[0]),   2),
                "high":   round(float(row["High"].iloc[0]),   2),
                "low":    round(float(row["Low"].iloc[0]),     2),
                "close":  round(float(row["Close"].iloc[0]),  2),
                "volume": int(row["Volume"].iloc[0]),
            })

        closes = [r["close"] for r in records]
        return json.dumps({
            "ticker":      ticker,
            "period_start": records[0]["date"],
            "period_end":   records[-1]["date"],
            "trading_days": len(records),
            "open_price":   records[0]["open"],
            "latest_close": records[-1]["close"],
            "period_high":  max(r["high"]  for r in records),
            "period_low":   min(r["low"]   for r in records),
            "avg_volume":   int(sum(r["volume"] for r in records) / len(records)),
            "pct_change":   round((closes[-1] - closes[0]) / closes[0] * 100, 2),
            "daily_closes": {r["date"]: r["close"] for r in records},
        })
    except Exception as e:
        return json.dumps({"ticker": ticker, "error": str(e)})


TOOL_DISPATCH = {"get_stock_history": get_stock_history}

# ── User input ────────────────────────────────────────────────────────
ticker_input = input("Enter stock ticker (e.g. AAPL): ").strip().upper() or "AAPL"
days_input   = input("Enter number of days to look back (e.g. 30): ").strip() or "30"

user_query = (
    f"Retrieve and analyse the stock price history for {ticker_input} "
    f"over the last {days_input} days. Give me: the opening and latest close price, "
    f"the period high and low, overall % change, average daily volume, "
    f"and a brief commentary on the trend."
)
console.print(f"\n[bold]Query:[/bold] {user_query}\n")

# ── First call: model decides to use the tool ─────────────────────────
console.print(f"[bold cyan]Calling {DEPLOYMENT}…[/bold cyan]")
resp = client.responses.create(model=DEPLOYMENT, input=user_query, tools=TOOLS)

tool_outputs = []
history_data = None
for item in resp.output:
    if item.type == "function_call":
        console.print(f"  [dim]→ tool call: {item.name}({item.arguments})[/dim]")
        result = TOOL_DISPATCH[item.name](json.loads(item.arguments))
        console.print(f"  [dim]← tool result received[/dim]")
        if item.name == "get_stock_history":
            history_data = json.loads(result)
        tool_outputs.append({
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": result,
        })

# ── Second call: model synthesises the analysis ───────────────────────
final = client.responses.create(
    model=DEPLOYMENT,
    input=resp.output + tool_outputs,
    tools=TOOLS,
)

console.print(Panel(
    final.output_text,
    title=f"[bold cyan]{ticker_input} — {days_input}-day Analysis[/bold cyan]",
    border_style="cyan",
))

# ── Token / latency summary ───────────────────────────────────────────
table = Table(title="Usage Summary", show_header=True)
table.add_column("Call", style="dim")
table.add_column("Input tok", justify="right")
table.add_column("Output tok", justify="right")

table.add_row("Tool call",     str(resp.usage.input_tokens),  str(resp.usage.output_tokens))
table.add_row("Final answer",  str(final.usage.input_tokens), str(final.usage.output_tokens))
table.add_row(
    "[bold]Total[/bold]",
    str(resp.usage.input_tokens  + final.usage.input_tokens),
    str(resp.usage.output_tokens + final.usage.output_tokens),
)

console.print(table)

# ── Full close history table ──────────────────────────────────────────
if history_data and "daily_closes" in history_data and not history_data.get("error"):
    closes = history_data["daily_closes"]
    first_close = list(closes.values())[0]

    history_table = Table(
        title=f"{history_data['ticker']} — Daily Close Prices "
              f"({history_data['period_start']} → {history_data['period_end']})",
        show_header=True,
    )
    history_table.add_column("Date", style="dim", width=12)
    history_table.add_column("Close (USD)", justify="right")
    history_table.add_column("Day Δ", justify="right")
    history_table.add_column("Cumulative Δ", justify="right")

    prev = first_close
    for date_str, close in closes.items():
        day_chg = close - prev
        cum_chg = close - first_close
        day_color  = "green" if day_chg >= 0 else "red"
        cum_color  = "green" if cum_chg >= 0 else "red"
        history_table.add_row(
            date_str,
            f"${close:.2f}",
            f"[{day_color}]{day_chg:+.2f}[/{day_color}]",
            f"[{cum_color}]{cum_chg:+.2f}[/{cum_color}]",
        )
        prev = close

    console.print(history_table)

# ── Line chart ────────────────────────────────────────────────────────
if history_data and "daily_closes" in history_data and not history_data.get("error"):
    from datetime import datetime
    closes = history_data["daily_closes"]
    dates  = [datetime.strptime(d, "%Y-%m-%d") for d in closes]
    prices = list(closes.values())

    pct    = history_data["pct_change"]
    color  = "#2ecc71" if pct >= 0 else "#e74c3c"

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(dates, prices, color=color, linewidth=2, marker="o", markersize=4, zorder=3)
    ax.fill_between(dates, prices, min(prices), alpha=0.12, color=color)

    # Period high / low reference lines
    ax.axhline(history_data["period_high"], color="#2ecc71", linewidth=0.8,
               linestyle="--", label=f"High ${history_data['period_high']:.2f}")
    ax.axhline(history_data["period_low"],  color="#e74c3c", linewidth=0.8,
               linestyle="--", label=f"Low  ${history_data['period_low']:.2f}")

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"${y:,.2f}"))
    plt.xticks(rotation=45, ha="right")

    ticker  = history_data["ticker"]
    sign    = "+" if pct >= 0 else ""
    ax.set_title(
        f"{ticker} — Closing Price  "
        f"({history_data['period_start']} → {history_data['period_end']})  "
        f"[{sign}{pct:.2f}%]",
        fontsize=13, fontweight="bold",
    )
    ax.set_ylabel("Close Price (USD)")
    ax.legend(fontsize=9)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.grid(axis="x", linestyle=":",  alpha=0.3)
    fig.tight_layout()

    out_path = os.path.join(os.path.dirname(__file__), f"{ticker}_close_chart.png")
    fig.savefig(out_path, dpi=150)
    plt.show()
    sleep(0.5)  # ensure the plot window has time to render before closing
    plt.close(fig)
    console.print(f"\n[bold green]Chart saved →[/bold green] {out_path}")
