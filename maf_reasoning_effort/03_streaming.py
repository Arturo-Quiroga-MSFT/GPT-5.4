#!/usr/bin/env python3
"""
03 — Streaming responses with Microsoft Agent Framework.

Per the official docs:
https://learn.microsoft.com/en-us/agent-framework/agents/?pivots=programming-language-python#streaming-responses

Streaming is exposed via ``agent.run(prompt, stream=True)`` which yields
``AgentResponseUpdate`` chunks; print ``chunk.text`` as it arrives.

Combines with ``reasoning_effort`` from sample 01 to show that model
parameters and streaming compose cleanly.
"""

from __future__ import annotations

import asyncio

from agent_framework import Agent

from config import get_chat_client


async def main() -> None:
    agent = Agent(
        client=get_chat_client(),
        name="StreamingTutor",
        instructions="You are a concise math tutor. Show numbered steps.",
        default_options={
            "max_tokens": 600,
            "reasoning": {"effort": "medium"},
        },
    )

    prompt = (
        "Explain why the sum of the first n positive integers equals n(n+1)/2. "
        "Use a short numbered proof."
    )
    print(f"User: {prompt}\nAssistant: ", end="", flush=True)

    async for chunk in agent.run(prompt, stream=True):
        if chunk.text:
            print(chunk.text, end="", flush=True)
    print()


if __name__ == "__main__":
    asyncio.run(main())
