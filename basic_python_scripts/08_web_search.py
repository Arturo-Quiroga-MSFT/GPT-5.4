#!/usr/bin/env python3
"""
08 — Web search grounding  (Responses API)

Uses the built-in web_search tool so GPT-5.4 can ground its answer
in live web results (BrowseComp SOTA: 82.7%).
"""

import time
from config import DEPLOYMENT, get_client
from rich import print as rprint
from rich.panel import Panel

client = get_client()

t0 = time.perf_counter()
response = client.responses.create(
    model=DEPLOYMENT,
    input="What are the latest announcements from the war in Iran, and attacks on Lebanon, today?",
    tools=[{"type": "web_search_preview"}],
)

rprint(Panel(response.output_text, title="Web-Grounded Answer"))

# Show citations if present
for item in response.output:
    if hasattr(item, "type") and item.type == "message":
        for block in getattr(item, "content", []):
            if hasattr(block, "annotations"):
                for ann in block.annotations:
                    rprint(f"  [dim]↳ {ann.url}[/dim]")

elapsed = time.perf_counter() - t0

rprint(f"\n[dim]Tokens — input: {response.usage.input_tokens}  "
       f"output: {response.usage.output_tokens}[/dim]")
rprint(f"[dim]Elapsed: {elapsed:.1f}s[/dim]")
