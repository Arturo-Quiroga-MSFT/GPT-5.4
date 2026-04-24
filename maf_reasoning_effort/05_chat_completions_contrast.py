#!/usr/bin/env python3
"""
05 — Chat Completions API counterpart (for contrast with the Responses-API samples).

MAF Python provides two Azure OpenAI clients:

* ``OpenAIChatClient``           → Responses API (newer; no api_version needed)
* ``OpenAIChatCompletionClient`` → Chat Completions API (legacy; api_version required)

This sample shows the Chat Completions path so you can compare against
``01_reasoning_effort_sweep.py`` (which uses the Responses path). The
``reasoning_effort`` options-dict pattern is identical across both.

Note: hosted tools like ``client.get_web_search_tool(...)`` are only
available on the Responses path.
"""

from __future__ import annotations

import asyncio

from agent_framework import Agent

from config import get_chat_completion_client


async def main() -> None:
    # Chat Completions exposes reasoning effort under a different
    # top-level parameter name (``reasoning_effort``) than Responses
    # (``reasoning={"effort": ...}``). MAF passes options straight
    # through to the underlying SDK, so we use the SDK-native name here.
    agent = Agent(
        client=get_chat_completion_client(),
        name="ChatCompletionsAgent",
        instructions="You are concise. Show numbered reasoning steps.",
        default_options={
            "max_tokens": 400,
            "reasoning_effort": "low",
        },
    )

    prompt = (
        "A farmer has 17 sheep. All but 9 run away. "
        "How many sheep does the farmer have left? Explain step by step."
    )
    print(f"User: {prompt}")

    response = await agent.run(prompt)
    print(f"Assistant: {response.text}")


if __name__ == "__main__":
    asyncio.run(main())
