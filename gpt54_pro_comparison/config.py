"""
Shared configuration for GPT-5.4 vs GPT-5.4-pro comparison scripts.

Both models are served via the same Azure OpenAI Responses API endpoint;
the only difference is the deployment name.  Add a second deployment entry
to your .env:

    AZURE_OPENAI_DEPLOYMENT=gpt-5.4
    AZURE_OPENAI_DEPLOYMENT_PRO=gpt-5.4-pro
"""

import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import OpenAI

load_dotenv()

# ── Azure OpenAI settings ─────────────────────────────────────────────
ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/")
BASE_URL = f"{ENDPOINT}/openai/v1/"

_credential = DefaultAzureCredential()
_token_provider = get_bearer_token_provider(
    _credential, "https://cognitiveservices.azure.com/.default"
)

# ── Model constants ───────────────────────────────────────────────────
GPT54 = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5.4")
GPT54_PRO = os.getenv("AZURE_OPENAI_DEPLOYMENT_PRO", "gpt-5.4-pro")
MODELS = [GPT54, GPT54_PRO]

MODEL_STYLES = {
    GPT54: "bold cyan",
    GPT54_PRO: "bold green",
}


def get_client() -> OpenAI:
    """Return an OpenAI client pointed at the Azure Responses API v1 endpoint."""
    return OpenAI(
        base_url=BASE_URL,
        api_key=_token_provider(),
    )
