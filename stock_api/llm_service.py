"""
LLM service — agentic analysis pipeline as a streaming SSE generator.

Phases
------
1. Non-streaming call: model issues get_stock_history tool call.
   Yields: status, tool_call, tool_result (or error).

2. Streaming call: model generates the main analysis text using the tool result.
   Yields: analysis_start, analysis_delta (per token), analysis_done.

3. Non-streaming agentic follow-up loop: model picks and executes its own
   suggested next step, handling any additional tool calls transparently.
   Yields: followup_start, followup_tool_call, followup_tool_result (if needed),
           followup_text, done.

All events use the SSE format:
    data: {"type": "<event_type>", "data": {...}}\n\n

Phase 3 text is yielded as a single followup_text event rather than streamed
token-by-token because the tool call decision must happen non-streaming first.
Phase 2 (the main analysis) provides the primary streaming experience.
"""

import json
from typing import Generator

from config import DEPLOYMENT, get_client
from stock_service import TOOLS, TOOL_DISPATCH

client = get_client()

FOLLOWUP_PROMPT = (
    "Please now automatically choose and execute the single most insightful "
    "follow-up analysis you suggested at the end of your previous response. "
    "Do not ask me which one — just pick it, do it, and show the result."
)


def _sse(event_type: str, data: dict) -> str:
    return f"data: {json.dumps({'type': event_type, 'data': data})}\n\n"


def run_analysis_stream(ticker: str, days: int) -> Generator[str, None, None]:
    """
    Sync generator — yields SSE-formatted strings for StreamingResponse.
    FastAPI runs sync generators in a thread-pool automatically.
    """
    query = (
        f"Retrieve and analyse the stock price history for {ticker} "
        f"over the last {days} days. Give me: the opening and latest close price, "
        f"the period high and low, overall % change, average daily volume, "
        f"and a brief commentary on the trend."
    )

    total_input = 0
    total_output = 0

    # ── Phase 1: first call — model issues tool call ──────────────────
    yield _sse("status", {"message": f"Calling {DEPLOYMENT}…"})

    try:
        resp1 = client.responses.create(model=DEPLOYMENT, input=query, tools=TOOLS)
    except Exception as e:
        yield _sse("error", {"message": f"Model call failed: {e}"})
        return

    total_input += resp1.usage.input_tokens
    total_output += resp1.usage.output_tokens

    tool_outputs = []

    for item in resp1.output:
        if item.type == "function_call":
            args = json.loads(item.arguments)
            yield _sse("tool_call", {"name": item.name, "args": args})

            result_str = TOOL_DISPATCH[item.name](args)
            result_data = json.loads(result_str)

            if result_data.get("error"):
                yield _sse("error", {"message": result_data["error"]})
                return

            yield _sse("tool_result", result_data)
            tool_outputs.append(
                {
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": result_str,
                }
            )

    # ── Phase 2: streaming analysis ───────────────────────────────────
    yield _sse("analysis_start", {})

    final_id = None
    try:
        stream = client.responses.create(
            model=DEPLOYMENT,
            input=resp1.output + tool_outputs,
            tools=TOOLS,
            stream=True,
        )
        for event in stream:
            if event.type == "response.output_text.delta":
                yield _sse("analysis_delta", {"delta": event.delta})
            elif event.type == "response.completed":
                final_id = event.response.id
                total_input += event.response.usage.input_tokens
                total_output += event.response.usage.output_tokens
    except Exception as e:
        yield _sse("error", {"message": f"Streaming analysis failed: {e}"})
        return

    yield _sse("analysis_done", {})

    # ── Phase 3: follow-up — non-streaming agentic loop ───────────────
    yield _sse("followup_start", {})

    try:
        followup_resp = client.responses.create(
            model=DEPLOYMENT,
            input=FOLLOWUP_PROMPT,
            previous_response_id=final_id,
            tools=TOOLS,
        )
        total_input += followup_resp.usage.input_tokens
        total_output += followup_resp.usage.output_tokens

        # Agentic loop: handle any tool calls the follow-up triggers
        while any(item.type == "function_call" for item in followup_resp.output):
            fu_tool_outputs = []
            for item in followup_resp.output:
                if item.type == "function_call":
                    args = json.loads(item.arguments)
                    yield _sse("followup_tool_call", {"name": item.name, "args": args})

                    result_str = TOOL_DISPATCH[item.name](args)
                    result_data = json.loads(result_str)
                    yield _sse("followup_tool_result", result_data)

                    fu_tool_outputs.append(
                        {
                            "type": "function_call_output",
                            "call_id": item.call_id,
                            "output": result_str,
                        }
                    )

            followup_resp = client.responses.create(
                model=DEPLOYMENT,
                input=followup_resp.output + fu_tool_outputs,
                previous_response_id=followup_resp.id,
                tools=TOOLS,
            )
            total_input += followup_resp.usage.input_tokens
            total_output += followup_resp.usage.output_tokens

        yield _sse("followup_text", {"text": followup_resp.output_text})

    except Exception as e:
        yield _sse("error", {"message": f"Follow-up failed: {e}"})
        return

    # ── Done ──────────────────────────────────────────────────────────
    yield _sse(
        "done",
        {
            "usage": {
                "total_input_tokens": total_input,
                "total_output_tokens": total_output,
            }
        },
    )


