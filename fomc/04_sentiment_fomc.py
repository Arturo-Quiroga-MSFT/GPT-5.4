#!/usr/bin/env python3
"""
04_sentiment_fomc.py — Structured sentiment analysis across FOMC meetings

Reads raw FOMC minutes from data/, sends each to GPT-5.4 with a strict
JSON schema to extract: hawkish/dovish score, key topics, rate outlook,
and dissent signals.  Outputs a timeline summary.

Usage:
    python 04_sentiment_fomc.py                    # analyze all meetings
    python 04_sentiment_fomc.py --year 2024        # only 2024 meetings
    python 04_sentiment_fomc.py --last 5           # last 5 meetings
"""

import argparse
import json
import os
import time

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config import DATA_DIR, DEPLOYMENT, get_client

console = Console()

SENTIMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "meeting_date": {"type": "string", "description": "YYYY-MM-DD"},
        "overall_tone": {
            "type": "string",
            "enum": ["strongly_hawkish", "hawkish", "neutral", "dovish", "strongly_dovish"],
        },
        "hawkish_score": {
            "type": "number",
            "description": "Score from -1.0 (very dovish) to 1.0 (very hawkish)",
        },
        "key_topics": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Top 3-5 policy topics discussed",
        },
        "rate_outlook": {
            "type": "string",
            "description": "Brief description of the implied rate path",
        },
        "inflation_concern": {
            "type": "string",
            "enum": ["high", "moderate", "low"],
        },
        "labor_market_view": {
            "type": "string",
            "enum": ["strong", "moderating", "weakening"],
        },
        "dissent_present": {"type": "boolean"},
        "notable_quote": {
            "type": "string",
            "description": "One key sentence that captures the meeting's tone",
        },
        "summary": {
            "type": "string",
            "description": "2-3 sentence executive summary of the meeting",
        },
    },
    "required": [
        "meeting_date", "overall_tone", "hawkish_score", "key_topics",
        "rate_outlook", "inflation_concern", "labor_market_view",
        "dissent_present", "notable_quote", "summary",
    ],
    "additionalProperties": False,
}

ANALYSIS_PROMPT = """\
You are a Federal Reserve policy analyst. Analyze the following FOMC meeting \
minutes and extract structured data about the committee's monetary policy stance.

Be precise with the hawkish_score: use the full -1.0 to 1.0 range.
For the notable_quote, pick a verbatim sentence from the minutes.
"""


def analyze_meeting(client, date_str: str, text: str) -> dict | None:
    """Send a single meeting's text to GPT-5.4 for structured analysis."""
    # Truncate very long documents to fit comfortably
    max_chars = 200_000  # ~50K tokens, well within limits
    if len(text) > max_chars:
        text = text[:max_chars]

    formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    user_msg = f"FOMC Meeting Minutes — {formatted_date}\n\n{text}"

    try:
        response = client.responses.create(
            model=DEPLOYMENT,
            instructions=ANALYSIS_PROMPT,
            input=user_msg,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "fomc_sentiment",
                    "schema": SENTIMENT_SCHEMA,
                    "strict": True,
                }
            },
        )
        return json.loads(response.output_text)
    except Exception as exc:
        console.print(f"[red]✗ Error analyzing {date_str}: {exc}[/red]")
        return None


def display_timeline(results: list[dict]):
    """Print a rich table summarizing sentiment across meetings."""
    table = Table(title="FOMC Sentiment Timeline", show_lines=True)
    table.add_column("Date", style="cyan", width=12)
    table.add_column("Tone", width=18)
    table.add_column("Score", justify="right", width=6)
    table.add_column("Inflation", width=10)
    table.add_column("Labor", width=12)
    table.add_column("Rate Outlook", max_width=35)
    table.add_column("Dissent", width=7)

    tone_colors = {
        "strongly_hawkish": "bold red",
        "hawkish": "red",
        "neutral": "yellow",
        "dovish": "green",
        "strongly_dovish": "bold green",
    }

    for r in results:
        tone_style = tone_colors.get(r["overall_tone"], "white")
        score_str = f"{r['hawkish_score']:+.2f}"
        dissent = "Yes" if r["dissent_present"] else "No"

        table.add_row(
            r["meeting_date"],
            f"[{tone_style}]{r['overall_tone']}[/{tone_style}]",
            score_str,
            r["inflation_concern"],
            r["labor_market_view"],
            r["rate_outlook"][:35],
            dissent,
        )

    console.print(table)


def main():
    parser = argparse.ArgumentParser(description="Structured FOMC sentiment analysis")
    parser.add_argument("--year", type=int, nargs="*", help="Filter by year(s)")
    parser.add_argument("--last", type=int, help="Analyze only the last N meetings")
    args = parser.parse_args()

    if not os.path.isdir(DATA_DIR):
        console.print("[red]No data/ directory. Run 01_scrape_fomc.py first.[/red]")
        return

    txt_files = sorted(f for f in os.listdir(DATA_DIR) if f.endswith(".txt"))

    if args.year:
        txt_files = [f for f in txt_files if int(f[:4]) in args.year]
    if args.last:
        txt_files = txt_files[-args.last:]

    if not txt_files:
        console.print("[red]No matching files found.[/red]")
        return

    console.print(f"Analyzing [bold green]{len(txt_files)}[/bold green] meetings…\n")

    client = get_client()
    results = []

    for filename in txt_files:
        date_str = filename.replace(".txt", "")
        console.print(f"  Analyzing {date_str}…", end=" ")

        filepath = os.path.join(DATA_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        t0 = time.perf_counter()
        result = analyze_meeting(client, date_str, text)
        elapsed = time.perf_counter() - t0

        if result:
            results.append(result)
            tone = result["overall_tone"]
            console.print(f"[green]✓[/green] {tone} ({elapsed:.1f}s)")
        else:
            console.print("[red]✗[/red]")

        time.sleep(0.2)

    if results:
        console.print()
        display_timeline(results)

        # Save results
        out_path = os.path.join(DATA_DIR, "sentiment_results.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        console.print(f"\n[dim]Results saved to {out_path}[/dim]")


if __name__ == "__main__":
    main()
