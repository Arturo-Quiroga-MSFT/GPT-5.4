#!/usr/bin/env python3
"""
05 — Streaming Comparison: GPT-5.4 vs GPT-5.4-pro

Streams responses from both models token-by-token, measuring
time-to-first-token (TTFT) and total latency.
"""

import time
from config import MODELS, MODEL_STYLES, get_client
from rich.console import Console
from rich.table import Table

console = Console()
client = get_client()

PROMPT = (
    "Write a short poem (4 lines) about the beauty of reasoning "
    "in artificial intelligence."
)

results = []

for model in MODELS:
    style = MODEL_STYLES[model]
    console.print(f"\n[{style}]═══ {model} streaming ═══[/{style}]\n")

    t0 = time.perf_counter()
    ttft = None
    full_text = ""

    stream = client.responses.create(
        model=model,
        input=PROMPT,
        reasoning={"effort": "high", "summary": "auto"},
        stream=True,
    )

    for event in stream:
        if event.type == "response.output_text.delta":
            if ttft is None:
                ttft = time.perf_counter() - t0
            console.print(event.delta, end="", highlight=False)
            full_text += event.delta
        elif event.type == "response.completed":
            elapsed = time.perf_counter() - t0
            usage = event.response.usage
            results.append({
                "model": model,
                "ttft": ttft or 0,
                "total": elapsed,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
            })

    console.print("\n")

# ── Summary ───────────────────────────────────────────────────────────
table = Table(title="Streaming Comparison")
table.add_column("Model", style="cyan")
table.add_column("TTFT (s)", justify="right")
table.add_column("Total (s)", justify="right")
table.add_column("Input tok", justify="right")
table.add_column("Output tok", justify="right")

for r in results:
    table.add_row(
        r["model"],
        f"{r['ttft']:.2f}",
        f"{r['total']:.1f}",
        str(r["input_tokens"]),
        str(r["output_tokens"]),
    )

console.print(table)
