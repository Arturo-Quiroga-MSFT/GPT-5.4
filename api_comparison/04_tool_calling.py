#!/usr/bin/env python3
"""
04 — Tool Calling: Chat Completions API vs Responses API
=========================================================

Both APIs support function/tool calling, but the loop structure, object
shapes, and how you submit results back differ in important ways.

Run:
    python 04_tool_calling.py

KEY DIFFERENCES visible in this script
───────────────────────────────────────
Chat Completions                    Responses API
─────────────────────────────────── ─────────────────────────────────────────
tools=[{"type":"function","function":{  tools=[{"type":"function","name":...,
  "name":...,"description":...,           "description":...,"parameters":...}]
  "parameters":...}}]                    (flatter — no nested "function" key)
finish_reason == "tool_calls"       iterate r.output for type=="function_call"
choices[0].message.tool_calls       item.name, item.arguments, item.call_id
role="tool", tool_call_id=...       type="function_call_output", call_id=...
second create() call with messages  second create() with input=[...] list
Built-in tools: none                Built-in: web_search_preview,
                                      file_search, code_interpreter

PSA TIP ► The Responses API tool definitions are less nested (no double
"function" wrapping).  For built-in tools like web search you add ONE
dict and the API handles the entire retrieval loop — no custom code.
"""

import json
import time
import requests

from config import DEPLOYMENT, get_chat_client, get_responses_client
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# ── Shared tool definitions (note schema differences shown inline) ────
TOOLS_CHAT = [
    {
        "type": "function",
        "function": {                      # ← nested "function" key required
            "name": "get_weather",
            "description": "Get current weather for a city.",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        },
    }
]

