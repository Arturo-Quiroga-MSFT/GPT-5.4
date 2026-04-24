# Microsoft Agent Framework — `reasoning_effort`, streaming & web search

Standalone samples answering the question:

> Does the Microsoft Agent Framework (MAF) SDK support specifying model
> parameters such as `reasoning_effort`?

**Short answer:** Yes — in MAF Python, every `ChatClient` and `Agent` is generic
over a `ChatOptions` `TypedDict`. You pass model parameters (including
`reasoning={"effort": ...}`) via `default_options=` at construction time or
`options=` at call time. Provider-specific options are added by extending the
base `ChatOptions` `TypedDict`. See upstream sample
[`typed_options.py`](https://github.com/microsoft/agent-framework/blob/main/python/samples/02-agents/typed_options.py).

> Tested live against `gpt-5.4` on Azure OpenAI Responses with
> `agent-framework==1.2.0` (Python 3.11). All five samples pass.

## Supported chat providers (Python)

Per the [official docs](https://learn.microsoft.com/en-us/agent-framework/agents/?pivots=programming-language-python#supported-chat-providers):

| Provider | Server-side conversation state |
|---|---|
| Foundry Agent | Yes |
| Azure OpenAI Responses | Yes |
| Azure OpenAI Chat Completion | No |
| OpenAI Responses | Yes |
| OpenAI Chat Completion | No |
| Anthropic Claude | No |
| Amazon Bedrock | No |
| GitHub Copilot | No |
| Ollama (OpenAI-compatible) | No |
| Any other `SupportsChatGetResponse` | Varies |

These samples target **Azure OpenAI Responses** via `OpenAIChatClient(azure_endpoint=..., credential=...)`, the canonical wiring from the [Azure provider sample](https://github.com/microsoft/agent-framework/blob/main/python/samples/02-agents/providers/azure/openai_client_basic.py).

### Responses vs Chat Completions in MAF Python

The class names are slightly counter‑intuitive:

| MAF class | API | `api_version` required? |
|---|---|---|
| `OpenAIChatClient` | **Responses** (newer, preferred) | No |
| `OpenAIChatCompletionClient` | Chat Completions (legacy) | Yes |

Samples 01–04 use the Responses path. Sample 05 shows the Chat Completions path for contrast. Confirmed by the official [Azure provider README](https://github.com/microsoft/agent-framework/tree/main/python/samples/02-agents/providers/azure).

## Files

| File | What it shows |
|---|---|
| [`config.py`](config.py) | Factories for both Azure OpenAI Responses and Chat Completions clients (Entra ID) |
| [`01_reasoning_effort_sweep.py`](01_reasoning_effort_sweep.py) | Same prompt across all `reasoning_effort` levels with a `rich` comparison table (Responses) |
| [`02_typed_options.py`](02_typed_options.py) | Defines `OpenAIReasoningChatOptions(TypedDict)`; construction-time default + per-run override on both `ChatClient` and `Agent` |
| [`03_streaming.py`](03_streaming.py) | `async for chunk in agent.run(prompt, stream=True)` combined with `reasoning.effort` ([docs](https://learn.microsoft.com/en-us/agent-framework/agents/?pivots=programming-language-python#streaming-responses)) |
| [`04_web_search.py`](04_web_search.py) | Hosted Web Search tool via `client.get_web_search_tool(...)` ([docs](https://learn.microsoft.com/en-us/agent-framework/agents/tools/web-search?pivots=programming-language-python)) — Responses-only |
| [`05_chat_completions_contrast.py`](05_chat_completions_contrast.py) | Same prompt against `OpenAIChatCompletionClient` (Chat Completions API) for contrast |

## Setup

```bash
cd maf_reasoning_effort
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
az login   # DefaultAzureCredential will pick this up
```

Set environment variables (a project-root `.env` with these already works):

```bash
export AZURE_OPENAI_ENDPOINT="https://<your-resource>.openai.azure.com"
# Either name works — MAF samples prefer AZURE_OPENAI_MODEL,
# but config.py also accepts AZURE_OPENAI_DEPLOYMENT (used elsewhere in this repo).
export AZURE_OPENAI_MODEL="gpt-5.4"           # your deployment name
# Optional — only needed for the Chat Completions sample (05):
export AZURE_OPENAI_API_VERSION="2025-04-01-preview"
```

## Run

```bash
python 01_reasoning_effort_sweep.py
python 02_typed_options.py
python 03_streaming.py
python 04_web_search.py
python 05_chat_completions_contrast.py
```

## Key API surface

```python
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient, OpenAIChatOptions
from azure.identity import DefaultAzureCredential

# Provider-specific TypedDict for reasoning models
class OpenAIReasoningChatOptions(OpenAIChatOptions, total=False):
    temperature: None         # unsupported on reasoning models
    top_p: None

client = OpenAIChatClient(
    model="gpt-5.4",
    azure_endpoint="https://<your-resource>.openai.azure.com",
    credential=DefaultAzureCredential(),
)

agent = Agent[OpenAIReasoningChatOptions](
    client=client,
    instructions="You are concise.",
    default_options={"reasoning": {"effort": "medium"}, "max_tokens": 500},
    tools=[client.get_web_search_tool(user_location={"city": "Toronto", "region": "CA"})],
)

# Streaming + per-run override
async for chunk in agent.run("Hard problem", stream=True,
                             options={"reasoning": {"effort": "high"}}):
    if chunk.text:
        print(chunk.text, end="", flush=True)
```

Provider parity note: Anthropic uses `thinking={"type": "enabled", "budget_tokens": ...}`
instead of `reasoning.effort`; the same `default_options` / `options` mechanism
applies — you swap the `TypedDict` for the provider's options class.

## Gotchas discovered while testing

Even within MAF, the **reasoning-effort knob is named differently per API surface**
because MAF passes the options dict straight through to the underlying SDK:

| API / Provider | Option key |
|---|---|
| Azure OpenAI / OpenAI **Responses** (`OpenAIChatClient`) | `"reasoning": {"effort": "low\|medium\|high\|..."}` |
| Azure OpenAI / OpenAI **Chat Completions** (`OpenAIChatCompletionClient`) | `"reasoning_effort": "low\|medium\|high\|..."` |
| Anthropic Claude | `"thinking": {"type": "enabled", "budget_tokens": N}` |

The call-site mechanism is identical (`default_options=` or per-run `options=`); only the schema differs.

A few other small footguns worth knowing:

- `client.get_response(...)` requires a list of `Message` objects — passing a bare string raises `'str' object has no attribute 'role'`. `agent.run("...")` accepts a string directly.
- `response.usage_details` is a plain `dict` (`{'input_token_count', 'output_token_count', 'total_token_count'}`), not an attribute object — use `.get(...)`.
- The model identifier on a response is `response.model`, not `response.model_id`.
- Hosted `client.get_web_search_tool(...)` only exists on the Responses path; it is not available on `OpenAIChatCompletionClient`.
