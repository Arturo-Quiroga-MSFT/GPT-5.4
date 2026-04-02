# Chat Completions API vs Responses API with GPT-5.4

> PSA guidance — field reference for partner architecture conversations

---

## Overview

GPT-5.4 is accessible through two distinct Azure OpenAI API surfaces.
Both are production-ready and both support the model's reasoning
capabilities.  They are *not* redundant — they have different strengths,
and the right choice depends on what a customer/partner is building.

This directory contains six runnable scripts that show the same scenario
implemented on both APIs side-by-side, along with the trade-off analysis
below.

---

## Quick-Reference Feature Matrix

| Feature | Chat Completions | Responses API |
|---|---|---|
| **SDK client** | `AzureOpenAI` | `OpenAI` (base\_url `/openai/v1/`) |
| **Create method** | `chat.completions.create()` | `responses.create()` |
| **System prompt** | `messages role="developer"` | `instructions=` param |
| **Reasoning effort** | `reasoning_effort="high"` (flat) | `reasoning={"effort":"high"}` (dict) |
| **Reasoning summary** | Not available | `reasoning={"summary":"auto"}` |
| **Multi-turn state** | Client owns message list | `previous_response_id` — server-owned |
| **Input token growth** | Linear with turns | Roughly constant |
| **Tool schema** | `{type:"function", function:{...}}` | `{type:"function", name:..., ...}` (flatter) |
| **Tool result role** | `role="tool"` | `type="function_call_output"` |
| **Built-in web search** | Not supported | `{"type":"web_search_preview"}` |
| **Built-in file search** | Not supported | `{"type":"file_search"}` |
| **Code interpreter** | Not supported | `{"type":"code_interpreter"}` |
| **Structured output param** | `response_format={json_schema:{...}}` | `text={format:{...}}` |
| **Answer shortcut** | `choices[0].message.content` | `output_text` |
| **Streaming event API** | `chunk.choices[0].delta.content` | `event.type` + `event.delta` |
| **Reasoning stream** | Hidden | `response.reasoning_summary_text.delta` |
| **LangChain support** | Native | Via compatible wrapper |
| **Semantic Kernel support** | Native | Via compatible wrapper |
| **`n > 1` completions** | Yes | No |
| **`logprobs`** | Yes | No |

---

## API Surface Comparison

### Initialization

```python
# Chat Completions API
from openai import AzureOpenAI

client = AzureOpenAI(
    azure_endpoint=ENDPOINT,
    azure_ad_token_provider=token_provider,
    api_version="2025-04-01-preview",
)

# Responses API
from openai import OpenAI

client = OpenAI(
    base_url=f"{ENDPOINT}/openai/v1/",
    api_key=token_provider(),
)
```

### Basic Call

```python
# Chat Completions API
response = client.chat.completions.create(
    model="gpt-5.4",
    messages=[
        {"role": "developer", "content": "You are a helpful assistant."},
        {"role": "user",      "content": "Explain quantum entanglement."},
    ],
)
answer = response.choices[0].message.content   # dig into choices

# Responses API
response = client.responses.create(
    model="gpt-5.4",
    instructions="You are a helpful assistant.",
    input="Explain quantum entanglement.",
)
answer = response.output_text                  # top-level convenience
```

### Reasoning Effort + Summary

```python
# Chat Completions API
# reasoning_effort is a flat top-level string; no summary possible
response = client.chat.completions.create(
    model="gpt-5.4",
    messages=[...],
    reasoning_effort="high",      # "none" | "low" | "medium" | "high" | "xhigh"
)
# The model thought deeply — but you cannot see how

# Responses API
# reasoning is a nested dict; you can request the summary
response = client.responses.create(
    model="gpt-5.4",
    input="...",
    reasoning={
        "effort":  "high",
        "summary": "auto",        # "auto" | "concise" | "detailed"
    },
)
# Retrieve the model's visible reasoning chain
for item in response.output:
    if item.type == "reasoning":
        for s in item.summary:
            print(s.text)   # what the model actually thought about
```

---

## In-Depth Trade-off Analysis

### 1 — Reasoning Visibility

