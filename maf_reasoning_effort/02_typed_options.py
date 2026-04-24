#!/usr/bin/env python3
"""
02 — Typed options & per-run override.

Adapted from the upstream MAF sample
https://github.com/microsoft/agent-framework/blob/main/python/samples/02-agents/typed_options.py
to target Azure OpenAI with Entra ID.

Shows three things:
1. A provider-specific `TypedDict` that marks parameters unsupported on
   reasoning models as `None`, so the type checker flags misuse.
2. Setting `reasoning.effort` at agent construction via `default_options`.
3. Overriding `reasoning.effort` for a single `agent.run(...)` call.
"""

from __future__ import annotations

import asyncio

from agent_framework import Agent, Message
from agent_framework.openai import OpenAIChatOptions

from config import get_chat_client


class OpenAIReasoningChatOptions(OpenAIChatOptions, total=False):
    """Options for OpenAI/Azure-OpenAI reasoning models (e.g., gpt-5.4, o-series).

    Reasoning models reject several sampling parameters; mark them
    ``None`` so static type checkers catch misuse.
    """

    temperature: None
    top_p: None
    frequency_penalty: None
    presence_penalty: None
    logit_bias: None
    logprobs: None
    top_logprobs: None
    stop: None


async def demo_chat_client_reasoning() -> None:
    print("\n=== ChatClient with reasoning options ===")
    client = get_chat_client()

    response = await client.get_response(
        [Message("user", contents=["What is 2 + 2? Show one short reasoning step."])],
        options={
            "max_tokens": 200,
            "reasoning": {"effort": "low"},
        },
    )
    print(f"Response: {response.text}")
    print(f"Model: {response.model}")


async def demo_agent_default_and_override() -> None:
    print("\n=== Agent with default_options + per-run override ===")

    agent = Agent[OpenAIReasoningChatOptions](
        client=get_chat_client(),
        name="math-tutor",
        instructions="You are a concise math tutor. Show numbered steps.",
        default_options={
            "max_tokens": 400,
            "reasoning": {"effort": "medium"},  # default for every run
        },
    )

    # Uses the default (medium)
    r1 = await agent.run("What is 25 * 47?")
    print(f"[medium] {r1.text}")

    # Override just for this call
    r2 = await agent.run(
        "Prove that the sum of two odd numbers is even.",
        options={"reasoning": {"effort": "high"}},
    )
    print(f"[high override] {r2.text}")


async def main() -> None:
    await demo_chat_client_reasoning()
    await demo_agent_default_and_override()


if __name__ == "__main__":
    asyncio.run(main())
