"""
Stock Analysis API — FastAPI application entry point.

Start the server:
    cd stock_api
    uvicorn main:app --reload --port 8000

The API exposes a single streaming endpoint:
    POST /api/analyse   →  SSE stream of analysis events

And a health check:
    GET  /api/health    →  { "status": "ok" }

CORS is configured to allow requests from the Vite dev server (port 5173)
and from localhost:3000 for other common setups.  Adjust ALLOWED_ORIGINS for
production.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from models import AnalyseRequest
from llm_service import run_analysis_stream

# Origins allowed to call the API — extend as needed for production
ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Vite default
    "http://localhost:3000",  # Create-React-App / other setups
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

app = FastAPI(
    title="Stock Analysis API",
    description="Streaming GPT-5.4 stock analysis backed by yfinance.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/analyse")
def analyse(req: AnalyseRequest):
    """
    Stream a full analysis of the requested ticker over the given number of days.

    Returns a text/event-stream where each line is:
        data: {"type": "<event>", "data": {...}}

    Event types (in order):
        status            — model call initiated
        tool_call         — model issued get_stock_history
        tool_result       — yfinance data returned (includes daily_closes for charting)
        analysis_start    — model starting to generate analysis text
        analysis_delta    — one token of analysis text (delta: str)
        analysis_done     — analysis text complete
        followup_start    — follow-up phase beginning
        followup_tool_call  — follow-up triggered a tool call (optional)
        followup_tool_result — follow-up tool result (optional)
        followup_text     — complete follow-up analysis text
        done              — pipeline complete (includes usage token counts)
        error             — something went wrong (message: str)
    """
    return StreamingResponse(
        run_analysis_stream(req.ticker, req.days),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # disables nginx buffering when behind a proxy
            "Connection": "keep-alive",
        },
    )
