#!/usr/bin/env python3
"""
01 — Hello Comparison: GPT-5.4 vs GPT-5.4-pro

Sends the same prompt to both models and compares response quality,
token usage, and latency side-by-side.
"""

import time
from config import MODELS, MODEL_STYLES, get_client
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
client = get_client()

PROMPT = "Hello! Tell me one fascinating fact about reasoning models."

results = []

for model in MODELS:
    style = MODEL_STYLES[model]
    console.print(f"[{style}]Calling {model}…[/{style}]")
    t0 = time.perf_counter()
    resp = client.responses.create(model=model, input=PROMPT)
    elapsed = time.perf_counter() - t0
    results.append({
        "model": model,
        "text": resp.output_text,
        "input_tokens": resp.usage.input_tokens,
        "output_tokens": resp.usage.output_tokens,
        "latency": elapsed,
    })

# ── Display ───────────────────────────────────────────────────────────
for r in results:
    border = MODEL_STYLES[r["model"]].split()[-1]  # "cyan" or "green"
    console.print(Panel(r["text"], title=r["model"], border_style=border))

table = Table(title="Hello — Comparison Summary")
table.add_column("Model", style="cyan")
table.add_column("Input tok", justify="right")
table.add_column("Output tok", justify="right")
table.add_column("Latency (s)", justify="right")

for r in results:
    table.add_row(
        r["model"],
        str(r["input_tokens"]),
        str(r["output_tokens"]),
        f"{r['latency']:.1f}",
    )

console.print(table)
