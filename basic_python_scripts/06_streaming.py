#!/usr/bin/env python3
"""
06 — Streaming responses  (Responses API)

Streams GPT-5.4 output token-by-token to the terminal, showing
real-time generation including reasoning summary events.
"""

import time
from config import DEPLOYMENT, get_client
from rich.console import Console

console = Console()
client = get_client()

PROMPT = (
    "Write a short poem (4 lines) about the beauty of reasoning "
    "in artificial intelligence."
)

console.print("[bold]Streaming GPT-5.4 response…[/bold]\n")

t0 = time.perf_counter()
stream = client.responses.create(
    model=DEPLOYMENT,
    input=PROMPT,
    reasoning={"effort": "high", "summary": "auto"},
    stream=True,
)

in_reasoning = False

for event in stream:
    # Output text deltas
    if event.type == "response.output_text.delta":
        if in_reasoning:
            console.print("\n")  # blank line after reasoning summary
            in_reasoning = False
        console.print(event.delta, end="", highlight=False)

    # Reasoning summary deltas (when summary is enabled)
    elif event.type == "response.reasoning_summary_text.delta":
        in_reasoning = True
        console.print(f"[dim italic]{event.delta}[/dim italic]", end="")

    # Stream completed
    elif event.type == "response.completed":
        elapsed = time.perf_counter() - t0
        console.print()  # newline
        usage = event.response.usage
        console.print(
            f"\n[dim]Tokens — input: {usage.input_tokens}  "
            f"output: {usage.output_tokens}  "
            f"total: {usage.total_tokens}[/dim]"
        )
        console.print(f"[dim]Elapsed: {elapsed:.1f}s[/dim]")
