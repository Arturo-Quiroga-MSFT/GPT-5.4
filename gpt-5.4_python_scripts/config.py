"""
Shared configuration and client setup for GPT-5.4 experiments.

Uses the standard OpenAI Python SDK with base_url pointed at the
Azure OpenAI Responses API v1 endpoint.  Authentication is via
Microsoft Entra ID (DefaultAzureCredential).
"""

import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import OpenAI

load_dotenv()

# ── Azure OpenAI settings ─────────────────────────────────────────────
ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/")
DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5.4")
BASE_URL = f"{ENDPOINT}/openai/v1/"

# ── Entra ID (DefaultAzureCredential) ─────────────────────────────────
_credential = DefaultAzureCredential()
_token_provider = get_bearer_token_provider(
    _credential, "https://cognitiveservices.azure.com/.default"
)

# ── Model constants ───────────────────────────────────────────────────
MODEL = "gpt-5.4"
MAX_INPUT_TOKENS = 272_000
MAX_OUTPUT_TOKENS = 128_000
REASONING_EFFORTS = ["none", "low", "medium", "high", "xhigh"]


def get_client() -> OpenAI:
    """Return an OpenAI client pointed at the Azure Responses API v1 endpoint."""
    return OpenAI(
        base_url=BASE_URL,
        api_key=_token_provider(),
    )