TOOLS_RESPONSES = [
    {
        "type": "function",
        "name": "get_weather",             # ← flat, no "function" nesting
        "description": "Get current weather for a city.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    }
]


def get_weather(city: str) -> str:
    """Real implementation — wttr.in, no key needed."""
    try:
        r = requests.get(f"https://wttr.in/{city}?format=j1", timeout=10)
        r.raise_for_status()
        data = r.json()["current_condition"][0]
        return json.dumps({
            "city":        city,
            "temp_c":      data["temp_C"],
            "condition":   data["weatherDesc"][0]["value"],
            "humidity":    data["humidity"],
        })
    except Exception as exc:
        return json.dumps({"city": city, "error": str(exc)})


city  = input("Enter a city (default: Paris): ").strip() or "Paris"
query = f"What is the current weather in {city}?"
console.print(f"\n[bold]Query:[/bold] {query}\n")

# ══════════════════════════════════════════════════════════════════════
# 1. CHAT COMPLETIONS API  ─ manual tool-call loop
# ══════════════════════════════════════════════════════════════════════
console.rule("[bold yellow]Chat Completions API[/bold yellow]")
chat = get_chat_client()

t0 = time.perf_counter()

# Step 1 — model decides to call a tool
r1 = chat.chat.completions.create(
    model=DEPLOYMENT,
    messages=[{"role": "user", "content": query}],
    tools=TOOLS_CHAT,
)

tool_calls_made = []

# Step 2 — execute each tool call and build result messages
messages_with_results = [{"role": "user", "content": query}]
messages_with_results.append(r1.choices[0].message)  # append assistant message (with tool_calls)

for tc in (r1.choices[0].message.tool_calls or []):
    args    = json.loads(tc.function.arguments)
    result  = get_weather(args["city"])
    tool_calls_made.append({"name": tc.function.name, "args": args, "result": result})

    messages_with_results.append({
        "role":         "tool",               # ← role must be "tool"
        "tool_call_id": tc.id,                # ← must echo the call_id
        "content":      result,
    })

# Step 3 — second create() call to get final answer
r2 = chat.chat.completions.create(
    model=DEPLOYMENT,
    messages=messages_with_results,
    tools=TOOLS_CHAT,
)

chat_elapsed = time.perf_counter() - t0
chat_answer  = r2.choices[0].message.content

console.print(Panel(chat_answer, title="Chat Completions — final answer"))
console.print(f"[dim]Tool calls: {[t['name'] for t in tool_calls_made]}[/dim]")
console.print(f"[dim]Requires 2 API calls + manual message list management[/dim]")
console.print(f"[dim]Elapsed: {chat_elapsed:.1f}s[/dim]\n")

# ══════════════════════════════════════════════════════════════════════
# 2. RESPONSES API  ─ same tool pattern but flatter objects
# ══════════════════════════════════════════════════════════════════════
console.rule("[bold cyan]Responses API[/bold cyan]")
resp = get_responses_client()

t0 = time.perf_counter()

# Step 1 — model decides to call a tool
r1 = resp.responses.create(
    model=DEPLOYMENT,
    input=query,
    tools=TOOLS_RESPONSES,
)

tool_call_outputs = []
resp_tool_calls_made = []

# Step 2 — iterate output items to find function_call items
for item in r1.output:
    if item.type == "function_call":
        args   = json.loads(item.arguments)
        result = get_weather(args["city"])
        resp_tool_calls_made.append({"name": item.name, "args": args, "result": result})

        tool_call_outputs.append({
            "type":    "function_call_output",  # ← different type name
            "call_id": item.call_id,             # ← same concept, different field name
            "output":  result,                   # ← "output" not "content"
        })

# Step 3 — second create() submitting outputs via input list
r2 = resp.responses.create(
    model=DEPLOYMENT,
    input=tool_call_outputs,                    # ← input takes the output list
    previous_response_id=r1.id,                 # ← server already has the context
    tools=TOOLS_RESPONSES,
)

resp_elapsed = time.perf_counter() - t0
resp_answer  = r2.output_text

console.print(Panel(resp_answer, title="Responses API — final answer"))
console.print(f"[dim]Tool calls: {[t['name'] for t in resp_tool_calls_made]}[/dim]")
console.print(f"[dim]Requires 2 API calls + previous_response_id (no message list mgmt)[/dim]")
console.print(f"[dim]Elapsed: {resp_elapsed:.1f}s[/dim]\n")

# ── BONUS: Show the built-in web search tool (Responses API only) ────
console.rule("[bold cyan]Responses API — Built-in web_search_preview tool[/bold cyan]")
console.print("[dim]Chat Completions has no equivalent — you'd implement web search yourself.[/dim]\n")

t0 = time.perf_counter()
r_web = resp.responses.create(
    model=DEPLOYMENT,
    input=f"What is the weather forecast for {city} this weekend?",
    tools=[{"type": "web_search_preview"}],    # ← one line — no custom code
)
web_elapsed = time.perf_counter() - t0
console.print(Panel(r_web.output_text, title="Web-grounded answer (Responses API only)"))
console.print(f"[dim]Elapsed: {web_elapsed:.1f}s[/dim]\n")

# ══════════════════════════════════════════════════════════════════════
# SUMMARY TABLE
# ══════════════════════════════════════════════════════════════════════
table = Table(title="Tool Calling — Side-by-Side", show_lines=True)
table.add_column("Dimension",          style="bold")
table.add_column("Chat Completions",   style="yellow")
table.add_column("Responses API",      style="cyan")

table.add_row("Tool schema format",   'nested {"function":{...}}',  'flat {"name":...}')
table.add_row("Detect tool call",     'finish_reason=="tool_calls"', 'item.type=="function_call"')
table.add_row("Result submission",    'role="tool", tool_call_id=…', 'type="function_call_output", call_id=…')
table.add_row("Result field name",    '"content"',                   '"output"')
table.add_row("Context for turn 2",   "resend full messages list",   "previous_response_id")
table.add_row("Web search",           "implement yourself",          '{"type":"web_search_preview"}')
table.add_row("File search",          "implement yourself",          '{"type":"file_search"}')
table.add_row("Code interpreter",     "not available",               '{"type":"code_interpreter"}')
table.add_row("Total elapsed (s)",    f"{chat_elapsed:.1f}",         f"{resp_elapsed:.1f}")

console.print(table)
