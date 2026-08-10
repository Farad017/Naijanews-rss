#!/usr/bin/env python3

"""
Generate a custom RSS 2.0 feed from Nairaland's MAIN HOMEPAGE ONLY.

The feed contains only:
- Topic title
- Topic URL

IMPORTANT:
This script does NOT scrape /topics/, forum pages, or individual
Nairaland sub-pages. It fetches only:

    https://www.nairaland.com/

and extracts topic links displayed on that homepage.
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
HOME_URL = f"{BASE}/"
OUTPUT = Path("feed.xml")

# Maximum number of homepage topics to place in the RSS feed.
MAX_ITEMS = 100

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; NairalandRSSBot/1.0; "
        "+https://github.com/)"
    )
}


def is_homepage_topic_url(href: str) -> bool:
    """
    Return True only for Nairaland topic URLs of the form:

        /123456/topic-title

    This deliberately excludes:
        /topics/
        /topics/2
        /politics/
        /login
        /register
        etc.
    """

    try:
        parsed = urlparse(href)

        # Only accept links belonging to Nairaland.
        if parsed.netloc and parsed.netloc.lower() not in {
            "www.nairaland.com",
            "nairaland.com",
        }:
            return False

        path = parsed.path.strip("/")

        parts = path.split("/", 1)

        # A topic URL has exactly:
        # numeric topic ID + topic slug
        if len(parts) != 2:
            return False

        topic_id, slug = parts

        return topic_id.isdigit() and bool(slug)

    except Exception:
        return False


def get_homepage_topics() -> list[tuple[str, str]]:
    """
    Fetch ONLY the Nairaland homepage and extract topic links
    displayed on that page.
    """

    response = requests.get(
        HOME_URL,
        headers=HEADERS,
        timeout=30,
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    results = []
    seen_urls = set()

    for a in soup.find_all("a", href=True):

        href = a.get("href", "").strip()

        if not is_homepage_topic_url(href):
            continue

        title = " ".join(a.stripped_strings)

        title = re.sub(r"\s+", " ", title).strip()

        title = html.unescape(title)

        if not title:
            continue

        link = urljoin(BASE, href)

        # Remove query strings/fragments so the RSS URL is clean.
        parsed_link = urlparse(link)

        link = parsed_link._replace(
            query="",
            fragment="",
        ).geturl()

        if link in seen_urls:
            continue

        seen_urls.add(link)

        results.append((title, link))

    return results


def xml_escape(value: str) -> str:
    return html.escape(value, quote=True)


def build_feed(items: list[tuple[str, str]]) -> str:

    now = datetime.now(timezone.utc).strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )

    xml_items = []

    for title, link in items:

        xml_items.append(
            "    <item>\n"
            f"      <title>{xml_escape(title)}</title>\n"
            f"      <link>{xml_escape(link)}</link>\n"
            "    </item>"
        )

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0">\n'
        "  <channel>\n"
        "    <title>Nairaland Homepage - New Topics</title>\n"
        f"    <link>{HOME_URL}</link>\n"
        "    <description>"
        "Topics displayed on the Nairaland homepage."
        "</description>\n"
        f"    <lastBuildDate>{now}</lastBuildDate>\n"
        + "\n".join(xml_items)
        + "\n  </channel>\n"
        "</rss>\n"
    )


def main() -> None:

    items = get_homepage_topics()

    if not items:
        raise RuntimeError(
            "No topic links were found on the Nairaland homepage. "
            "Refusing to overwrite feed.xml."
        )

    # Keep only the topics displayed on the homepage,
    # up to our configured maximum.
    items = items[:MAX_ITEMS]

    OUTPUT.write_text(
        build_feed(items),
        encoding="utf-8",
    )

    print(
        f"Wrote {len(items)} homepage topics to {OUTPUT}"
    )


if __name__ == "__main__":
    main()
