#!/usr/bin/env python3
"""
Generate a custom RSS 2.0 feed containing newly created Nairaland topics.

The feed contains only:
- Topic title
- Topic URL

It reads Nairaland's "New Topics" pages and writes feed.xml.
"""

from __future__ import annotations

import html
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BASE = "https://www.nairaland.com"
TOPICS_URL = f"{BASE}/topics/"
OUTPUT = Path("feed.xml")

# Read several newest pages so a busy hour is less likely to miss topics.
PAGES_TO_FETCH = 3
MAX_ITEMS = 150

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; NairalandRSSBot/1.0; "
        "+https://github.com/)"
    )
}


def is_topic_url(href: str) -> bool:
    """Return True for Nairaland topic URLs such as /123456/topic-name."""
    try:
        path = urlparse(href).path.strip("/")
        parts = path.split("/", 1)
        if len(parts) != 2:
            return False
        return parts[0].isdigit() and bool(parts[1])
    except Exception:
        return False


def get_topics(page_number: int) -> list[tuple[str, str]]:
    url = TOPICS_URL if page_number == 1 else f"{TOPICS_URL}{page_number}"
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a.get("href", "").strip()
        if not is_topic_url(href):
            continue

        title = " ".join(a.stripped_strings)
        title = re.sub(r"\s+", " ", title).strip()
        title = html.unescape(title)

        if not title:
            continue

        link = urljoin(BASE, href)
        if link in seen:
            continue

        seen.add(link)
        results.append((title, link))

    return results


def xml_escape(value: str) -> str:
    return html.escape(value, quote=True)


def build_feed(items: list[tuple[str, str]]) -> str:
    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

    xml_items = []
    for title, link in items:
        xml_items.append(
            "    <item>\n"
            f"      <title>{xml_escape(title)}</title>\n"
            f"      <link>{xml_escape(link)}</link>\n"
            f"      <guid isPermaLink=\"true\">{xml_escape(link)}</guid>\n"
            "    </item>"
        )

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0">\n'
        "  <channel>\n"
        "    <title>Nairaland - All New Topics</title>\n"
        f"    <link>{BASE}/topics/</link>\n"
        "    <description>New topics from across Nairaland.</description>\n"
        f"    <lastBuildDate>{now}</lastBuildDate>\n"
        + "\n".join(xml_items)
        + "\n  </channel>\n"
        "</rss>\n"
    )


def main() -> None:
    all_items = []
    seen_urls = set()

    for page in range(1, PAGES_TO_FETCH + 1):
        try:
            items = get_topics(page)
        except Exception as exc:
            print(f"Warning: could not fetch page {page}: {exc}")
            continue

        for title, link in items:
            if link not in seen_urls:
                seen_urls.add(link)
                all_items.append((title, link))

    if not all_items:
        raise RuntimeError("No Nairaland topics were found; refusing to overwrite feed.xml.")

    # Nairaland's New Topics page is already newest-first.
    all_items = all_items[:MAX_ITEMS]

    OUTPUT.write_text(build_feed(all_items), encoding="utf-8")
    print(f"Wrote {len(all_items)} topics to {OUTPUT}")


if __name__ == "__main__":
    main()
