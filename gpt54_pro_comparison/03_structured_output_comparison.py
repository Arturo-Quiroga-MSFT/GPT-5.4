#!/usr/bin/env python3
"""
03 — Structured Output Comparison: GPT-5.4 vs GPT-5.4-pro

Both models use native JSON schema enforcement via the Responses API.
Measures schema compliance, token usage, and latency.
"""

import json
import time
from config import MODELS, MODEL_STYLES, get_client
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
client = get_client()

PROMPT = "Give me 3 interesting cities in South America with population and a fun fact."

SCHEMA = {
    "type": "object",
    "properties": {
        "cities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name":       {"type": "string"},
                    "country":    {"type": "string"},
                    "population": {"type": "integer"},
                    "fun_fact":   {"type": "string"},
                },
                "required": ["name", "country", "population", "fun_fact"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["cities"],
    "additionalProperties": False,
}

results = []

for model in MODELS:
    style = MODEL_STYLES[model]
    console.print(f"[{style}]{model} (JSON schema)…[/{style}]")
    t0 = time.perf_counter()
    resp = client.responses.create(
        model=model,
        input=PROMPT,
        text={
            "format": {
                "type": "json_schema",
                "name": "city_comparison",
                "schema": SCHEMA,
                "strict": True,
            }
        },
    )
    elapsed = time.perf_counter() - t0

    valid = False
    data = None
    try:
        data = json.loads(resp.output_text)
        valid = True
    except json.JSONDecodeError:
        pass

    results.append({
        "model": model,
        "data": data,
        "input_tokens": resp.usage.input_tokens,
        "output_tokens": resp.usage.output_tokens,
        "latency": elapsed,
        "valid_json": valid,
    })

# ── Display ───────────────────────────────────────────────────────────
for r in results:
    border = MODEL_STYLES[r["model"]].split()[-1]
    console.print(Panel(
        json.dumps(r["data"], indent=2, ensure_ascii=False) if r["data"] else "No structured output",
        title=f"{r['model']} — valid={r['valid_json']}",
        border_style=border if r["valid_json"] else "red",
    ))

table = Table(title="Structured Output Comparison")
table.add_column("Model", style="cyan")
table.add_column("Valid JSON", justify="center")
table.add_column("Input tok", justify="right")
table.add_column("Output tok", justify="right")
table.add_column("Latency (s)", justify="right")

for r in results:
    table.add_row(
        r["model"],
        "✓" if r["valid_json"] else "✗",
        str(r["input_tokens"]),
        str(r["output_tokens"]),
        f"{r['latency']:.1f}",
    )

console.print(table)
