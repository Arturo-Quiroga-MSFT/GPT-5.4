#!/usr/bin/env python3
"""
05 — Streaming: Chat Completions API vs Responses API
=====================================================

Both APIs support streaming, but they use completely different event
models.  The Responses API is richer — it emits typed events including
reasoning summary deltas, which Chat Completions never surfaces.

Run:
    python 05_streaming.py

KEY DIFFERENCES visible in this script
───────────────────────────────────────
Chat Completions                    Responses API
─────────────────────────────────── ─────────────────────────────────────────
stream=True                         stream=True  (same param)
for chunk in stream:                for event in stream:
  chunk.choices[0].delta.content      event.type determines what arrived
  (content or None on tool calls)     "response.output_text.delta" → text
                                      "response.reasoning_summary_text.delta"
                                        → visible reasoning stream
                                      "response.completed" → usage + final
finish_reason == "stop"             event.type=="response.completed"
usage in last chunk (if requested)  usage in response.completed event

PSA TIP ► The Responses API emits reasoning summary events in the
stream — you can show customers a live "thinking out loud" feed before
the final answer arrives.  This is architecturally impossible with Chat
Completions streaming.
"""

import time
from config import DEPLOYMENT, get_chat_client, get_responses_client
from rich.console import Console
from rich.live import Live
from rich.text import Text

console = Console()

PROMPT = (
    "Write a short analysis (5 sentences) of why reasoning models like GPT-5.4 "
    "are better suited for complex enterprise tasks than standard LLMs."
)

console.print(f"[bold]Prompt:[/bold] {PROMPT}\n")

# ══════════════════════════════════════════════════════════════════════
# 1. CHAT COMPLETIONS API  ─ chunk.choices[0].delta.content
# ══════════════════════════════════════════════════════════════════════
console.rule("[bold yellow]Chat Completions API — streaming[/bold yellow]")
chat = get_chat_client()

t0             = time.perf_counter()
chat_tokens_in  = 0
chat_tokens_out = 0
chat_text       = ""

stream = chat.chat.completions.create(
    model=DEPLOYMENT,
    messages=[{"role": "user", "content": PROMPT}],
    reasoning_effort="medium",
    stream=True,
    stream_options={"include_usage": True},   # ask for usage in final chunk
)

console.print("[yellow]Streaming:[/yellow] ", end="")

for chunk in stream:
    # Extract text delta
    delta = ""
    if chunk.choices:
        delta = chunk.choices[0].delta.content or ""

    if delta:
        console.print(delta, end="", highlight=False)
        chat_text += delta

    # Final chunk carries usage (when stream_options.include_usage=True)
    if chunk.usage:
        chat_tokens_in  = chunk.usage.prompt_tokens
        chat_tokens_out = chunk.usage.completion_tokens

chat_elapsed = time.perf_counter() - t0
console.print()  # newline after stream

console.print(f"[dim]Input tokens : {chat_tokens_in}[/dim]")
console.print(f"[dim]Output tokens: {chat_tokens_out}[/dim]")
console.print(f"[dim]Elapsed      : {chat_elapsed:.1f}s[/dim]")
console.print("[dim italic]Reasoning tokens were consumed but not visible in the stream.[/dim italic]\n")

# ══════════════════════════════════════════════════════════════════════
# 2. RESPONSES API  ─ typed events including reasoning summary stream
# ══════════════════════════════════════════════════════════════════════
console.rule("[bold cyan]Responses API — streaming with reasoning summary[/bold cyan]")
resp = get_responses_client()

t0              = time.perf_counter()
resp_tokens_in  = 0
resp_tokens_out = 0
resp_text       = ""
resp_reasoning  = ""
in_reasoning    = False
first_text      = True

stream = resp.responses.create(
    model=DEPLOYMENT,
    input=PROMPT,
    reasoning={"effort": "medium", "summary": "auto"},  # enable summary stream
    stream=True,
)

for event in stream:
    event_type = event.type

    # ── Reasoning summary delta ──────────────────────────────────
    if event_type == "response.reasoning_summary_text.delta":
        if not in_reasoning:
            console.print("\n[dim italic]〈 thinking 〉[/dim italic] ", end="")
            in_reasoning = True
        console.print(f"[dim italic]{event.delta}[/dim italic]", end="", highlight=False)
        resp_reasoning += event.delta

    # ── Output text delta ────────────────────────────────────────
    elif event_type == "response.output_text.delta":
        if in_reasoning:
            console.print("\n[dim italic]〈 /thinking 〉[/dim italic]\n")
            console.print("[cyan]Answer:[/cyan] ", end="")
            in_reasoning = False
        if first_text:
            console.print("[cyan]Answer:[/cyan] ", end="")
            first_text = False
        console.print(event.delta, end="", highlight=False)
        resp_text += event.delta

    # ── Stream completed — usage in the event ───────────────────
    elif event_type == "response.completed":
        resp_elapsed    = time.perf_counter() - t0
        usage           = event.response.usage
        resp_tokens_in  = usage.input_tokens
        resp_tokens_out = usage.output_tokens

console.print()  # newline after stream

console.print(f"[dim]Input tokens : {resp_tokens_in}[/dim]")
console.print(f"[dim]Output tokens: {resp_tokens_out}[/dim]")
console.print(f"[dim]Elapsed      : {resp_elapsed:.1f}s[/dim]")
reason_len = len(resp_reasoning.split())
console.print(f"[dim]Reasoning summary words streamed: {reason_len}[/dim]\n")

# ══════════════════════════════════════════════════════════════════════
# SUMMARY TABLE
# ══════════════════════════════════════════════════════════════════════
from rich.table import Table

table = Table(title="Streaming — Side-by-Side", show_lines=True)
table.add_column("Dimension",        style="bold")
table.add_column("Chat Completions", style="yellow")
table.add_column("Responses API",    style="cyan")

table.add_row("Event model",         "chunk.choices[0].delta.content", "event.type + event.delta")
table.add_row("Reasoning stream",    "Not available",                  "response.reasoning_summary_text.delta")
table.add_row("Completion signal",   'finish_reason=="stop"',          'event.type=="response.completed"')
table.add_row("Usage in stream",     "last chunk (opt-in)",            "response.completed event (always)")
table.add_row("Input tokens",        str(chat_tokens_in),              str(resp_tokens_in))
table.add_row("Output tokens",       str(chat_tokens_out),             str(resp_tokens_out))
table.add_row("Elapsed (s)",         f"{chat_elapsed:.1f}",            f"{resp_elapsed:.1f}")
table.add_row("Visible reasoning words", "0",                          str(reason_len))

console.print(table)
