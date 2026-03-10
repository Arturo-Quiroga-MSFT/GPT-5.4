#!/usr/bin/env python3
"""
04 — Vision / image understanding  (Responses API)

Sends an image URL (or local base64) to GPT-5.4 and asks it to
describe what it sees.  Demonstrates the multimodal input support.

Usage:
    python 04_vision.py                          # uses a sample image URL
    python 04_vision.py path/to/local/image.png  # uses a local file
"""

import base64
import sys
import time
from pathlib import Path

from config import DEPLOYMENT, get_client
from rich import print as rprint
from rich.panel import Panel

client = get_client()

SAMPLE_URL = "https://images.unsplash.com/photo-1546182990-dffeafbe841d?w=640"


def build_image_content(source: str | None = None) -> list[dict]:
    """Build the content array with an image (URL or local file)."""
    if source and Path(source).is_file():
        data = Path(source).read_bytes()
        b64 = base64.b64encode(data).decode()
        suffix = Path(source).suffix.lstrip(".").replace("jpg", "jpeg")
        image_item = {
            "type": "input_image",
            "image_url": f"data:image/{suffix};base64,{b64}",
            "detail": "high",
        }
    else:
        url = source or SAMPLE_URL
        image_item = {
            "type": "input_image",
            "image_url": url,
            "detail": "high",
        }

    return [
        image_item,
        {"type": "input_text", "text": "Describe this image in detail. What do you see?"},
    ]


source = sys.argv[1] if len(sys.argv) > 1 else None
content = build_image_content(source)

t0 = time.perf_counter()
response = client.responses.create(
    model=DEPLOYMENT,
    input=[{"role": "user", "content": content}],
)
elapsed = time.perf_counter() - t0

rprint(Panel(response.output_text, title="Vision Analysis"))
rprint(f"[dim]Tokens — input: {response.usage.input_tokens}  "
       f"output: {response.usage.output_tokens}[/dim]")
rprint(f"[dim]Elapsed: {elapsed:.1f}s[/dim]")
