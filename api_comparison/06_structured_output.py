#!/usr/bin/env python3
"""
06 — Structured Output: Chat Completions API vs Responses API
=============================================================

JSON-schema-constrained generation is available in both APIs.
The field names and nesting differ slightly; learn both so you can
support partners using either stack.

Run:
    python 06_structured_output.py

KEY DIFFERENCES visible in this script
───────────────────────────────────────
Chat Completions                    Responses API
─────────────────────────────────── ─────────────────────────────────────────
response_format={                   text={
  "type":"json_schema",               "format":{
  "json_schema":{                       "type":"json_schema",
    "name":...,                         "name":...,
    "schema":...,                       "schema":...,
    "strict":True                       "strict":True
  }                                   }
}                                   }
choices[0].message.content          output_text
  (string — parse yourself)           (string — parse yourself)

Both APIs enforce strict=True, meaning every field in the schema must
appear and no extra fields are allowed.  The model will not hallucinate
keys outside the schema.
"""

import json
import time
from config import DEPLOYMENT, get_chat_client, get_responses_client
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

PROMPT = (
    "List 3 enterprise use cases for GPT-5.4 reasoning models.  "
    "For each, provide: a short title, the industry vertical, "
    "the key benefit, and an estimated ROI tier (low/medium/high)."
)

# Shared schema — identical for both APIs
SCHEMA = {
    "type": "object",
    "properties": {
        "use_cases": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title":    {"type": "string"},
                    "industry": {"type": "string"},
                    "benefit":  {"type": "string"},
                    "roi_tier": {"type": "string", "enum": ["low", "medium", "high"]},
                },
                "required": ["title", "industry", "benefit", "roi_tier"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["use_cases"],
    "additionalProperties": False,
}

# ══════════════════════════════════════════════════════════════════════
# 1. CHAT COMPLETIONS API
# ══════════════════════════════════════════════════════════════════════
console.rule("[bold yellow]Chat Completions API — structured output[/bold yellow]")
chat = get_chat_client()

t0 = time.perf_counter()

chat_response = chat.chat.completions.create(
    model=DEPLOYMENT,
    messages=[{"role": "user", "content": PROMPT}],
    response_format={                          # ← top-level param name
        "type": "json_schema",
        "json_schema": {                       # ← nested under "json_schema"
            "name":   "enterprise_use_cases",
            "schema": SCHEMA,
            "strict": True,
        },
    },
)

chat_elapsed = time.perf_counter() - t0
chat_raw     = chat_response.choices[0].message.content  # always a string
chat_data    = json.loads(chat_raw)

console.print(Panel(
    json.dumps(chat_data, indent=2),
    title="Chat Completions — structured response"
))
console.print(f"[dim]response_format.json_schema param shape[/dim]")
console.print(f"[dim]Tokens — in: {chat_response.usage.prompt_tokens}  "
              f"out: {chat_response.usage.completion_tokens}[/dim]")
console.print(f"[dim]Elapsed: {chat_elapsed:.1f}s[/dim]\n")

# ══════════════════════════════════════════════════════════════════════
# 2. RESPONSES API
# ══════════════════════════════════════════════════════════════════════
console.rule("[bold cyan]Responses API — structured output[/bold cyan]")
resp = get_responses_client()

t0 = time.perf_counter()

resp_response = resp.responses.create(
    model=DEPLOYMENT,
    input=PROMPT,
    text={                                     # ← top-level param name "text"
        "format": {                            # ← nested under "format"
            "type":   "json_schema",
            "name":   "enterprise_use_cases",
            "schema": SCHEMA,
            "strict": True,
        }
    },
)

resp_elapsed = time.perf_counter() - t0
resp_raw     = resp_response.output_text      # same — always a string
resp_data    = json.loads(resp_raw)

console.print(Panel(
    json.dumps(resp_data, indent=2),
    title="Responses API — structured response"
))
console.print(f"[dim]text.format param shape[/dim]")
console.print(f"[dim]Tokens — in: {resp_response.usage.input_tokens}  "
              f"out: {resp_response.usage.output_tokens}[/dim]")
console.print(f"[dim]Elapsed: {resp_elapsed:.1f}s[/dim]\n")

# ══════════════════════════════════════════════════════════════════════
# VERIFY SCHEMA COMPLIANCE
# ══════════════════════════════════════════════════════════════════════
def validate_use_cases(data: dict) -> bool:
    """Basic structural validation."""
    cases = data.get("use_cases", [])
    if not isinstance(cases, list) or len(cases) == 0:
        return False
    for c in cases:
        if not all(k in c for k in ["title", "industry", "benefit", "roi_tier"]):
            return False
        if c["roi_tier"] not in ("low", "medium", "high"):
            return False
    return True

chat_valid = validate_use_cases(chat_data)
resp_valid = validate_use_cases(resp_data)

# ══════════════════════════════════════════════════════════════════════
# SUMMARY TABLE
# ══════════════════════════════════════════════════════════════════════
table = Table(title="Structured Output — Side-by-Side", show_lines=True)
table.add_column("Dimension",        style="bold")
table.add_column("Chat Completions", style="yellow")
table.add_column("Responses API",    style="cyan")

table.add_row("Format param",     "response_format={...}",  "text={format:{...}}")
table.add_row("Schema nesting",   'json_schema.{"schema":…}', 'format.{"schema":…}')
table.add_row("Result field",     "choices[0].message.content", "output_text")
table.add_row("Schema obeyed?",   "[green]Yes[/green]" if chat_valid else "[red]No[/red]",
                                  "[green]Yes[/green]" if resp_valid else "[red]No[/red]")
table.add_row("Input tokens",     str(chat_response.usage.prompt_tokens),
                                  str(resp_response.usage.input_tokens))
table.add_row("Output tokens",    str(chat_response.usage.completion_tokens),
                                  str(resp_response.usage.output_tokens))
table.add_row("Elapsed (s)",      f"{chat_elapsed:.1f}", f"{resp_elapsed:.1f}")

console.print(table)
console.print(
    "\n[bold]PSA Takeaway:[/bold]\n"
    "Both APIs produce identical JSON output for the same schema.  The\n"
    "parameter path is the main difference.  Migrate Chat Completions\n"
    "structured-output callers to Responses by moving response_format\n"
    "→ text.format and json_schema → (inline).  One rename, same schema."
)
