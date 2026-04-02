"""
FOMC service — provides RAG query and sentiment analysis for the stock API.

Reuses the fomc/ ChromaDB vector store and embedding pipeline.
"""

import importlib.util
import json
import os
from typing import Generator

from config import DEPLOYMENT, get_client

# ── Lazy-load chromadb so the API starts even if it's not installed ────
chromadb = None  # type: ignore[assignment]

def _ensure_chromadb():
    global chromadb
    if chromadb is None:
        import chromadb as _cdb
        chromadb = _cdb

# ── Load fomc config for shared constants ──────────────────────────────
_fomc_config_path = os.path.join(os.path.dirname(__file__), "..", "fomc", "config.py")
_fomc_cfg = None

def _ensure_fomc_config():
    global _fomc_cfg, CHROMA_DIR, EMBEDDING_MODEL, EMBEDDING_DIMENSIONS, DATA_DIR
    if _fomc_cfg is not None:
        return
    _spec = importlib.util.spec_from_file_location("fomc_config", _fomc_config_path)
    _fomc_cfg = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_fomc_cfg)
    CHROMA_DIR = _fomc_cfg.CHROMA_DIR
    EMBEDDING_MODEL = _fomc_cfg.EMBEDDING_MODEL
    EMBEDDING_DIMENSIONS = _fomc_cfg.EMBEDDING_DIMENSIONS
    DATA_DIR = _fomc_cfg.DATA_DIR

CHROMA_DIR: str = ""
EMBEDDING_MODEL: str = ""
EMBEDDING_DIMENSIONS: int = 0
DATA_DIR: str = ""

TOP_K = 10

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

def _get_collection():
    """Open the FOMC ChromaDB collection, or None if it doesn't exist."""
    _ensure_fomc_config()
    _ensure_chromadb()
    if not os.path.isdir(CHROMA_DIR):
        return None
    chroma = chromadb.PersistentClient(path=CHROMA_DIR)
    try:
        return chroma.get_collection("fomc_minutes")
    except Exception:
        return None


def _retrieve(collection, query: str, top_k: int = TOP_K) -> list[dict]:
    """Embed query and retrieve top-K chunks."""
    client = get_client()
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
        date_str = meta.get("date", "unknown")
        if len(date_str) == 8:
            date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
        chunks.append({
            "text": doc,
            "date": date_str,
            "similarity": round(1 - dist, 3),
        })
    return chunks


def _build_context(chunks: list[dict]) -> str:
    """Format retrieved chunks into a context block for the LLM."""
    parts = []
    for i, c in enumerate(chunks, 1):
        parts.append(
            f"[Excerpt {i} — FOMC Meeting {c['date']} "
            f"(relevance: {c['similarity']:.2f})]\n{c['text']}"
        )
    return "\n\n---\n\n".join(parts)


def _sse(event_type: str, data: dict) -> str:
    return f"data: {json.dumps({'type': event_type, 'data': data})}\n\n"


def get_fomc_status() -> dict:
    """Return info about the FOMC vector store availability."""
    try:
        _ensure_chromadb()
    except ImportError:
        return {"available": False, "chunk_count": 0, "meeting_count": 0}
    collection = _get_collection()
    if collection is None:
        return {"available": False, "chunk_count": 0, "meeting_count": 0}

    count = collection.count()
    # Estimate meeting count from unique dates
    if count > 0:
        metas = collection.get(limit=count, include=["metadatas"])["metadatas"]
        dates = {m.get("date") for m in metas if "date" in m}
        meeting_count = len(dates)
    else:
        meeting_count = 0

    return {"available": True, "chunk_count": count, "meeting_count": meeting_count}


def run_fomc_chat_stream(
    message: str, previous_response_id: str | None = None
) -> Generator[str, None, None]:
    """Stream a RAG-grounded FOMC analysis as SSE events."""
    collection = _get_collection()
    if collection is None or collection.count() == 0:
        yield _sse("error", {
            "message": "FOMC vector store not found. Run fomc/01_scrape_fomc.py and fomc/02_index_fomc.py first."
        })
        return

    # 1. Retrieve relevant chunks
    yield _sse("status", {"message": "Searching FOMC minutes…"})
    chunks = _retrieve(collection, message)

    yield _sse("fomc_sources", {
        "sources": [{"date": c["date"], "similarity": c["similarity"],
                      "preview": c["text"][:120].replace("\n", " ")} for c in chunks]
    })

    context = _build_context(chunks)
    user_message = (
        f"FOMC EXCERPTS:\n\n{context}\n\n"
        f"---\n\n"
        f"USER QUESTION: {message}"
    )

    # 2. Stream the answer
    yield _sse("analysis_start", {"message": "Analyzing…"})

    kwargs = {
        "model": DEPLOYMENT,
        "instructions": SYSTEM_PROMPT,
        "input": user_message,
        "reasoning": {"effort": "high", "summary": "auto"},
        "stream": True,
    }
    if previous_response_id:
        kwargs["previous_response_id"] = previous_response_id

    try:
        client = get_client()
        stream = client.responses.create(**kwargs)
    except Exception as e:
        yield _sse("error", {"message": f"Model call failed: {e}"})
        return

    response_id = None

    for event in stream:
        if event.type == "response.output_text.delta":
            yield _sse("analysis_delta", {"delta": event.delta})

        elif event.type == "response.reasoning_summary_text.delta":
            yield _sse("reasoning_delta", {"delta": event.delta})

        elif event.type == "response.completed":
            response_id = event.response.id
            usage = event.response.usage
            yield _sse("done", {
                "response_id": response_id,
                "usage": {
                    "input_tokens": usage.input_tokens,
                    "output_tokens": usage.output_tokens,
                    "total_tokens": usage.total_tokens,
                },
            })
