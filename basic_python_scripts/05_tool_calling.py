#!/usr/bin/env python3
"""
05 — Function / tool calling  (Responses API)

Registers two real tools (get_weather via wttr.in, get_stock_price via
yfinance) and lets GPT-5.4 decide which one(s) to call, then feeds
back the live results.

Usage:
    python 05_tool_calling.py
"""

import json
import time

import requests
import yfinance as yf
from config import DEPLOYMENT, get_client
from rich import print as rprint
from rich.panel import Panel

client = get_client()

# ── Tool definitions ──────────────────────────────────────────────────
TOOLS = [
    {
        "type": "function",
        "name": "get_weather",
        "description": "Get the current weather for a city.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name"},
            },
            "required": ["city"],
        },
    },
    {
        "type": "function",
        "name": "get_stock_price",
        "description": "Get the current stock price for a ticker symbol.",
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Stock ticker, e.g. MSFT"},
            },
            "required": ["ticker"],
        },
    },
]


# ── Real tool implementations ────────────────────────────────────────
def get_weather(args: dict) -> str:
    """Fetch current weather from wttr.in (free, no API key)."""
    city = args["city"]
    try:
        resp = requests.get(
            f"https://wttr.in/{city}?format=j1", timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        current = data["current_condition"][0]
        return json.dumps({
            "city": city,
            "temp_f": current["temp_F"],
            "temp_c": current["temp_C"],
            "condition": current["weatherDesc"][0]["value"],
            "humidity": current["humidity"],
            "wind_mph": current["windspeedMiles"],
            "feels_like_f": current["FeelsLikeF"],
        })
    except Exception as e:
        return json.dumps({"city": city, "error": str(e)})


def get_stock_price(args: dict) -> str:
    """Fetch current stock price from Yahoo Finance via yfinance."""
    ticker = args["ticker"].upper()
    try:
        stock = yf.Ticker(ticker)
        info = stock.fast_info
        return json.dumps({
            "ticker": ticker,
            "price": round(info.last_price, 2),
            "currency": info.currency,
            "day_high": round(info.day_high, 2),
            "day_low": round(info.day_low, 2),
            "market_cap": info.market_cap,
        })
    except Exception as e:
        return json.dumps({"ticker": ticker, "error": str(e)})


TOOL_DISPATCH = {
    "get_weather": get_weather,
    "get_stock_price": get_stock_price,
}

# ── Get user input ────────────────────────────────────────────────────
city = input("Enter a city for weather info: ").strip() or "Seattle"
ticker = input("Enter a stock ticker: ").strip().upper() or "MSFT"
user_query = f"What's the current weather in {city} and the stock price of {ticker}?"
rprint(f"\n[bold]Query:[/bold] {user_query}\n")

# ── Step 1: ask the model ────────────────────────────────────────────
t0 = time.perf_counter()
response = client.responses.create(
    model=DEPLOYMENT,
    input=user_query,
    tools=TOOLS,
)

# ── Step 2: handle tool calls ────────────────────────────────────────
tool_outputs = []
for item in response.output:
    if item.type == "function_call":
        fn = TOOL_DISPATCH[item.name]
        args = json.loads(item.arguments)
        result = fn(args)
        rprint(f"[yellow]Tool call → {item.name}({args}) = {result}[/yellow]")
        tool_outputs.append(
            {
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": result,
            }
        )

# ── Step 3: feed results back ────────────────────────────────────────
followup = client.responses.create(
    model=DEPLOYMENT,
    input=tool_outputs,
    previous_response_id=response.id,
)

elapsed = time.perf_counter() - t0

rprint(Panel(followup.output_text, title="Final Answer (with live data)"))
rprint(f"[dim]Total tokens — turn 1: {response.usage.total_tokens}  "
       f"turn 2: {followup.usage.total_tokens}[/dim]")
rprint(f"[dim]Elapsed: {elapsed:.1f}s[/dim]")
