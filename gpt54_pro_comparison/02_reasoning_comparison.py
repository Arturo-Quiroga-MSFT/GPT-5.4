#!/usr/bin/env python3
"""
02 — Reasoning Comparison: GPT-5.4 vs GPT-5.4-pro

Sends the same logic puzzle to both models at multiple reasoning effort
levels, comparing depth of reasoning, answer quality, and token costs.
"""

import time
from config import MODELS, MODEL_STYLES, get_client
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
client = get_client()

PROMPT = (
    "A farmer has 17 sheep. All but 9 run away. "
    "How many sheep does the farmer have left? Explain step by step."
)

EFFORTS = ["low", "medium", "high"]
results = []

for model in MODELS:
    style = MODEL_STYLES[model]
    for effort in EFFORTS:
        console.print(f"[{style}]{model} (effort={effort})…[/{style}]")
        t0 = time.perf_counter()
        resp = client.responses.create(
            model=model,
            input=PROMPT,
            reasoning={"effort": effort},
        )
        elapsed = time.perf_counter() - t0
        results.append({
            "model": model,
            "effort": effort,
            "text": resp.output_text,
            "input_tokens": resp.usage.input_tokens,
            "output_tokens": resp.usage.output_tokens,
            "reasoning_tokens": getattr(resp.usage, "reasoning_tokens", 0),
            "latency": elapsed,
        })

# ── Display responses ────────────────────────────────────────────────
for r in results:
    border = MODEL_STYLES[r["model"]].split()[-1]
    console.print(Panel(
        r["text"],
        title=f"{r['model']} — effort={r['effort']}",
        border_style=border,
    ))

# ── Summary table ────────────────────────────────────────────────────
table = Table(title="Reasoning Effort Comparison")
table.add_column("Model", style="cyan")
table.add_column("Effort", justify="center")
table.add_column("Input tok", justify="right")
table.add_column("Output tok", justify="right")
table.add_column("Reasoning tok", justify="right")
table.add_column("Latency (s)", justify="right")

for r in results:
    table.add_row(
        r["model"],
        r["effort"],
        str(r["input_tokens"]),
        str(r["output_tokens"]),
        str(r["reasoning_tokens"]),
        f"{r['latency']:.1f}",
    )

console.print(table)
