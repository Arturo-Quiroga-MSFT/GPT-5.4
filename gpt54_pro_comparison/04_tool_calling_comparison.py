#!/usr/bin/env python3
"""
04 — Tool Calling Comparison: GPT-5.4 vs GPT-5.4-pro

Both models are given the same tool definitions (get_weather, get_stock_price)
and must decide which tools to call.  Comparing tool selection accuracy,
argument quality, and total round-trip latency.
"""

import json
import time

import requests
import yfinance as yf
from config import MODELS, MODEL_STYLES, get_client
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
client = get_client()

# ── Tool definitions (OpenAI Responses API format) ────────────────────
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


# ── Real tool implementations ─────────────────────────────────────────
def get_weather(args: dict) -> str:
    city = args["city"]
    try:
        # Step 1: geocode city → lat/lon via Open-Meteo geocoding API
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "en", "format": "json"},
            timeout=10,
        )
        geo.raise_for_status()
        geo_data = geo.json()
        if not geo_data.get("results"):
            return json.dumps({"city": city, "error": "City not found"})
        loc = geo_data["results"][0]
        lat, lon = loc["latitude"], loc["longitude"]

        # Step 2: fetch current weather from Open-Meteo
        wx = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
                "temperature_unit": "celsius",
                "wind_speed_unit": "mph",
                "timezone": "auto",
            },
            timeout=10,
        )
        wx.raise_for_status()
        cur = wx.json()["current"]
        temp_c = cur["temperature_2m"]
        temp_f = round(temp_c * 9 / 5 + 32, 1)
        return json.dumps({
            "city": loc["name"],
            "country": loc.get("country", ""),
            "temp_c": temp_c,
            "temp_f": temp_f,
            "humidity": cur["relative_humidity_2m"],
            "wind_mph": cur["wind_speed_10m"],
            "weather_code": cur["weather_code"],
        })
    except Exception as e:
        return json.dumps({"city": city, "error": str(e)})


def get_stock_price(args: dict) -> str:
    ticker = args["ticker"].upper()
    try:
        stock = yf.Ticker(ticker)
        info = stock.fast_info
        return json.dumps({
            "ticker": ticker, "price": round(info.last_price, 2),
            "currency": info.currency,
        })
    except Exception as e:
        return json.dumps({"ticker": ticker, "error": str(e)})


TOOL_DISPATCH = {"get_weather": get_weather, "get_stock_price": get_stock_price}

# ── User query ────────────────────────────────────────────────────────
city = input("Enter a city for weather info: ").strip() or "Seattle"
ticker = input("Enter a stock ticker: ").strip().upper() or "MSFT"
user_query = f"What's the current weather in {city} and the stock price of {ticker}?"
console.print(f"\n[bold]Query:[/bold] {user_query}\n")

results = []

for model in MODELS:
    style = MODEL_STYLES[model]
    console.print(f"[{style}]{model} — tool calling…[/{style}]")
    t0 = time.perf_counter()

    # First call: let the model select and invoke tools
    resp = client.responses.create(model=model, input=user_query, tools=TOOLS)

    tool_outputs = []
    tools_called = []
    for item in resp.output:
        if item.type == "function_call":
            fn = TOOL_DISPATCH[item.name]
            args = json.loads(item.arguments)
            result = fn(args)
            tools_called.append(item.name)
            tool_outputs.append({
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": result,
            })

    # Second call: feed tool results back to get the final answer
    final = client.responses.create(
        model=model,
        input=resp.output + tool_outputs,
        tools=TOOLS,
    )
    elapsed = time.perf_counter() - t0

    results.append({
        "model": model,
        "text": final.output_text,
        "tools_called": tools_called,
        "input_tokens": resp.usage.input_tokens + final.usage.input_tokens,
        "output_tokens": resp.usage.output_tokens + final.usage.output_tokens,
        "latency": elapsed,
    })

# ── Display ───────────────────────────────────────────────────────────
for r in results:
    border = MODEL_STYLES[r["model"]].split()[-1]
    console.print(Panel(
        r["text"],
        title=f"{r['model']} (tools: {', '.join(r['tools_called'])})",
        border_style=border,
    ))

table = Table(title="Tool Calling Comparison")
table.add_column("Model", style="cyan")
table.add_column("Tools Called", style="yellow")
table.add_column("Input tok", justify="right")
table.add_column("Output tok", justify="right")
table.add_column("Latency (s)", justify="right")

for r in results:
    table.add_row(
        r["model"],
        ", ".join(r["tools_called"]) or "—",
        str(r["input_tokens"]),
        str(r["output_tokens"]),
        f"{r['latency']:.1f}",
    )

console.print(table)