This is the most significant architectural difference for GPT-5.4.

**Chat Completions** consumes reasoning tokens internally.  You are
billed for them but you cannot observe what the model thought.  This is
acceptable when the final answer quality is all that matters.

**Responses API** can return a reasoning *summary* — a natural-language
description of the model's chain-of-thought — as a first-class output
item.  This is invaluable for:

- Customer demos where *showing* reasoning builds trust
- Audit trails in regulated industries (finance, healthcare, legal)
- Debugging incorrect answers — you see where the model went wrong
- Building explainability features in enterprise AI products

**PSA recommendation:** whenever a partner asks how to make AI decisions
auditable or explainable, the Responses API reasoning summary is the
answer.  Chat Completions cannot provide this without a separate
summarisation call.

---

### 2 — Multi-turn State and Token Economics

**Chat Completions** is stateless.  Every turn you send the full
conversation history in the `messages` list.  Input token cost grows
linearly:

```
turn 1 → send  500 tokens
turn 2 → send 1100 tokens (500 + 600 new)
turn 3 → send 1900 tokens (1100 + 800 new)
...
turn 10 → potentially 10 000+ tokens of history resent
```

**Responses API** stores history server-side.  You chain turns with a
single `previous_response_id` string.  The Azure-side compaction means
each turn's input token count stays roughly stable at the size of the
new message.  On a 20-turn agentic conversation with tool outputs in
context this can mean **3–5× fewer input tokens billed**.

```python
# Turn 1
r = client.responses.create(model="gpt-5.4", input="First question")
prev_id = r.id

# Turn 2 — only the NEW message is sent; history lives on the server
r = client.responses.create(
    model="gpt-5.4",
    input="Follow-up question",
    previous_response_id=prev_id,      # that's it
)
```

**Consideration:** the server-side history has a retention window. If
a partner needs to own, encrypt, or audit conversation history
themselves, Chat Completions with a bring-your-own store (e.g., Azure
Cosmos DB or Table Storage) is the correct architecture.

---

### 3 — Built-in Tools

**Chat Completions** supports only custom function/tool definitions.
Web search, file search, and code execution require custom integrations.

**Responses API** ships with three built-in hosted tools:

| Tool | What it does |
|---|---|
| `web_search_preview` | BrowseComp-grade live web search (82.7% SOTA) |
| `file_search` | Vector search over Azure OpenAI file stores |
| `code_interpreter` | Sandboxed Python execution |

```python
# Web search — one line, no custom code, no search service provisioning
response = client.responses.create(
    model="gpt-5.4",
    input="What are the latest Azure AI announcements?",
    tools=[{"type": "web_search_preview"}],
)
```

For partners who previously needed to wire up Bing Search + function
calling, `web_search_preview` eliminates that integration entirely.

---

### 4 — Tool Calling Schema

The tool definition format is slightly different:

```python
# Chat Completions — nested under "function" key
{
    "type": "function",
    "function": {                   # ← extra nesting level
        "name":        "my_tool",
        "description": "...",
        "parameters":  { ... },
    }
}

# Responses API — flat
{
    "type":        "function",      # ← name at top level
    "name":        "my_tool",
    "description": "...",
    "parameters":  { ... },
}
```

Tool result submission also differs:

```python
# Chat Completions result
{"role": "tool", "tool_call_id": tc.id, "content": json_result}

# Responses API result
{"type": "function_call_output", "call_id": item.call_id, "output": json_result}
```

---

### 5 — Streaming Event Model

**Chat Completions** streaming yields `ChatCompletionChunk` objects.
Text arrives in `chunk.choices[0].delta.content`.  There is no
reasoning stream.

**Responses API** streaming yields typed events identified by
`event.type`.  The three most important for reasoning workloads:

| Event type | Meaning |
|---|---|
| `response.reasoning_summary_text.delta` | Next chunk of the reasoning summary |
| `response.output_text.delta` | Next chunk of the final answer |
| `response.completed` | Stream done; `event.response.usage` has full token counts |

