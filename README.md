---
title: GPT-5.4 Experimentation Workspace
description: Python scripts and a full-stack app for experimenting with GPT-5.4 on Azure OpenAI
author: Arturo Quiroga
ms.date: 2026-04-02
ms.topic: tutorial
keywords:
  - gpt-5.4
  - gpt-5.4-pro
  - azure openai
  - responses api
  - chat completions api
  - reasoning model
---

# GPT-5.4 Experimentation Workspace

Hands-on scripts and a full-stack demo app for experimenting with **GPT-5.4** and **GPT-5.4-pro**,
OpenAI's most capable reasoning models, deployed through **Azure OpenAI**.

## Model highlights

| Property | Value |
|---|---|
| Model IDs | `gpt-5.4` · `gpt-5.4-pro` |
| Context window | 272 K input / 128 K output (1 M coming soon) |
| Reasoning effort | `none` · `low` · `medium` · `high` · `xhigh` |
| Primary API | **Responses API** (`client.responses.create`) |
| Capabilities | Reasoning, vision, structured output, tool calling, web search, streaming, computer use (coming soon) |
| Azure regions | East US2, Sweden Central (Global Standard) |
| Pricing | $2.50 / M input — $0.25 / M cached — $15 / M output |
| Access | [Registration required](https://aka.ms/OAI/gpt53codexaccess) |

> **References**
>
> * [Azure Foundry Models — GPT-5.4](https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure?tabs=global-standard-aoai%2Cglobal-standard&pivots=azure-openai#gpt-54)
> * [Introducing GPT-5.4 — OpenAI blog](https://openai.com/index/introducing-gpt-5-4/)

## Prerequisites

* Python 3.10+
* Node.js 20+ (for `stock_ui` only)
* An Azure subscription with an Azure OpenAI resource
* A `gpt-5.4` deployment (and optionally `gpt-5.4-pro`)
* Azure CLI logged in (`az login`) for Entra ID authentication

## Quick start

```bash
# 1  Clone and enter the repo
cd GPT-5.4

# 2  Create a virtual environment with uv
uv venv .venv && source .venv/bin/activate

# 3  Install dependencies
uv pip install -r requirements.txt

# 4  Configure credentials
cp .env.sample .env         # then edit .env with your endpoint

# 5  Authenticate with Azure
az login

# 6  Run the smoke test
cd gpt-5.4_python_scripts && python 01_hello_gpt54.py
```

## Project structure

```text
GPT-5.4/
├── .env.sample                        # Azure credentials template
├── .gitignore
├── config.py                          # Root shared client & constants
├── requirements.txt                   # Root dependencies
├── README.md
│
├── gpt-5.4_python_scripts/            # Core GPT-5.4 feature scripts (Responses API)
│   ├── config.py
│   ├── requirements.txt
│   ├── 01_hello_gpt54.py
│   ├── 02_reasoning_effort.py
│   ├── 03_structured_output.py
│   ├── 04_vision.py
│   ├── 05_tool_calling.py
│   ├── 06_streaming.py
│   ├── 07_multi_turn.py
│   └── 08_web_search.py
│
├── gpt54_pro_comparison/              # GPT-5.4 vs GPT-5.4-pro head-to-head
│   ├── config.py
│   ├── requirements.txt
│   ├── 01_hello_comparison.py
│   ├── 02_reasoning_comparison.py
│   ├── 03_structured_output_comparison.py
│   ├── 04_tool_calling_comparison.py
│   ├── 05_streaming_comparison.py
│   └── 06_multi_turn_comparison.py
│
├── api_comparison/                    # Chat Completions API vs Responses API — PSA guide
│   ├── config.py
│   ├── requirements.txt
│   ├── README.md                      # In-depth trade-off analysis and decision tree
│   ├── 01_hello_comparison.py
│   ├── 02_reasoning_effort.py
│   ├── 03_multi_turn.py
│   ├── 04_tool_calling.py
│   ├── 05_streaming.py
│   └── 06_structured_output.py
│
├── fomc/                              # FOMC minutes RAG analysis pipeline
│   ├── config.py
│   ├── requirements.txt
│   ├── README.md
│   ├── 01_scrape_fomc.py
│   ├── 02_index_fomc.py
│   ├── 03_query_fomc.py
│   ├── 04_sentiment_fomc.py
│   ├── data/                          # Scraped minutes (gitignored)
│   └── chroma_db/                     # Vector store (gitignored)
│
├── finance/                           # Finance-focused experiments
│   ├── stock_history.py
│   └── advanced_finance_healthcare.ipynb
│
├── stock_api/                         # FastAPI backend for the stock demo app
│   ├── config.py
│   ├── requirements.txt
│   ├── main.py
│   ├── models.py
│   ├── llm_service.py
│   ├── stock_service.py
│   └── fomc_service.py
│
└── stock_ui/                          # React + TypeScript front-end
    ├── package.json
    ├── vite.config.ts
    └── src/
        ├── App.tsx
        ├── api/client.ts
        ├── components/
        └── hooks/
```

## Experiment scripts

### `gpt-5.4_python_scripts/` — Core GPT-5.4 features

All scripts use the **Responses API**.

| # | Script | What it demonstrates |
|---|---|---|
| 01 | `01_hello_gpt54.py` | Minimal call — send a prompt, print the reply and token usage |
| 02 | `02_reasoning_effort.py` | Sweep `none` → `xhigh`, compare quality, latency, and cost |
| 03 | `03_structured_output.py` | Strict JSON-schema output with `text.format` |
| 04 | `04_vision.py` | Image understanding (URL or local file) |
| 05 | `05_tool_calling.py` | Function/tool calling with real weather and stock price tools |
| 06 | `06_streaming.py` | Stream tokens in real time including reasoning summary events |
| 07 | `07_multi_turn.py` | Multi-turn conversation via `previous_response_id` |
| 08 | `08_web_search.py` | `web_search_preview` built-in tool for live web grounding |

### `gpt54_pro_comparison/` — GPT-5.4 vs GPT-5.4-pro

Side-by-side benchmarks across all major capabilities.
Requires a second deployment — add `AZURE_OPENAI_DEPLOYMENT_PRO=gpt-5.4-pro` to your `.env`.

| # | Script | What it compares |
|---|---|---|
| 01 | `01_hello_comparison.py` | Response quality, token usage, latency |
| 02 | `02_reasoning_comparison.py` | Reasoning depth at `low` / `medium` / `high` effort |
| 03 | `03_structured_output_comparison.py` | JSON schema compliance and latency |
| 04 | `04_tool_calling_comparison.py` | Tool selection accuracy and round-trip latency |
| 05 | `05_streaming_comparison.py` | Time-to-first-token and total streaming latency |
| 06 | `06_multi_turn_comparison.py` | Context retention over a 3-turn conversation |

### `api_comparison/` — Chat Completions API vs Responses API

PSA guidance for helping partners choose the right API surface for GPT-5.4.
Each script implements the same scenario on both APIs side-by-side and prints
a summary table.  See [`api_comparison/README.md`](api_comparison/README.md)
for the full trade-off analysis and decision tree.

| # | Script | What it compares |
|---|---|---|
| 01 | `01_hello_comparison.py` | SDK shape, response object paths, token field names |
| 02 | `02_reasoning_effort.py` | Flat param vs nested dict — and reasoning summary visibility |
| 03 | `03_multi_turn.py` | Client-owned history vs `previous_response_id` — token economics |
| 04 | `04_tool_calling.py` | Schema nesting, result submission format, built-in tools |
| 05 | `05_streaming.py` | Event model — reasoning summary stream vs text-only chunks |
| 06 | `06_structured_output.py` | `response_format.json_schema` vs `text.format` param path |

**When to use each API — quick rule of thumb:**

| Use Chat Completions | Use Responses API |
|---|---|
| LangChain / Semantic Kernel / AutoGen stack | New builds with own orchestration layer |
| Must own / encrypt conversation history | Auditable reasoning chain required |
| Need `n > 1` completions or `logprobs` | Built-in web search / file search / code interpreter |
| Migrating an existing OpenAI app | Long multi-turn sessions (token cost scaling) |

### `fomc/` — FOMC Minutes RAG Analysis

A complete Retrieval-Augmented Generation pipeline for analyzing Federal Reserve
monetary-policy documents.

| # | Script | What it does |
|---|---|---|
| 01 | `01_scrape_fomc.py` | Scrapes FOMC minutes from federalreserve.gov, saves as plain text |
| 02 | `02_index_fomc.py` | Chunks text, embeds via `text-embedding-3-large`, stores in ChromaDB |
| 03 | `03_query_fomc.py` | Interactive multi-turn RAG chat with streaming and source attribution |
| 04 | `04_sentiment_fomc.py` | Structured sentiment: hawkish/dovish score, rate outlook, inflation concern |

### `finance/` — Finance experiments

| File | Description |
|---|---|
| `stock_history.py` | GPT-5.4 uses tool calling to fetch OHLCV history for any ticker, produce a written analysis, a colour-coded price table, and a PNG chart |
| `advanced_finance_healthcare.ipynb` | Notebook exploring finance and healthcare use-cases |

### `stock_api/` + `stock_ui/` — Full-stack demo app

A FastAPI backend and React + TypeScript front-end that combine stock analysis,
FOMC sentiment, and GPT-5.4 reasoning into a single interactive application.

```bash
# Start the API
cd stock_api && uvicorn main:app --reload

# Start the UI (separate terminal)
cd stock_ui && npm install && npm run dev
```

## Key Responses API patterns

The SDK uses `from openai import OpenAI` with `base_url` pointing at
`https://<resource>.openai.azure.com/openai/v1/`. No `api_version` needed.
Authentication is via `DefaultAzureCredential` (Entra ID).

### Basic call

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://my-resource.openai.azure.com/openai/v1/",
    api_key=token_provider(),   # from get_bearer_token_provider
)
response = client.responses.create(
    model="gpt-5.4",
    input="Your prompt here",
)
print(response.output_text)
```

### With reasoning effort and summary

```python
response = client.responses.create(
    model="gpt-5.4",
    input="Hard problem",
    reasoning={"effort": "high", "summary": "auto"},
)
# See what the model thought about
for item in response.output:
    if item.type == "reasoning":
        for s in item.summary:
            print(s.text)
```

### Multi-turn (no message resend)

```python
r1 = client.responses.create(model="gpt-5.4", input="First question")
r2 = client.responses.create(
    model="gpt-5.4",
    input="Follow-up",
    previous_response_id=r1.id,   # only thing needed
)
```

### Built-in web search

```python
response = client.responses.create(
    model="gpt-5.4",
    input="Latest Azure AI announcements?",
    tools=[{"type": "web_search_preview"}],
)
```

### Structured output

```python
response = client.responses.create(
    model=DEPLOYMENT,
    input="Give me data",
    text={"format": {"type": "json_schema", "name": "my_schema",
                     "schema": MY_SCHEMA, "strict": True}},
)
```
