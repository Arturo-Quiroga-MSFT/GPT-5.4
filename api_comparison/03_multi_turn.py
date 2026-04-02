#!/usr/bin/env python3
"""
03 — Multi-turn Conversation: Chat Completions API vs Responses API
====================================================================

This is where the two APIs diverge most sharply.  Chat Completions requires
you to own and resend the full message history on every turn.  The Responses
API stores state server-side and you chain turns with a single ID.

Run:
    python 03_multi_turn.py

KEY DIFFERENCES visible in this script
───────────────────────────────────────
Chat Completions                    Responses API
─────────────────────────────────── ─────────────────────────────────────────
You build & manage a messages list  Server stores history — you keep only ID
Resend ALL prior messages every turn  Send only the new message each turn
Input tokens grow linearly           Input tokens stay roughly constant
Context window fills up eventually   No client-side buffer management needed
No native session concept            response.id is the session handle
You control history (privacy+)       OpenAI/Azure holds the history (govern-)

PSA TIP ► For long agentic conversations (10+ turns, retrieval results,
tool outputs in context), the Responses API's server-side state saves
significant input-token spend and simplifies application code.
"""

import time
from config import DEPLOYMENT, get_chat_client, get_responses_client
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

SYSTEM = "You are a helpful assistant that explains AI concepts simply."

TURNS = [
    "What is transformer architecture in one paragraph?",
    "How does the attention mechanism work within that?",
    "And how does GPT-5.4 extend that with chain-of-thought reasoning?",
    "Give me a concrete analogy that explains all three concepts together.",
]

# ══════════════════════════════════════════════════════════════════════
# 1. CHAT COMPLETIONS API  ─ developer owns message history
# ══════════════════════════════════════════════════════════════════════
console.rule("[bold yellow]Chat Completions API — developer manages history[/bold yellow]")
chat = get_chat_client()

# You must seed and maintain this list for the entire session
messages = [{"role": "developer", "content": SYSTEM}]

chat_turn_data = []
for i, user_msg in enumerate(TURNS, 1):
    messages.append({"role": "user", "content": user_msg})

    console.print(f"\n[yellow]Turn {i}:[/yellow] {user_msg}")
    t0 = time.perf_counter()

    r = chat.chat.completions.create(
        model=DEPLOYMENT,
        messages=messages,               # ← resend everything every time
    )
    elapsed = time.perf_counter() - t0

    assistant_msg = r.choices[0].message.content
    messages.append({"role": "assistant", "content": assistant_msg})  # append for next turn

    in_tok  = r.usage.prompt_tokens
    out_tok = r.usage.completion_tokens
    chat_turn_data.append({"turn": i, "in_tok": in_tok, "out_tok": out_tok, "latency": elapsed})

    console.print(Panel(assistant_msg[:300] + "…", title=f"Chat — Turn {i}"))
    console.print(f"[dim]  Input tokens this call: {in_tok} "
                  f"(includes all {i} prior turns)[/dim]")

console.print(f"\n[dim]Final messages list length: {len(messages)} items[/dim]")

# ══════════════════════════════════════════════════════════════════════
# 2. RESPONSES API  ─ server owns history; you keep only the last ID
# ══════════════════════════════════════════════════════════════════════
console.rule("[bold cyan]Responses API — server manages history[/bold cyan]")
resp    = get_responses_client()
prev_id = None  # this is the only thing you track between turns

resp_turn_data = []
for i, user_msg in enumerate(TURNS, 1):
    console.print(f"\n[cyan]Turn {i}:[/cyan] {user_msg}")

    kwargs = {
        "model":        DEPLOYMENT,
        "instructions": SYSTEM,
        "input":        user_msg,           # ← only the NEW message
    }
    if prev_id:
        kwargs["previous_response_id"] = prev_id  # ← link to previous turn

    t0 = time.perf_counter()
    r  = resp.responses.create(**kwargs)
    elapsed = time.perf_counter() - t0

    prev_id = r.id   # ← save this; that's all you need

    in_tok  = r.usage.input_tokens
    out_tok = r.usage.output_tokens
    resp_turn_data.append({"turn": i, "in_tok": in_tok, "out_tok": out_tok, "latency": elapsed})

    console.print(Panel(r.output_text[:300] + "…", title=f"Responses — Turn {i}"))
    console.print(f"[dim]  Input tokens this call: {in_tok}[/dim]")
    console.print(f"[dim]  Response ID: {r.id[:20]}… (only thing stored client-side)[/dim]")

console.print(f"\n[dim]Client-side state: just one string — '{prev_id[:20]}…'[/dim]")

# ══════════════════════════════════════════════════════════════════════
# TOKEN ECONOMICS TABLE
# ══════════════════════════════════════════════════════════════════════
table = Table(title="Multi-turn Token Economics", show_lines=True)
table.add_column("Turn")
table.add_column("Chat — Input tok", justify="right", style="yellow")
table.add_column("Responses — Input tok", justify="right", style="cyan")
table.add_column("Δ Input tok", justify="right")
table.add_column("Chat latency (s)", justify="right", style="yellow")
table.add_column("Resp latency (s)", justify="right", style="cyan")

for c, s in zip(chat_turn_data, resp_turn_data):
    delta = c["in_tok"] - s["in_tok"]
    delta_style = "red" if delta > 0 else "green"
    table.add_row(
        str(c["turn"]),
        str(c["in_tok"]),
        str(s["in_tok"]),
        f"[{delta_style}]+{delta}[/{delta_style}]" if delta >= 0 else f"[{delta_style}]{delta}[/{delta_style}]",
        f"{c['latency']:.1f}",
        f"{s['latency']:.1f}",
    )

console.print(table)
console.print(
    "\n[bold]PSA Takeaway:[/bold]\n"
    "Chat Completions input-token cost grows with each turn because you\n"
    "resend the entire history.  The Responses API keeps input tokens\n"
    "roughly stable — the server handles compaction.  Over a 20-turn\n"
    "agentic session this can mean [bold]3–5× fewer input tokens[/bold] billed."
)
