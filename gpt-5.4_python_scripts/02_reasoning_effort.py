#!/usr/bin/env python3
"""
02 — Reasoning-effort sweep  (Responses API)

Sends the same prompt at each reasoning_effort level (none → xhigh)
so you can compare quality, latency, and token cost side-by-side.
"""

import time
from config import DEPLOYMENT, REASONING_EFFORTS, get_client
from rich.console import Console
from rich.table import Table

console = Console()
client = get_client()

PROMPT = (
    "A farmer has 17 sheep. All but 9 run away. "
    "How many sheep does the farmer have left? Explain step by step."
)

table = Table(title="Reasoning-Effort Comparison")
table.add_column("Effort", style="cyan")
table.add_column("Answer (truncated)", max_width=60)
table.add_column("Input tok", justify="right")
table.add_column("Output tok", justify="right")
table.add_column("Latency (s)", justify="right")

for effort in REASONING_EFFORTS:
    t0 = time.perf_counter()

    response = client.responses.create(
        model=DEPLOYMENT,
        input=PROMPT,
        reasoning={"effort": effort},
    )

    elapsed = time.perf_counter() - t0
    answer = response.output_text.replace("\n", " ")[:120] + "…"

    table.add_row(
        effort,
        answer,
        str(response.usage.input_tokens),
        str(response.usage.output_tokens),
        f"{elapsed:.1f}",
    )

console.print(table)
