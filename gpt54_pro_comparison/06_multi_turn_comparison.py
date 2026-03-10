#!/usr/bin/env python3
"""
06 — Multi-Turn Comparison: GPT-5.4 vs GPT-5.4-pro

Runs the same 3-turn conversation through both models, comparing
how well each maintains context across turns.

Both models use `previous_response_id` for context chaining via the
Azure OpenAI Responses API.
"""

import time
from config import MODELS, MODEL_STYLES, get_client
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
client = get_client()

SYSTEM = (
    "You are a helpful assistant that specialises in explaining "
    "complex AI concepts simply."
)

TURNS = [
    "What is chain-of-thought reasoning in language models?",
    "How does that differ from traditional prompting?",
    "Can you give a concrete example with a math problem?",
]

all_results = {}

for model in MODELS:
    style = MODEL_STYLES[model]
    console.print(f"\n[{style}]═══ {model} Multi-Turn ═══[/{style}]")

    prev_id = None
    turn_results = []

    for i, user_msg in enumerate(TURNS, 1):
        console.print(f"\n[bold]Turn {i}:[/bold] {user_msg}")
        kwargs = {"model": model, "input": user_msg, "instructions": SYSTEM}
        if prev_id:
            kwargs["previous_response_id"] = prev_id

        t0 = time.perf_counter()
        resp = client.responses.create(**kwargs)
        elapsed = time.perf_counter() - t0
        prev_id = resp.id

        border = style.split()[-1]
        console.print(Panel(
            resp.output_text[:400] + ("…" if len(resp.output_text) > 400 else ""),
            title=f"{model} — Turn {i}",
            border_style=border,
        ))
        turn_results.append({
            "turn": i,
            "input_tokens": resp.usage.input_tokens,
            "output_tokens": resp.usage.output_tokens,
            "latency": elapsed,
        })

    all_results[model] = turn_results

    # Per-model turn-by-turn table
    table = Table(title=f"{model} — Turn-by-Turn Stats")
    table.add_column("Turn", justify="center")
    table.add_column("Input tok", justify="right")
    table.add_column("Output tok", justify="right")
    table.add_column("Latency (s)", justify="right")
    for r in turn_results:
        table.add_row(
            str(r["turn"]),
            str(r["input_tokens"]),
            str(r["output_tokens"]),
            f"{r['latency']:.1f}",
        )
    console.print(table)

# ── Cross-model totals ────────────────────────────────────────────────
console.print("\n")
summary = Table(title="Multi-Turn Totals Comparison")
summary.add_column("Model", style="cyan")
summary.add_column("Total Input tok", justify="right")
summary.add_column("Total Output tok", justify="right")
summary.add_column("Total Latency (s)", justify="right")

for model, results in all_results.items():
    summary.add_row(
        model,
        str(sum(r["input_tokens"] for r in results)),
        str(sum(r["output_tokens"] for r in results)),
        f"{sum(r['latency'] for r in results):.1f}",
    )

console.print(summary)
