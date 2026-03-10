---
title: GPT-5.4 Experimentation Workspace
description: A set of Python scripts to experiment with GPT-5.4 on Azure OpenAI using the Responses API
author: Arturo Quiroga
ms.date: 2026-03-10
ms.topic: tutorial
keywords:
  - gpt-5.4
  - gpt-5.4-pro
  - azure openai
  - responses api
  - reasoning model
---

# GPT-5.4 Experimentation Workspace

Hands-on scripts for experimenting with **GPT-5.4** and **GPT-5.4-pro**, OpenAI's most capable
reasoning models, deployed through **Azure OpenAI** and accessed exclusively via
the **Responses API**.

## Model highlights

| Property | Value |
|---|---|
| Model IDs | `gpt-5.4` · `gpt-5.4-pro` |
| Context window | 272 K input / 128 K output (1 M coming soon) |
| Reasoning effort | `none` · `low` · `medium` · `high` · `xhigh` |
| API | **Responses API** (`client.responses.create`) |
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
cd gpt-5.4_python_scripts
python 01_hello_gpt54.py
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
├── gpt-5.4_python_scripts/            # Core GPT-5.4 feature scripts
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
└── finance/                           # Finance-focused experiments
    ├── stock_history.py
    └── advanced_finance_healthcare.ipynb
```

## Experiment scripts

### `gpt-5.4_python_scripts/` — Core GPT-5.4 features

All scripts use the **Responses API** — the Chat Completions API is deprecated.

| # | Script | What it demonstrates |
|---|---|---|
| 01 | `01_hello_gpt54.py` | Minimal call — send a prompt, print the reply and token usage |
| 02 | `02_reasoning_effort.py` | Sweep `none` → `xhigh`, compare quality, latency, and cost |
| 03 | `03_structured_output.py` | Strict JSON-schema output with `text.format` |
| 04 | `04_vision.py` | Image understanding (URL or local file) |
| 05 | `05_tool_calling.py` | Function/tool calling with mock implementations |
| 06 | `06_streaming.py` | Stream tokens in real time with reasoning summaries |
| 07 | `07_multi_turn.py` | Multi-turn conversation via `previous_response_id` |
| 08 | `08_web_search.py` | `web_search_preview` tool for live web grounding |

### `gpt54_pro_comparison/` — GPT-5.4 vs GPT-5.4-pro

Side-by-side benchmarks showing how the pro model compares across all major capabilities.
Requires a second deployment — add `AZURE_OPENAI_DEPLOYMENT_PRO=gpt-5.4-pro` to your `.env`.

| # | Script | What it compares |
|---|---|---|
| 01 | `01_hello_comparison.py` | Response quality, token usage, latency |
| 02 | `02_reasoning_comparison.py` | Reasoning depth at `low` / `medium` / `high` effort |
| 03 | `03_structured_output_comparison.py` | JSON schema compliance and latency |
| 04 | `04_tool_calling_comparison.py` | Tool selection accuracy and round-trip latency |
| 05 | `05_streaming_comparison.py` | Time-to-first-token and total streaming latency |
| 06 | `06_multi_turn_comparison.py` | Context retention over a 3-turn conversation |

### `finance/` — Finance experiments

| File | Description |
|---|---|
| `stock_history.py` | GPT-5.4 uses tool calling to fetch daily OHLCV history for any ticker over a user-specified number of days, then produces a written analysis, a colour-coded close price table, and a PNG line chart |
| `advanced_finance_healthcare.ipynb` | Notebook exploring finance and healthcare use-cases with GPT-5.4 |

## Key Responses API patterns

The SDK uses `from openai import OpenAI` with `base_url` pointing at
`https://<resource>.openai.azure.com/openai/v1/`. No `api_version` needed.
Auth is via `DefaultAzureCredential` (Entra ID).