# ── Chat stream (multi-turn, user-driven) ─────────────────────────────
CHAT_SYSTEM_PROMPT = (
    "You are a concise financial analysis assistant with access to real-time stock price data. "
    "When asked about a stock, use the get_stock_history tool to fetch actual price data before analysing. "
    "Keep responses focused and actionable. After each analysis, suggest one follow-up the user might explore."
)


def run_chat_stream(message: str, previous_response_id: str | None) -> Generator[str, None, None]:
    """
    Single-turn handler for the chat endpoint.  Accepts any free-form message
    and an optional previous_response_id for conversation continuity.

    No automatic follow-up phase — the user drives all follow-up turns.

    Events yielded (in order):
        status → [tool_call → tool_result]? → analysis_start →
        analysis_delta* → analysis_done → done | error

    The `done` event includes `response_id` so the frontend can chain the
    next message without resending history.
    """
    total_input = 0
    total_output = 0

    yield _sse("status", {"message": f"Calling {DEPLOYMENT}…"})

    # ── Step 1: Non-streaming call (detect / execute tool calls) ──────
    kwargs: dict = {
        "model": DEPLOYMENT,
        "input": message,
        "tools": TOOLS,
        "instructions": CHAT_SYSTEM_PROMPT,
    }
    if previous_response_id:
        kwargs["previous_response_id"] = previous_response_id

    try:
        resp = client.responses.create(**kwargs)
    except Exception as e:
        yield _sse("error", {"message": f"Model call failed: {e}"})
        return

    total_input += resp.usage.input_tokens
    total_output += resp.usage.output_tokens

    tool_outputs = []
    for item in resp.output:
        if item.type == "function_call":
            args = json.loads(item.arguments)
            yield _sse("tool_call", {"name": item.name, "args": args})

            result_str = TOOL_DISPATCH[item.name](args)
            result_data = json.loads(result_str)

            if result_data.get("error"):
                yield _sse("error", {"message": result_data["error"]})
                return

            yield _sse("tool_result", result_data)
            tool_outputs.append(
                {
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": result_str,
                }
            )

    # ── Step 2a: Tool calls happened — stream the synthesis ───────────
    yield _sse("analysis_start", {})
    response_id: str | None = None

    if tool_outputs:
        try:
            stream = client.responses.create(
                model=DEPLOYMENT,
                input=resp.output + tool_outputs,
                tools=TOOLS,
                stream=True,
            )
            for event in stream:
                if event.type == "response.output_text.delta":
                    yield _sse("analysis_delta", {"delta": event.delta})
                elif event.type == "response.completed":
                    response_id = event.response.id
                    total_input += event.response.usage.input_tokens
                    total_output += event.response.usage.output_tokens
        except Exception as e:
            yield _sse("error", {"message": f"Streaming failed: {e}"})
            return
    else:
        # ── Step 2b: No tool calls — emit text from step 1 directly ───
        yield _sse("analysis_delta", {"delta": resp.output_text})
        response_id = resp.id

    yield _sse("analysis_done", {})
    yield _sse(
        "done",
        {
            "response_id": response_id,
            "usage": {
                "total_input_tokens": total_input,
                "total_output_tokens": total_output,
            },
        },
    )
