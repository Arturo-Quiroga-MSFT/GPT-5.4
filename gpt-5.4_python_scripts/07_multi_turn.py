#!/usr/bin/env python3
"""
07 — Multi-turn conversation  (Responses API)

Demonstrates how to chain turns using `previous_response_id` so the
model retains full conversation context without resending messages.
Also shows how to set a system/developer instruction.
"""

import time
from config import DEPLOYMENT, get_client
from rich import print as rprint
from rich.panel import Panel

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

prev_id = None

for i, user_msg in enumerate(TURNS, 1):
    rprint(f"\n[bold cyan]Turn {i}:[/bold cyan] {user_msg}")

    kwargs = {
        "model": DEPLOYMENT,
        "input": user_msg,
        "instructions": SYSTEM,
    }
    if prev_id:
        kwargs["previous_response_id"] = prev_id

    t0 = time.perf_counter()
    response = client.responses.create(**kwargs)
    elapsed = time.perf_counter() - t0
    prev_id = response.id

    rprint(Panel(response.output_text, title=f"GPT-5.4 — Turn {i}"))
    rprint(f"[dim]Tokens — input: {response.usage.input_tokens}  "
           f"output: {response.usage.output_tokens}[/dim]")
    rprint(f"[dim]Elapsed: {elapsed:.1f}s[/dim]")
