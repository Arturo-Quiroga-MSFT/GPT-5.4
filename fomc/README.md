---
title: "FOMC Minutes Analysis with RAG + GPT-5.4"
description: "Retrieval-Augmented Generation pipeline that scrapes, indexes, and analyzes Federal Open Market Committee meeting minutes using GPT-5.4 on Azure OpenAI."
author: "arturoquiroga"
ms.date: "2026-03-11"
ms.topic: "tutorial"
keywords: ["fomc", "rag", "vector search", "chromadb", "embeddings", "federal reserve", "monetary policy", "gpt-5.4", "azure openai", "sentiment analysis"]
---

## Overview

A complete RAG (Retrieval-Augmented Generation) pipeline for analyzing Federal Open Market Committee
meeting minutes. The system scrapes official FOMC documents from the Federal Reserve website, chunks
and embeds them into a local vector store, and answers monetary-policy questions through GPT-5.4 with
full source attribution.

Inspired by the [MathWorks FOMC Challenge Project](https://github.com/mathworks/MATLAB-Simulink-Challenge-Project-Hub/tree/main/projects/Federal%20Open%20Market%20Committee%20Minutes%20Analysis%20with%20Large%20Language%20Models),
reimplemented entirely in Python using the Azure OpenAI Responses API.

## Architecture

```text
Federal Reserve website
        │
        │  01_scrape_fomc.py (requests + BeautifulSoup)
        ▼
data/<YYYYMMDD>.txt            plain-text minutes files
        │
        │  02_index_fomc.py (text-embedding-3-large → ChromaDB)
        ▼
chroma_db/                     local vector store (cosine similarity)
        │
        │  03_query_fomc.py   retrieves top-K chunks → GPT-5.4 streaming
        │  04_sentiment.py    structured JSON extraction per meeting
        ▼
GPT-5.4 (Azure OpenAI Responses API)
```

## Contents

| File | Purpose |
|---|---|
| `config.py` | FOMC-specific settings (embedding model, chunk size, paths); imports root Azure OpenAI config |
| `01_scrape_fomc.py` | Scrapes FOMC minutes from federalreserve.gov and saves as `data/<YYYYMMDD>.txt` |
| `02_index_fomc.py` | Chunks text, embeds via `text-embedding-3-large`, stores in ChromaDB |
| `03_query_fomc.py` | Interactive multi-turn RAG chat with streaming output and source attribution |
| `04_sentiment_fomc.py` | Structured sentiment extraction: hawkish/dovish score, inflation concern, rate outlook |
| `requirements.txt` | Additional dependencies beyond root (`beautifulsoup4`, `chromadb`) |

## Quick start

```bash
# Install additional dependencies
uv pip install -r fomc/requirements.txt

# 1. Scrape FOMC minutes (all available, or filter by year)
cd fomc
python 01_scrape_fomc.py --year 2023 2024 2025

# 2. Chunk and embed into vector store
python 02_index_fomc.py

# 3. Interactive Q&A
python 03_query_fomc.py

# 4. Structured sentiment analysis
python 04_sentiment_fomc.py --last 8
```

## Scripts in detail

### 01 — Scrape FOMC minutes

Downloads meeting minutes as plain text from the Federal Reserve website.

```bash
python 01_scrape_fomc.py                  # all available years
python 01_scrape_fomc.py --year 2024      # only 2024
python 01_scrape_fomc.py --year 2023 2024 # multiple years
```

Files are cached in `data/`; re-running skips already-downloaded documents.

### 02 — Index into vector store

Splits each document into ~500-token chunks with overlap, embeds them using
`text-embedding-3-large` (1024 dimensions), and stores everything in a local ChromaDB instance.

```bash
python 02_index_fomc.py           # incremental — only indexes new files
python 02_index_fomc.py --reset   # wipe and rebuild from scratch
```

### 03 — RAG query chat

Retrieves the most relevant chunks via cosine similarity, builds a grounded prompt,
and streams GPT-5.4's analysis with a sources table.

```bash
python 03_query_fomc.py                                         # interactive chat
python 03_query_fomc.py -q "What drove the September 2024 rate cut?"  # single question
```

Features:

- Multi-turn conversation via `previous_response_id`
- Streaming output with reasoning summaries
- Source attribution table showing meeting dates and relevance scores
- Type `new` to reset conversation context, `quit` to exit

### 04 — Structured sentiment analysis

Sends each meeting's full text through GPT-5.4 with a strict JSON schema to extract:

- **Hawkish/dovish score** (-1.0 to 1.0)
- **Overall tone** classification
- **Inflation concern** level
- **Labor market view**
- **Rate outlook** narrative
- **Dissent** presence
- **Notable quote** (verbatim)
- **Executive summary**

```bash
python 04_sentiment_fomc.py                    # all meetings in data/
python 04_sentiment_fomc.py --year 2024        # only 2024
python 04_sentiment_fomc.py --last 5           # last 5 meetings
```

Results are saved to `data/sentiment_results.json` for further analysis.

## Configuration

Key settings in `config.py`:

| Setting | Default | Description |
|---|---|---|
| `EMBEDDING_MODEL` | `text-embedding-3-large` | Azure OpenAI embedding model |
| `EMBEDDING_DIMENSIONS` | `1024` | Dimensionality slice (cost-efficient vs full 3072) |
| `CHUNK_SIZE` | `500` | Target tokens per chunk |
| `CHUNK_OVERLAP` | `50` | Overlap tokens between consecutive chunks |

## Data sources

- [FOMC Calendar & Minutes](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm) — official
  Federal Reserve website
- Minutes are available from 2014 onward (current calendar page) with historical archives going further back

## Potential extensions

- **Additional data sources**: SEC filings, earnings call transcripts, financial news
- **Time-series visualization**: Plot hawkish/dovish scores alongside Fed Funds rate changes
- **Market impact analysis**: Correlate sentiment shifts with equity/bond market reactions using `yfinance`
- **Integration with stock UI**: Add an FOMC analysis tab to the existing `stock_ui` dashboard
