#!/usr/bin/env python3
"""
02_index_fomc.py — Chunk and embed FOMC minutes into a ChromaDB vector store

Reads the plain-text files produced by 01_scrape_fomc.py, splits them
into overlapping chunks, computes embeddings via Azure OpenAI
text-embedding-3-large, and stores everything in a local ChromaDB.

Usage:
    python 02_index_fomc.py            # index all files in data/
    python 02_index_fomc.py --reset    # wipe the DB and re-index
"""

import argparse
import os
import re
import shutil
import time

import chromadb
from rich.console import Console
from rich.progress import track

from config import (
    CHROMA_DIR,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DATA_DIR,
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL,
    get_client,
)

console = Console()

# ── Chunking ──────────────────────────────────────────────────────────

def _approx_token_count(text: str) -> int:
    """Rough token count (1 token ≈ 4 chars for English)."""
    return len(text) // 4


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Split text into chunks of ~chunk_size tokens with overlap.
    Splits on paragraph boundaries first, then sentence boundaries.
    Enforces a hard max of 7500 tokens per chunk (embedding API limit is 8192).
    """
    hard_max = 7500  # safety margin below 8192 embedding limit
    paragraphs = re.split(r"\n{2,}", text)
    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        para_tokens = _approx_token_count(para)

        # If a single paragraph exceeds hard_max, split it by sentences
        if para_tokens > hard_max:
            sentences = re.split(r"(?<=[.!?])\s+", para)
            for sent in sentences:
                sent_tokens = _approx_token_count(sent)
                if current_tokens + sent_tokens > chunk_size and current:
                    chunks.append("\n\n".join(current))
                    current = []
                    current_tokens = 0
                current.append(sent)
                current_tokens += sent_tokens
            continue

        if current_tokens + para_tokens > chunk_size and current:
            chunks.append("\n\n".join(current))

            # Keep overlap: walk back from the end
            overlap_parts: list[str] = []
            overlap_count = 0
            for p in reversed(current):
                pt = _approx_token_count(p)
                if overlap_count + pt > overlap:
                    break
                overlap_parts.insert(0, p)
                overlap_count += pt
            current = overlap_parts
            current_tokens = overlap_count

        current.append(para)
        current_tokens += para_tokens

    if current:
        chunks.append("\n\n".join(current))

    # Final safety pass: split any chunk that's still too long
    safe_chunks = []
    for chunk in chunks:
        if _approx_token_count(chunk) <= hard_max:
            safe_chunks.append(chunk)
        else:
            # Brute-force split by character count
            max_chars = hard_max * 4
            for i in range(0, len(chunk), max_chars):
                safe_chunks.append(chunk[i : i + max_chars])

    return safe_chunks


# ── Embedding ─────────────────────────────────────────────────────────

def embed_batch(client, texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts via Azure OpenAI."""
    resp = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
        dimensions=EMBEDDING_DIMENSIONS,
    )
    return [item.embedding for item in resp.data]


# ── Main ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Index FOMC minutes into ChromaDB")
    parser.add_argument("--reset", action="store_true", help="Wipe and rebuild the index")
    args = parser.parse_args()

    if args.reset and os.path.exists(CHROMA_DIR):
        console.print("[yellow]Resetting vector store…[/yellow]")
        shutil.rmtree(CHROMA_DIR)

    # Gather text files
    if not os.path.isdir(DATA_DIR):
        console.print("[red]No data/ directory found. Run 01_scrape_fomc.py first.[/red]")
        return

    txt_files = sorted(f for f in os.listdir(DATA_DIR) if f.endswith(".txt"))
    if not txt_files:
        console.print("[red]No .txt files in data/. Run 01_scrape_fomc.py first.[/red]")
        return

    console.print(f"Found [bold green]{len(txt_files)}[/bold green] minutes files")

    # ChromaDB setup
    chroma = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = chroma.get_or_create_collection(
        name="fomc_minutes",
        metadata={"hnsw:space": "cosine"},
    )

    # Check what's already indexed
    existing_dates = set()
    if collection.count() > 0:
        existing_meta = collection.get()["metadatas"]
        existing_dates = {m["date"] for m in existing_meta if "date" in m}

    openai_client = get_client()
    total_chunks = 0
    batch_size = 64  # embedding API batch limit

    for filename in track(txt_files, description="Indexing…"):
        date_str = filename.replace(".txt", "")
        if date_str in existing_dates:
            continue

        filepath = os.path.join(DATA_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = chunk_text(text)
        if not chunks:
            continue

        # Process in batches
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            embeddings = embed_batch(openai_client, batch)

            ids = [f"{date_str}_chunk_{i + j}" for j in range(len(batch))]
            metadatas = [
                {"date": date_str, "year": date_str[:4], "chunk_index": i + j}
                for j in range(len(batch))
            ]

            collection.add(
                ids=ids,
                documents=batch,
                embeddings=embeddings,
                metadatas=metadatas,
            )
            time.sleep(0.1)  # rate-limit courtesy

        total_chunks += len(chunks)

    console.print(
        f"\n[bold green]Done![/bold green] "
        f"Indexed {total_chunks} new chunks. "
        f"Total in DB: {collection.count()}"
    )


if __name__ == "__main__":
    main()
