#!/usr/bin/env python3
"""
02 — Reasoning Effort: Chat Completions API vs Responses API
=============================================================

Both APIs expose a way to control how hard GPT-5.4 thinks before
answering.  The parameter names, nesting, and capabilities differ
significantly — and that difference matters for reasoning-heavy workloads.

Run:
    python 02_reasoning_effort.py

KEY DIFFERENCES visible in this script
───────────────────────────────────────
Chat Completions                    Responses API
─────────────────────────────────── ─────────────────────────────────────────
reasoning_effort="high"             reasoning={"effort":"high"}
  (top-level str param)               (nested dict param)
no reasoning summary option         summary="auto"|"concise"|"detailed"
  → reasoning is hidden               → see what the model thought about
completion_tokens_details           output_tokens_details
  .reasoning_tokens                   .reasoning_tokens

PSA TIP ► The reasoning summary in the Responses API is a game-changer
for debugging and explaining model behaviour to customers.  Chat
Completions gives you no window into the reasoning chain.
"""

import time
from config import DEPLOYMENT, REASONING_EFFORTS, get_chat_client, get_responses_client
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

PROMPT = (
    "A train leaves City A at 09:00 going 120 km/h. "
    "Another train leaves City B (400 km away) at 09:30 going 80 km/h toward City A. "
    "At what time do they meet?  Show full working."
)

console.print(f"[bold]Prompt:[/bold] {PROMPT}\n")

# ══════════════════════════════════════════════════════════════════════
# 1. CHAT COMPLETIONS API  ─ reasoning_effort is a flat top-level param
# ══════════════════════════════════════════════════════════════════════
console.rule("[bold yellow]Chat Completions API[/bold yellow]")
chat = get_chat_client()

chat_results = []
for effort in REASONING_EFFORTS:
    t0 = time.perf_counter()
    r = chat.chat.completions.create(
        model=DEPLOYMENT,
        messages=[{"role": "user", "content": PROMPT}],
        reasoning_effort=effort,           # ← flat top-level string
    )
    elapsed = time.perf_counter() - t0

    details = getattr(r.usage, "completion_tokens_details", None)
    reason_tok = getattr(details, "reasoning_tokens", "?")
    chat_results.append({
        "effort":      effort,
        "answer":      (r.choices[0].message.content or "")[:100] + "…",
        "in_tok":      r.usage.prompt_tokens,
        "out_tok":     r.usage.completion_tokens,
        "reason_tok":  reason_tok,
        "latency":     elapsed,
    })
    console.print(f"[yellow]  effort={effort}[/yellow] → "
                  f"{elapsed:.1f}s | out={r.usage.completion_tokens} tok "
                  f"| reasoning={reason_tok} tok")

# No reasoning summary available — the model's thinking is opaque
console.print("[dim italic]  ↑ Reasoning tokens were consumed but you cannot see the chain.[/dim italic]\n")

# ══════════════════════════════════════════════════════════════════════
# 2. RESPONSES API  ─ reasoning is a nested dict, summary is available
# ══════════════════════════════════════════════════════════════════════
console.rule("[bold cyan]Responses API[/bold cyan]")
resp = get_responses_client()

resp_results = []
for effort in REASONING_EFFORTS:
    t0 = time.perf_counter()
    r = resp.responses.create(
        model=DEPLOYMENT,
        input=PROMPT,
        reasoning={                        # ← nested dict
            "effort":  effort,
            "summary": "auto",             # ← get a visible reasoning summary!
        },
    )
    elapsed = time.perf_counter() - t0

    # Collect visible reasoning summary (if generated)
    reasoning_summary = ""
    for item in r.output:
        if item.type == "reasoning":
            for summary_item in getattr(item, "summary", []):
                reasoning_summary += getattr(summary_item, "text", "")

    details   = getattr(r.usage, "output_tokens_details", None)
    reason_tok = getattr(details, "reasoning_tokens", "?")
    resp_results.append({
        "effort":           effort,
        "answer":           r.output_text[:100] + "…",
        "in_tok":           r.usage.input_tokens,
        "out_tok":          r.usage.output_tokens,
        "reason_tok":       reason_tok,
        "reasoning_summary": reasoning_summary[:200] + ("…" if len(reasoning_summary) > 200 else ""),
        "latency":          elapsed,
    })
    console.print(f"[cyan]  effort={effort}[/cyan] → "
                  f"{elapsed:.1f}s | out={r.usage.output_tokens} tok "
                  f"| reasoning={reason_tok} tok")
    if reasoning_summary:
        console.print(Panel(
            reasoning_summary[:300] + ("…" if len(reasoning_summary) > 300 else ""),
            title=f"Reasoning summary ({effort})",
            style="dim",
        ))

# ══════════════════════════════════════════════════════════════════════
# SUMMARY TABLE
# ══════════════════════════════════════════════════════════════════════
table = Table(title="Reasoning Effort — Side-by-Side", show_lines=True)
table.add_column("Effort")
table.add_column("API")
table.add_column("In tok",  justify="right")
table.add_column("Out tok", justify="right")
table.add_column("Reason tok", justify="right")
table.add_column("Latency (s)", justify="right")
table.add_column("Reasoning visible?")

for c, s in zip(chat_results, resp_results):
    table.add_row(
        c["effort"], "[yellow]Chat Completions[/yellow]",
        str(c["in_tok"]), str(c["out_tok"]), str(c["reason_tok"]),
        f"{c['latency']:.1f}", "[red]No[/red]",
    )
    table.add_row(
        s["effort"], "[cyan]Responses[/cyan]",
        str(s["in_tok"]), str(s["out_tok"]), str(s["reason_tok"]),
        f"{s['latency']:.1f}", "[green]Yes — summary returned[/green]",
    )

console.print(table)

console.print("\n[bold]PSA Takeaway:[/bold]")
console.print(
    "The Responses API [cyan]reasoning.summary[/cyan] field lets you surface [bold]why[/bold] the\n"
    "model reached a conclusion — invaluable for customer demos, debugging,\n"
    "and building trust in AI-assisted decisions.  Chat Completions keeps\n"
    "all reasoning tokens hidden; you pay for them but never see them."
)