### Basic call

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://my-resource.openai.azure.com/openai/v1/",
    api_key=token,  # from get_bearer_token_provider
)
response = client.responses.create(
    model="gpt-5.4",
    input="Your prompt here",
)
print(response.output_text)
```

### With reasoning effort

```python
response = client.responses.create(
    model="gpt-5.4",
    input="Hard math problem",
    reasoning={"effort": "xhigh"},
)
```

### Multi-turn (no message resend)

```python
r1 = client.responses.create(model="gpt-5.4", input="First question")
r2 = client.responses.create(
    model="gpt-5.4",
    input="Follow-up",
    previous_response_id=r1.id,
)
```

### Structured output

```python
response = client.responses.create(
    model=DEPLOYMENT,
    input="Give me data",
    text={"format": {"type": "json_schema", "json_schema": MY_SCHEMA}},
)
```


# GPT-5.4 Experimentation Workspace

Hands-on scripts for experimenting with **GPT-5.4**, OpenAI's most capable
reasoning model, deployed through **Azure OpenAI** and accessed exclusively via
the **Responses API**.

## Model highlights

| Property | Value |
|---|---|
| Model ID | `gpt-5.4` (2026-03-05) |
| Context window | 272 K input / 128 K output (1 M coming soon) |
| Reasoning effort | `none` · `low` · `medium` · `high` · `xhigh` |
| API | **Responses API** (`client.responses.create`) |
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
* An Azure subscription with an Azure OpenAI resource
* A `gpt-5.4` deployment (apply for access at the link above)
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
python 01_hello_gpt54.py
```

## Experiment scripts

All scripts use the **Responses API** — the Chat Completions API is deprecated.

| # | Script | What it demonstrates |
|---|---|---|
| 01 | `01_hello_gpt54.py` | Minimal call — send a prompt, print the reply and token usage |
| 02 | `02_reasoning_effort.py` | Sweep `none` → `xhigh`, compare quality, latency, and cost |
| 03 | `03_structured_output.py` | Strict JSON-schema output with `text.format` |
| 04 | `04_vision.py` | Image understanding (URL or local file) |
| 05 | `05_tool_calling.py` | Function/tool calling with mock implementations |
| 06 | `06_streaming.py` | Stream tokens in real time with reasoning summaries |
| 07 | `07_multi_turn.py` | Multi-turn conversation via `previous_response_id` |
| 08 | `08_web_search.py` | `web_search_preview` tool for live web grounding |

## Project structure

```text
GPT-5.4/
├── .env.sample              # Template for Azure credentials
├── .gitignore
├── config.py                # Shared client & constants
├── requirements.txt
├── README.md
├── 01_hello_gpt54.py
├── 02_reasoning_effort.py
├── 03_structured_output.py
├── 04_vision.py
├── 05_tool_calling.py
├── 06_streaming.py
├── 07_multi_turn.py
└── 08_web_search.py
```

## Key Responses API patterns

The SDK uses `from openai import OpenAI` with `base_url` pointing at
`https://<resource>.openai.azure.com/openai/v1/`. No `api_version` needed.
Auth is via `DefaultAzureCredential` (Entra ID).

### Basic call

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://my-resource.openai.azure.com/openai/v1/",
    api_key=token,  # from get_bearer_token_provider
)
response = client.responses.create(
    model="gpt-5.4",
    input="Your prompt here",
)
print(response.output_text)
```

### With reasoning effort

```python
response = client.responses.create(
    model="gpt-5.4",
    input="Hard math problem",
    reasoning={"effort": "xhigh"},
)
```

### Multi-turn (no message resend)

```python
r1 = client.responses.create(model="gpt-5.4", input="First question")
r2 = client.responses.create(
    model="gpt-5.4",
    input="Follow-up",
    previous_response_id=r1.id,
)
```

### Structured output

```python
response = client.responses.create(
    model=DEPLOYMENT,
    input="Give me data",
    text={"format": {"type": "json_schema", "json_schema": MY_SCHEMA}},
)
```
