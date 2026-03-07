#!/usr/bin/env python3
"""
03 — Structured output with JSON schema  (Responses API)

Asks GPT-5.4 for data in a strict JSON schema, demonstrating
the built-in structured-output capability.
"""

import json
import time
from config import DEPLOYMENT, get_client
from rich import print as rprint
from rich.panel import Panel

client = get_client()

SCHEMA = {
    "type": "object",
    "properties": {
        "cities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name":       {"type": "string"},
                    "country":    {"type": "string"},
                    "population": {"type": "integer"},
                    "fun_fact":   {"type": "string"},
                },
                "required": ["name", "country", "population", "fun_fact"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["cities"],
    "additionalProperties": False,
}

t0 = time.perf_counter()
response = client.responses.create(
    model=DEPLOYMENT,
    input="Give me 3 interesting cities in South America with population and a fun fact.",
    text={"format": {"type": "json_schema", "name": "city_comparison", "schema": SCHEMA, "strict": True}},
)
elapsed = time.perf_counter() - t0

data = json.loads(response.output_text)
rprint(Panel(json.dumps(data, indent=2, ensure_ascii=False),
             title="Structured Output"))
rprint(f"[dim]Tokens — input: {response.usage.input_tokens}  "
       f"output: {response.usage.output_tokens}[/dim]")
rprint(f"[dim]Elapsed: {elapsed:.1f}s[/dim]")
