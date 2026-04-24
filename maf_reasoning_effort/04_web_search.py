#!/usr/bin/env python3
"""
04 — Web Search tool with Microsoft Agent Framework.

Per the official docs:
https://learn.microsoft.com/en-us/agent-framework/agents/tools/web-search?pivots=programming-language-python

The chat client exposes ``get_web_search_tool(...)`` returning a hosted
tool you pass via ``tools=[...]`` to the ``Agent``. Web Search
availability depends on the provider (Azure OpenAI Responses and
OpenAI Responses support it; Chat Completion clients do not).

Combines streaming + ``reasoning_effort`` + the hosted web search tool.
"""

from __future__ import annotations

import asyncio

from agent_framework import Agent

from config import get_chat_client


async def main() -> None:
    client = get_chat_client()

    web_search = client.get_web_search_tool(
        user_location={"city": "Toronto", "region": "CA"},
    )

    agent = Agent(
        client=client,
        name="WebSearchAssistant",
        instructions=(
            "You are a helpful assistant. Use the web search tool when the "
            "question requires current information. Cite sources inline."
        ),
        tools=[web_search],
        default_options={"reasoning": {"effort": "low"}},
    )

    question = "What were the top headlines about Microsoft Azure this week?"
    print(f"User: {question}\nAssistant: ", end="", flush=True)

    async for chunk in agent.run(question, stream=True):
        if chunk.text:
            print(chunk.text, end="", flush=True)
    print()


if __name__ == "__main__":
    asyncio.run(main())
