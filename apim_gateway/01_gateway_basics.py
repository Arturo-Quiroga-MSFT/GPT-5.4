#!/usr/bin/env python3
"""
01 — Gateway basics

Smoke-test that the APIM gateway is correctly routing to the
Foundry / Azure OpenAI backend.  Sends a single prompt and prints:

  • The model's reply
  • Token usage
  • Latency
  • Key APIM response headers that confirm the gateway is in the path
    (x-ms-region, x-request-id, x-ms-rai-invoked, etc.)

The OpenAI SDK does not expose raw response headers directly, so we
make a second lightweight raw request (using httpx, which the SDK
already depends on) to capture them for inspection.

Usage:
    cd apim_gateway
    python 01_gateway_basics.py
"""

import time
import httpx
from config import APIM_BASE_URL, APIM_SUBSCRIPTION_KEY, DEPLOYMENT, get_client
from rich import print as rprint
from rich.panel import Panel
from rich.table import Table
from rich.console import Console

console = Console()

# ── 1. Normal SDK call through the gateway ────────────────────────────
client = get_client()

rprint("[bold]Sending request through APIM gateway…[/bold]")
t0 = time.perf_counter()

response = client.responses.create(
    model=DEPLOYMENT,
    input="In one sentence, explain what Azure API Management does.",
)

elapsed = time.perf_counter() - t0

rprint(Panel(response.output_text, title=f"[green]{response.model}[/green] via APIM"))
rprint(f"[dim]Usage — input: {response.usage.input_tokens}  "
       f"output: {response.usage.output_tokens}  "
       f"total: {response.usage.total_tokens}[/dim]")
rprint(f"[dim]Latency: {elapsed:.2f}s[/dim]")

# ── 2. Raw request to capture APIM response headers ───────────────────
# We replicate a minimal chat-completions body and inspect what headers
# APIM injects on the response.  These headers are the "fingerprint"
# proving the gateway is in the path rather than a direct AOAI call.

rprint("\n[bold]Checking APIM response headers…[/bold]")

raw_url = f"{APIM_BASE_URL}responses"
headers = {
    "Ocp-Apim-Subscription-Key": APIM_SUBSCRIPTION_KEY,
    "Content-Type": "application/json",
    "api-key": "apim-managed",
}
body = {
    "model": DEPLOYMENT,
    "input": "ping",
    "max_output_tokens": 5,
}

try:
    with httpx.Client(timeout=30) as http:
        raw = http.post(raw_url, headers=headers, json=body)

    # Headers of interest — APIM / Azure OpenAI typically inject these
    APIM_HEADERS = [
        "x-ms-region",
        "x-request-id",
        "x-ms-rai-invoked",
        "x-ratelimit-remaining-requests",
        "x-ratelimit-remaining-tokens",
        "apim-request-id",
        "x-envoy-upstream-service-time",
    ]

    table = Table(title="APIM Response Headers", show_header=True)
    table.add_column("Header", style="cyan")
    table.add_column("Value")

    found_any = False
    for h in APIM_HEADERS:
        val = raw.headers.get(h)
        if val:
            table.add_row(h, val)
            found_any = True

    if found_any:
        console.print(table)
        rprint("[green]APIM gateway confirmed in the request path.[/green]")
    else:
        rprint("[yellow]No APIM-specific headers found. "
               "Check that APIM_ENDPOINT is the gateway URL, not a direct AOAI endpoint.[/yellow]")
        rprint(f"[dim]HTTP status: {raw.status_code}[/dim]")

except Exception as e:
    rprint(f"[red]Header probe failed:[/red] {e}")
    rprint("[dim]The SDK call above still succeeded — the header probe is informational only.[/dim]")
