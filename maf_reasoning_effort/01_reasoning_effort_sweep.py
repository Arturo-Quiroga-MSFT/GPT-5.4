#!/usr/bin/env python3
"""
01 — Reasoning-effort sweep with Microsoft Agent Framework.

MAF equivalent of `gpt-5.4_python_scripts/02_reasoning_effort.py`.

Demonstrates that MAF *does* support model-side controls like
`reasoning_effort`: pass them through the `options=` argument
(a TypedDict) on `ChatClient.get_response(...)` or `Agent.run(...)`.
"""

from __future__ import annotations

import asyncio
import time

from agent_framework import Message
from rich.console import Console
from rich.table import Table

from config import REASONING_EFFORTS, get_chat_client

PROMPT = (
    "A farmer has 17 sheep. All but 9 run away. "
    "How many sheep does the farmer have left? Explain step by step."
)


async def main() -> None:
    console = Console()
    client = get_chat_client()

    table = Table(title="MAF — Reasoning-Effort Comparison")
    table.add_column("Effort", style="cyan")
    table.add_column("Answer (truncated)", max_width=60)
    table.add_column("Input tok", justify="right")
    table.add_column("Output tok", justify="right")
    table.add_column("Latency (s)", justify="right")

    for effort in REASONING_EFFORTS:
        t0 = time.perf_counter()

        response = await client.get_response(
            [Message("user", contents=[PROMPT])],
            options={"reasoning": {"effort": effort}},
        )

        elapsed = time.perf_counter() - t0
        answer = (response.text or "").replace("\n", " ")[:120] + "…"

        usage = response.usage_details or {}
        in_tok = usage.get("input_token_count", 0) or 0
        out_tok = usage.get("output_token_count", 0) or 0

        table.add_row(effort, answer, str(in_tok), str(out_tok), f"{elapsed:.1f}")

    console.print(table)


if __name__ == "__main__":
    asyncio.run(main())
