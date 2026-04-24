"""
Shared MAF client factories.

Targets Azure OpenAI via Microsoft Agent Framework, authenticated with
Entra ID (``DefaultAzureCredential``).

MAF Python class → API mapping (note the slightly counter-intuitive names):

    ``OpenAIChatClient``           → Responses API   (newer, preferred)
    ``OpenAIChatCompletionClient`` → Chat Completions (legacy)

The Responses API does **not** require an ``api_version``; this module
omits it for that path. The Chat Completions factory keeps a default
since that API still requires one.
"""

from __future__ import annotations

import os

from agent_framework.openai import OpenAIChatClient, OpenAIChatCompletionClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()

ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/")
# Accept either AZURE_OPENAI_MODEL (MAF convention) or
# AZURE_OPENAI_DEPLOYMENT (used elsewhere in this repo).
MODEL = (
    os.getenv("AZURE_OPENAI_MODEL")
    or os.getenv("AZURE_OPENAI_DEPLOYMENT")
    or "gpt-5.4"
)
CHAT_COMPLETIONS_API_VERSION = os.getenv(
    "AZURE_OPENAI_API_VERSION", "2025-04-01-preview"
)

REASONING_EFFORTS = ["none", "low", "medium", "high", "xhigh"]


def get_chat_client() -> OpenAIChatClient:
    """Return an Azure-OpenAI **Responses** client (Entra ID auth).

    No ``api_version`` is passed — the Responses API doesn't need one.
    """
    return OpenAIChatClient(
        model=MODEL,
        azure_endpoint=ENDPOINT,
        credential=DefaultAzureCredential(),
    )


def get_chat_completion_client() -> OpenAIChatCompletionClient:
    """Return an Azure-OpenAI **Chat Completions** client (Entra ID auth).

    Provided for contrast with :func:`get_chat_client`. The Chat
    Completions API still requires ``api_version``.
    """
    return OpenAIChatCompletionClient(
        model=MODEL,
        azure_endpoint=ENDPOINT,
        api_version=CHAT_COMPLETIONS_API_VERSION,
        credential=DefaultAzureCredential(),
    )
