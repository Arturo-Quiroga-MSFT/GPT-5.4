---
title: "APIM Gateway for Foundry Models"
description: "Azure API Management as a production-grade AI gateway in front of Microsoft Foundry / Azure OpenAI, with progressively richer examples."
author: "arturoquiroga"
ms.date: "2026-03-10"
ms.topic: "overview"
keywords: ["azure api management", "apim", "foundry", "azure openai", "ai gateway", "gpt-5.4"]
---

## Overview

This subdirectory places Azure API Management (APIM) in front of your Foundry / Azure OpenAI deployments
to gain the benefits you need for a production-grade release: load balancing across backend pools,
token-level rate limiting, centralized observability, and security hardening, all without changing
the application code that already works in the sibling directories.

The approach is deliberately incremental. Start with the smoke test, confirm the gateway is in the
path, and layer in policies and infrastructure only once the basics are solid.

## Architecture

```text
your scripts (OpenAI SDK)
        │
        │  APIM subscription key
        ▼
Azure API Management
  ├── inbound policies  (auth, rate-limit, routing)
  ├── backend pool      (one or more Foundry/AOAI endpoints)
  └── outbound policies (metrics, conditional logging)
        │
        │  managed identity token
        ▼
Foundry / Azure OpenAI endpoint
```

Clients never see the backend URL. APIM authenticates to the backend with its own managed identity,
decoupling client auth from backend auth.

## Contents

| File | Purpose |
|---|---|
| `config.py` | APIM-specific client setup (subscription key auth, gateway base URL) |
| `requirements.txt` | Minimal dependencies for this subdirectory |
| `.env.example` | Environment variable template |
| `01_gateway_basics.py` | Smoke test: proves the gateway is in the path via response headers |

## Prerequisites

- An APIM instance (Developer tier is fine for experimentation; Standard v2 for production)
- The Azure OpenAI / Foundry API imported into APIM with the Responses endpoint (`/openai/v1/responses`) included
- The APIM instance's system-assigned managed identity granted **Cognitive Services OpenAI User** on your Foundry / AOAI resource
- An APIM product with a subscription key

## Setup

Copy `.env.example` to `.env` in this directory and fill in your values:

```bash
cp .env.example .env
```

The two required variables are:

- `APIM_ENDPOINT`: your gateway base URL, e.g. `https://my-apim.azure-api.net/aoai`
- `APIM_SUBSCRIPTION_KEY`: found in the APIM portal under Subscriptions

The scripts share the same virtual environment as the rest of the workspace. Activate it from the
repo root before running anything here:

```bash
source ../.venv/bin/activate
```

## Running the smoke test

```bash
cd apim_gateway
python 01_gateway_basics.py
```

The output confirms two things:

1. The model replied (backend routing works)
2. APIM-specific response headers are present (`x-ms-region`, `apim-request-id`, etc.), proving the
   request went through the gateway and not directly to the backend

## Streaming and logging

When using streaming mode (`stream=True`), do not attempt to log the response body at the APIM
layer via `log-to-eventhub`. Reading the response body forces APIM to buffer the full response
before forwarding, which breaks streaming for the client.

The recommended pattern for production:

- Log the request body at the gateway (always safe, always complete JSON)
- Use the `azure-openai-emit-token-metric` policy for token counts (reads headers, not the body,
  so it is safe for streaming)
- For non-streaming requests, log the response body conditionally via an inbound variable that
  checks for `"stream": true`
- For streaming token counting in application code, set `stream_options: {"include_usage": true}`
  to receive a final usage SSE chunk before `[DONE]`

## Reusing scripts from other subdirectories

The scripts in `gpt-5.4_python_scripts/` and `gpt54_pro_comparison/` work through the gateway
without modification. Change `AZURE_OPENAI_ENDPOINT` to your `APIM_ENDPOINT` and swap
`DefaultAzureCredential` for a subscription key header, or simply point them at this directory's
`config.py`.

## What comes next

Once `01_gateway_basics.py` is green, the natural progression is:

1. Token-limit policy (`azure-openai-token-limit`) to prevent quota exhaustion
2. Backend pool with two or more Foundry endpoints for automatic failover on 429 / 5xx
3. Retry policy with exponential backoff
4. Diagnostic Logs to a Log Analytics workspace for request-level observability
5. `azure-openai-emit-token-metric` to App Insights for per-deployment token dashboards
6. Bicep / azd infra definition to make the full setup reproducible
