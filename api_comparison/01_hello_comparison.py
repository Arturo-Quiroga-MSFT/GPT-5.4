#!/usr/bin/env python3
"""
01 — Hello GPT-5.4: Chat Completions API vs Responses API
==========================================================

The simplest possible call on both APIs.  Side-by-side output lets you
compare the SDK shape, response object structure, and token metadata.

Run:
    python 01_hello_comparison.py

KEY DIFFERENCES visible in this script
───────────────────────────────────────
Chat Completions                    Responses API
─────────────────────────────────── ─────────────────────────────────────────
messages=[{"role":"user",...}]       input="..."  (string or list)
choices[0].message.content          output_text  (convenience property)
usage.completion_tokens             usage.output_tokens
usage.prompt_tokens                 usage.input_tokens
no reasoning_tokens in basic call   output_tokens_details.reasoning_tokens
AzureOpenAI client                  OpenAI client (pointed at /openai/v1/)
"""

import time
from config import DEPLOYMENT, get_chat_client, get_responses_client
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
PROMPT = "In two sentences, what makes GPT-5.4 unique among reasoning models?"

# ══════════════════════════════════════════════════════════════════════
# 1. CHAT COMPLETIONS API
# ══════════════════════════════════════════════════════════════════════
console.rule("[bold yellow]Chat Completions API[/bold yellow]")

chat   = get_chat_client()
t0     = time.perf_counter()

chat_response = chat.chat.completions.create(
    model=DEPLOYMENT,
    messages=[
        {"role": "developer", "content": "You are a concise AI assistant."},
        {"role": "user",      "content": PROMPT},
    ],
)

chat_elapsed = time.perf_counter() - t0

# Access pattern: choices[0].message.content
chat_text     = chat_response.choices[0].message.content
chat_in_tok   = chat_response.usage.prompt_tokens
chat_out_tok  = chat_response.usage.completion_tokens

# reasoning_tokens lives inside completion_tokens_details (may be None on low effort)
chat_reason_tok = getattr(
    getattr(chat_response.usage, "completion_tokens_details", None),
    "reasoning_tokens", "n/a"
)

console.print(Panel(chat_text, title="Chat Completions — answer"))
console.print(f"[dim]Object path: response.choices[0].message.content[/dim]")
console.print(f"[dim]Input tokens : {chat_in_tok} (usage.prompt_tokens)[/dim]")
console.print(f"[dim]Output tokens: {chat_out_tok} (usage.completion_tokens)[/dim]")
console.print(f"[dim]Reason tokens: {chat_reason_tok} "
              f"(usage.completion_tokens_details.reasoning_tokens)[/dim]")
console.print(f"[dim]Elapsed      : {chat_elapsed:.1f}s[/dim]\n")

# ══════════════════════════════════════════════════════════════════════
# 2. RESPONSES API
# ══════════════════════════════════════════════════════════════════════
console.rule("[bold cyan]Responses API[/bold cyan]")

resp   = get_responses_client()
t0     = time.perf_counter()

resp_response = resp.responses.create(
    model=DEPLOYMENT,
    instructions="You are a concise AI assistant.",
    input=PROMPT,
)

resp_elapsed = time.perf_counter() - t0

# Access pattern: response.output_text  (shortcut — no digging)
resp_text       = resp_response.output_text
resp_in_tok     = resp_response.usage.input_tokens
resp_out_tok    = resp_response.usage.output_tokens
resp_reason_tok = getattr(
    getattr(resp_response.usage, "output_tokens_details", None),
    "reasoning_tokens", "n/a"
)

console.print(Panel(resp_text, title="Responses API — answer"))
console.print(f"[dim]Object path: response.output_text  ← convenience shortcut[/dim]")
console.print(f"[dim]Input tokens : {resp_in_tok} (usage.input_tokens)[/dim]")
console.print(f"[dim]Output tokens: {resp_out_tok} (usage.output_tokens)[/dim]")
console.print(f"[dim]Reason tokens: {resp_reason_tok} "
              f"(usage.output_tokens_details.reasoning_tokens)[/dim]")
console.print(f"[dim]Response ID  : {resp_response.id} ← use for multi-turn[/dim]")
console.print(f"[dim]Elapsed      : {resp_elapsed:.1f}s[/dim]\n")

# ══════════════════════════════════════════════════════════════════════
# SUMMARY TABLE
# ══════════════════════════════════════════════════════════════════════
table = Table(title="Hello — Side-by-Side Summary", show_lines=True)
table.add_column("Dimension",       style="bold")
table.add_column("Chat Completions",style="yellow")
table.add_column("Responses API",   style="cyan")

table.add_row("SDK client",    "AzureOpenAI",             "OpenAI (base_url=/openai/v1/)")
table.add_row("Create method", "chat.completions.create()","responses.create()")
table.add_row("System prompt", 'messages role="developer"', "instructions= param")
table.add_row("User message",  'messages role="user"',     "input= param")
table.add_row("Answer path",   "choices[0].message.content","output_text")
table.add_row("Input tokens",  f"{chat_in_tok} (prompt_tokens)", f"{resp_in_tok} (input_tokens)")
table.add_row("Output tokens", f"{chat_out_tok} (completion_tokens)", f"{resp_out_tok} (output_tokens)")
table.add_row("State ID",      "none (stateless)",        f"{resp_response.id[:20]}…")
table.add_row("Latency (s)",   f"{chat_elapsed:.1f}",     f"{resp_elapsed:.1f}")

console.print(table)
