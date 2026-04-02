#!/usr/bin/env python3
"""
01_scrape_fomc.py — Download FOMC meeting minutes from the Federal Reserve

Scrapes the FOMC calendar page for links to meeting minutes, downloads
each one, extracts the plain-text body, and saves to data/<date>.txt.

Usage:
    python 01_scrape_fomc.py                  # scrape all available minutes
    python 01_scrape_fomc.py --year 2024      # scrape only 2024
    python 01_scrape_fomc.py --year 2023 2024 # scrape 2023 and 2024
"""

import argparse
import os
import re
import time

import requests
from bs4 import BeautifulSoup
from rich.console import Console
from rich.progress import track

from config import DATA_DIR, FOMC_BASE_URL, FOMC_CALENDAR_URL

console = Console()
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "FOMC-Research-Bot/1.0 (academic)"})

# ── Discover minutes URLs ─────────────────────────────────────────────

def _archive_calendar_urls() -> list[str]:
    """Return URLs for the main calendar page plus historical year pages."""
    resp = SESSION.get(FOMC_CALENDAR_URL, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    urls = [FOMC_CALENDAR_URL]
    # Historical pages linked as fomchistorical20XX.htm
    for a in soup.find_all("a", href=re.compile(r"fomchistorical\d{4}\.htm")):
        href = a["href"]
        if not href.startswith("http"):
            href = FOMC_BASE_URL + href
        urls.append(href)
    return urls


def discover_minutes_links(years: list[int] | None = None) -> list[dict]:
    """
    Return a list of {"date": "YYYYMMDD", "url": "..."} for every
    FOMC minutes page found on the Fed website.

    The calendar page contains direct links like:
      /monetarypolicy/fomcminutes20241218.htm
    """
    calendar_urls = _archive_calendar_urls()
    minutes = []
    seen = set()

    for cal_url in track(calendar_urls, description="Scanning calendars…"):
        try:
            resp = SESSION.get(cal_url, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as exc:
            console.print(f"[yellow]⚠ Skipping {cal_url}: {exc}[/yellow]")
            continue

        soup = BeautifulSoup(resp.text, "html.parser")

        # Minutes links match: /monetarypolicy/fomcminutes<YYYYMMDD>.htm
        for a in soup.find_all("a", href=re.compile(r"fomcminutes\d{8}\.htm$")):
            href: str = a["href"]

            # Skip PDF links
            if href.endswith(".pdf"):
                continue

            date_match = re.search(r"(\d{8})", href)
            if not date_match:
                continue

            date_str = date_match.group(1)

            if years and int(date_str[:4]) not in years:
                continue

            if date_str in seen:
                continue
            seen.add(date_str)

            full_url = href if href.startswith("http") else FOMC_BASE_URL + href
            minutes.append({"date": date_str, "url": full_url})

        time.sleep(0.3)  # polite crawling

    minutes.sort(key=lambda m: m["date"])
    return minutes


# ── Download & extract text ───────────────────────────────────────────

def extract_minutes_text(url: str) -> str:
    """Download an FOMC minutes page and return cleaned plain text."""
    resp = SESSION.get(url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # The main content is in <div id="article">
    article = soup.find("div", id="article")
    if article is None:
        # Fallback selectors for older pages
        article = (
            soup.find("div", id="content")
            or soup.find("div", class_="col-xs-12")
            or soup.body
        )
    if article is None:
        raise ValueError(f"Could not find content div in {url}")

    # Remove script/style tags
    for tag in article.find_all(["script", "style", "nav", "header", "footer"]):
        tag.decompose()

    text = article.get_text(separator="\n", strip=True)

    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


# ── Main ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Scrape FOMC meeting minutes")
    parser.add_argument(
        "--year", type=int, nargs="*",
        help="Limit to specific year(s), e.g. --year 2023 2024",
    )
    args = parser.parse_args()

    os.makedirs(DATA_DIR, exist_ok=True)

    console.print("[bold]Discovering FOMC minutes links…[/bold]")
    minutes = discover_minutes_links(args.year)
    console.print(f"Found [bold green]{len(minutes)}[/bold green] minutes documents")

    downloaded = 0
    skipped = 0

    for doc in track(minutes, description="Downloading minutes…"):
        out_path = os.path.join(DATA_DIR, f"{doc['date']}.txt")
        if os.path.exists(out_path):
            skipped += 1
            continue

        try:
            text = extract_minutes_text(doc["url"])
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(text)
            downloaded += 1
            time.sleep(0.5)  # polite delay
        except Exception as exc:
            console.print(f"[red]✗ {doc['date']}: {exc}[/red]")

    console.print(
        f"\n[bold green]Done![/bold green] "
        f"Downloaded: {downloaded}, Skipped (cached): {skipped}, "
        f"Total available: {len(minutes)}"
    )
    console.print(f"Data saved to [bold]{DATA_DIR}/[/bold]")


if __name__ == "__main__":
    main()
