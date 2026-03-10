"""
Shared configuration for APIM-gateway experiments.

Auth model
----------
Clients authenticate to APIM via a subscription key (sent as the
'Ocp-Apim-Subscription-Key' header).  APIM authenticates onward to
the Foundry / Azure OpenAI backend using its own managed identity, so
the backend endpoint is never exposed to callers.

Required environment variables (see .env.example)
--------------------------------------------------
APIM_ENDPOINT             - Full base URL of the APIM gateway, e.g.
                            https://my-apim.azure-api.net/aoai
APIM_SUBSCRIPTION_KEY     - APIM product/subscription key
AZURE_OPENAI_DEPLOYMENT   - Deployment name, e.g. gpt-5.4  (default: gpt-5.4)
AZURE_OPENAI_DEPLOYMENT_PRO - Optional second deployment (default: gpt-5.4-pro)

Optional fallback (for non-gateway comparisons / direct calls)
--------------------------------------------------------------
AZURE_OPENAI_ENDPOINT     - Direct Azure OpenAI endpoint (only needed when
                            running direct-vs-gateway comparison scripts)
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ── APIM gateway settings ─────────────────────────────────────────────
APIM_ENDPOINT = os.environ["APIM_ENDPOINT"].rstrip("/")
APIM_SUBSCRIPTION_KEY = os.environ["APIM_SUBSCRIPTION_KEY"]

# The Responses API lives at <base>/openai/v1/
APIM_BASE_URL = f"{APIM_ENDPOINT}/openai/v1/"

# ── Model constants (same deployment names as other subdirs) ──────────
DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5.4")
DEPLOYMENT_PRO = os.getenv("AZURE_OPENAI_DEPLOYMENT_PRO", "gpt-5.4-pro")

REASONING_EFFORTS = ["none", "low", "medium", "high", "xhigh"]


def get_client() -> OpenAI:
    """
    Return an OpenAI client routed through the APIM gateway.

    The subscription key is passed via the standard 'Ocp-Apim-Subscription-Key'
    header.  A placeholder value is supplied to the SDK's api_key field to
    satisfy its validation; APIM strips that header before forwarding and
    substitutes its own managed-identity token for the backend leg.
    """
    return OpenAI(
        base_url=APIM_BASE_URL,
        api_key="apim-managed",          # placeholder — auth is the sub key below
        default_headers={
            "Ocp-Apim-Subscription-Key": APIM_SUBSCRIPTION_KEY,
        },
    )