This lets you build UX patterns impossible with Chat Completions:
a real-time "thinking" panel that fades away as the answer arrives, or
a collapsible audit trail that populates live.

---

### 6 — Framework Compatibility

This is the main reason Chat Completions still has a strong place in the
partner landscape.

| Framework | Chat Completions | Responses API |
|---|---|---|
| **LangChain** | Native first-class support | Via `ChatOpenAI` with base\_url override |
| **Semantic Kernel** | Native | Partial — check SK release notes |
| **AutoGen** | Native | Partial — under active development |
| **LlamaIndex** | Native | Via custom LLM wrapper |
| **Haystack** | Native | Via compatible client |

If a partner is already invested in LangChain or Semantic Kernel
orchestration, Chat Completions is the path of least resistance.  The
Responses API is best adopted in *new* builds or where the partner
controls the orchestration layer themselves.

---

## When to Use Each API

### Use Chat Completions when

- The partner uses LangChain, Semantic Kernel, AutoGen, or LlamaIndex
  and wants to stay on that stack
- The application needs `n > 1` alternative completions or `logprobs`
- The partner must own, encrypt, or audit every message in the
  conversation history
- Migrating an existing OpenAI Chat Completions app with minimal changes
- The team has strong existing investment in the Chat Completions pattern

### Use the Responses API when

- Building *new* agentic apps or copilots from scratch
- The model's reasoning chain needs to be visible (compliance, demos,
  debugging)
- Multi-turn conversation cost is a concern (long sessions, many tools)
- The app can use built-in web search or file search instead of custom
  integrations
- The partner wants the most capable and future-forward API surface for
  GPT-5.4 and upcoming models
- Building real-time UX that surfaces reasoning live to end users

---

## Decision Tree

```
Is the partner already using LangChain / Semantic Kernel / AutoGen?
├─ Yes → Chat Completions  (native SDK support, no refactoring)
└─ No (new build or own orchestration)
   │
   Does the app need conversation history stored in partner infra?
   ├─ Yes → Chat Completions  (you own the messages list)
   └─ No
      │
      Does the app need auditable reasoning / explainability?
      ├─ Yes → Responses API  (reasoning summary)
      └─ No
         │
         Does the app need web search, file search, or code execution?
         ├─ Yes → Responses API  (built-in tools)
         └─ No
            │
            Is multi-turn cost / context window scaling a concern?
            ├─ Yes → Responses API  (server-side state)
            └─ No → Either works; Responses API preferred for new builds
```

---

## Migration Cheat Sheet

Moving a Chat Completions caller to the Responses API:

| Chat Completions | Responses API |
|---|---|
| `AzureOpenAI(azure_endpoint=…)` | `OpenAI(base_url=BASE_URL, api_key=token)` |
| `client.chat.completions.create()` | `client.responses.create()` |
| `messages=[{"role":"developer",…}]` | `instructions="…"` |
| `messages=[{"role":"user",…}]` | `input="…"` |
| `choices[0].message.content` | `output_text` |
| `usage.prompt_tokens` | `usage.input_tokens` |
| `usage.completion_tokens` | `usage.output_tokens` |
| `response_format={json_schema:{…}}` | `text={format:{…}}` |
| `reasoning_effort="high"` | `reasoning={"effort":"high","summary":"auto"}` |
| Build messages list for multi-turn | `previous_response_id=prev_id` |

---

## Scripts in This Directory

| Script | What it shows |
|---|---|
| `01_hello_comparison.py` | Minimal call — SDK shape, response object, token fields |
| `02_reasoning_effort.py` | Effort levels and reasoning summary visibility |
| `03_multi_turn.py` | 4-turn conversation — token economics comparison |
| `04_tool_calling.py` | Tool definition format, loop structure, built-in web search |
| `05_streaming.py` | Event model — reasoning summary stream vs text-only chunks |
| `06_structured_output.py` | JSON schema enforcement — param path differences |

Run any script from this directory with:

```bash
cd api_comparison
python 01_hello_comparison.py
```

Requires the `.env` at the workspace root with `AZURE_OPENAI_ENDPOINT`
and `AZURE_OPENAI_DEPLOYMENT` set.
