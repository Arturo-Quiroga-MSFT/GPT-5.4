#!/usr/bin/env python3
"""
01 — Hello GPT-5.4  (Responses API)

Minimal smoke-test: send a single prompt via the Responses API
and print the reply along with token-usage metadata.
"""

import time
from config import DEPLOYMENT, get_client
from rich import print as rprint
from rich.panel import Panel

client = get_client()

t0 = time.perf_counter()
response = client.responses.create(
    model=DEPLOYMENT,
    input="Hello! Tell me one fascinating fact about reasoning models.",
)

elapsed = time.perf_counter() - t0

# ── Display ───────────────────────────────────────────────────────────
rprint(Panel(response.output_text, title="GPT-5.4 says"))
rprint(f"[dim]Model: {response.model}[/dim]")
rprint(f"[dim]Usage — input: {response.usage.input_tokens}  "
       f"output: {response.usage.output_tokens}  "
       f"total: {response.usage.total_tokens}[/dim]")
rprint(f"[dim]Elapsed: {elapsed:.1f}s[/dim]")
