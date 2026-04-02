"""
Shared configuration for Chat Completions API vs Responses API comparison.

Two clients are provided:
  - get_responses_client()  → OpenAI pointed at Azure /openai/v1/
  - get_chat_client()       → AzureOpenAI using the standard chat/completions endpoint

Both authenticate via Microsoft Entra ID (DefaultAzureCredential).
Both target the same GPT-5.4 deployment; the only difference is the API surface.
"""

import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI, OpenAI

load_dotenv()

# ── Azure OpenAI settings ─────────────────────────────────────────────
ENDPOINT  = os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/")
DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5.4")

# Responses API — uses the new /openai/v1/ base path
RESPONSES_BASE_URL = f"{ENDPOINT}/openai/v1/"

# Chat Completions API — uses the current GA preview that includes
# reasoning_effort support for GPT-5.4
CHAT_API_VERSION = "2025-04-01-preview"

# ── Entra ID (DefaultAzureCredential) ─────────────────────────────────
_credential      = DefaultAzureCredential()
_token_provider  = get_bearer_token_provider(
    _credential, "https://cognitiveservices.azure.com/.default"
)

# ── Shared constants ──────────────────────────────────────────────────
MODEL = DEPLOYMENT
REASONING_EFFORTS = ["low", "medium", "high"]


def get_responses_client() -> OpenAI:
    """
    Responses API client.

    Uses the /openai/v1/ base URL which exposes client.responses.create().
    The Entra token is passed as the api_key (the SDK sends it as a Bearer token).
    """
    return OpenAI(
        base_url=RESPONSES_BASE_URL,
        api_key=_token_provider(),
    )


def get_chat_client() -> AzureOpenAI:
    """
    Chat Completions API client.

    Standard AzureOpenAI client using azure_endpoint + api_version convention.
    Exposes client.chat.completions.create().
    """
    return AzureOpenAI(
        azure_endpoint=ENDPOINT,
        azure_ad_token_provider=_token_provider,
        api_version=CHAT_API_VERSION,
    )
