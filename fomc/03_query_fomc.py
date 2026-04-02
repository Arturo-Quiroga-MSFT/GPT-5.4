#!/usr/bin/env python3
"""
03_query_fomc.py — Interactive RAG Q&A over FOMC meeting minutes

Retrieves relevant chunks from the ChromaDB vector store, builds a
grounded prompt, and sends it to GPT-5.4 for analysis.  Supports
multi-turn conversation with streaming output.

Usage:
    python 03_query_fomc.py                          # interactive chat
    python 03_query_fomc.py -q "What drove rate hikes in 2023?"
"""

import argparse
import json
import time

import chromadb
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config import (
    CHROMA_DIR,
    DEPLOYMENT,
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL,
    get_client,
)

console = Console()

SYSTEM_PROMPT = """\
You are a Federal Reserve policy analyst AI. You answer questions about \
U.S. monetary policy using excerpts from official FOMC (Federal Open Market \
Committee) meeting minutes.

Rules:
- Base your answers ONLY on the provided FOMC excerpts.
- Cite the meeting date(s) you reference (format: YYYY-MM-DD).
- If the excerpts don't contain enough information, say so clearly.
- When analyzing sentiment, classify the tone as hawkish, dovish, or neutral \
  and explain why.
- Be concise but thorough. Use bullet points for clarity when appropriate.
"""

TOP_K = 10  # number of chunks to retrieve


# ── Retrieval ─────────────────────────────────────────────────────────

def retrieve(client, collection, query: str, top_k: int = TOP_K) -> list[dict]:
    """Embed the query and retrieve the top-K most relevant chunks."""
    q_resp = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=query,
        dimensions=EMBEDDING_DIMENSIONS,
    )
    q_embedding = q_resp.data[0].embedding

    results = collection.query(
        query_embeddings=[q_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text": doc,
            "date": meta.get("date", "unknown"),
            "similarity": 1 - dist,  # cosine distance → similarity
        })
    return chunks


def build_context(chunks: list[dict]) -> str:
    """Format retrieved chunks into a context block for the LLM."""
    parts = []
    for i, c in enumerate(chunks, 1):
        date = c["date"]
        # Format YYYYMMDD → YYYY-MM-DD
        if len(date) == 8:
            date = f"{date[:4]}-{date[4:6]}-{date[6:]}"
        parts.append(
            f"[Excerpt {i} — FOMC Meeting {date} "
            f"(relevance: {c['similarity']:.2f})]\n{c['text']}"
        )
    return "\n\n---\n\n".join(parts)


# ── Display helpers ───────────────────────────────────────────────────

def show_sources(chunks: list[dict]):
    """Print a compact table of retrieved sources."""
    table = Table(title="Retrieved Sources", show_lines=False)
    table.add_column("#", style="dim", width=3)
    table.add_column("Meeting Date", style="cyan")
    table.add_column("Relevance", justify="right", style="green")
    table.add_column("Preview", max_width=60)

    for i, c in enumerate(chunks, 1):
        date = c["date"]
        if len(date) == 8:
            date = f"{date[:4]}-{date[4:6]}-{date[6:]}"
        preview = c["text"][:100].replace("\n", " ") + "…"
        table.add_row(str(i), date, f"{c['similarity']:.3f}", preview)

    console.print(table)


# ── Query with streaming ─────────────────────────────────────────────

def query_fomc(client, collection, question: str, prev_id: str | None = None):
    """Run a single RAG query with streaming output. Returns response id."""
    t0 = time.perf_counter()

    # 1. Retrieve
    chunks = retrieve(client, collection, question)
    show_sources(chunks)

    context = build_context(chunks)

    user_message = (
        f"FOMC EXCERPTS:\n\n{context}\n\n"
        f"---\n\n"
        f"USER QUESTION: {question}"
    )

    # 2. Stream the answer
    console.print("\n[bold]GPT-5.4 Analysis:[/bold]\n")

    kwargs = {
        "model": DEPLOYMENT,
        "instructions": SYSTEM_PROMPT,
        "input": user_message,
        "reasoning": {"effort": "high", "summary": "auto"},
        "stream": True,
    }
    if prev_id:
        kwargs["previous_response_id"] = prev_id

    stream = client.responses.create(**kwargs)

    response_id = None
    in_reasoning = False

    for event in stream:
        if event.type == "response.output_text.delta":
            if in_reasoning:
                console.print("\n")
                in_reasoning = False
            console.print(event.delta, end="", highlight=False)

        elif event.type == "response.reasoning_summary_text.delta":
            in_reasoning = True
            console.print(f"[dim italic]{event.delta}[/dim italic]", end="")

        elif event.type == "response.completed":
            response_id = event.response.id
            elapsed = time.perf_counter() - t0
            usage = event.response.usage
            console.print(
                f"\n\n[dim]Tokens — input: {usage.input_tokens}  "
                f"output: {usage.output_tokens}  "
                f"total: {usage.total_tokens}[/dim]"
            )
            console.print(f"[dim]Elapsed: {elapsed:.1f}s[/dim]")

    return response_id


# ── Interactive loop ──────────────────────────────────────────────────

def interactive(client, collection):
    """Multi-turn chat loop."""
    console.print(
        Panel(
            "[bold]FOMC Minutes Analysis — RAG Chat[/bold]\n\n"
            "Ask questions about Federal Reserve monetary policy.\n"
            "Type [bold cyan]quit[/bold cyan] or [bold cyan]exit[/bold cyan] to stop.\n"
            "Type [bold cyan]new[/bold cyan] to start a fresh conversation.",
            title="🏦 FOMC Analyst",
        )
    )

    prev_id = None

    while True:
        console.print()
        question = console.input("[bold cyan]You:[/bold cyan] ").strip()

        if not question:
            continue
        if question.lower() in ("quit", "exit", "q"):
            console.print("[dim]Goodbye![/dim]")
            break
        if question.lower() == "new":
            prev_id = None
            console.print("[yellow]Starting new conversation…[/yellow]")
            continue

        prev_id = query_fomc(client, collection, question, prev_id)


# ── Main ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Query FOMC minutes with RAG + GPT-5.4")
    parser.add_argument("-q", "--question", type=str, help="Single question (non-interactive)")
    args = parser.parse_args()

    # Open ChromaDB
    chroma = chromadb.PersistentClient(path=CHROMA_DIR)
    try:
        collection = chroma.get_collection("fomc_minutes")
    except Exception:
        console.print(
            "[red]Vector store not found. Run 02_index_fomc.py first.[/red]"
        )
        return

    console.print(f"[dim]Loaded {collection.count()} chunks from vector store[/dim]")

    openai_client = get_client()

    if args.question:
        query_fomc(openai_client, collection, args.question)
    else:
        interactive(openai_client, collection)


if __name__ == "__main__":
    main()
