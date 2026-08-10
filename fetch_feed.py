#!/usr/bin/env python3

"""
Generate a custom RSS 2.0 feed from Nairaland's MAIN HOMEPAGE ONLY.

The feed contains only:
- Topic title
- Topic URL

IMPORTANT:
This script does NOT scrape /topics/, forum pages, or individual
Nairaland sub-pages.

It fetches ONLY:

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


# ------------------------------------------------------------
# SETTINGS
# ------------------------------------------------------------

BASE = "https://www.nairaland.com"
HOME_URL = f"{BASE}/"

# The generated RSS file
OUTPUT = Path("feed.xml")

# Maximum number of topics to put in the RSS feed
MAX_ITEMS = 100

# Identify our request to Nairaland
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; NairalandRSSBot/1.0; "
        "+https://github.com/)"
    )
}


# ------------------------------------------------------------
# CHECK WHETHER A LINK IS A NAIRALAND TOPIC
# ------------------------------------------------------------

def is_homepage_topic_url(href: str) -> bool:
    """
    Accept only normal Nairaland topic URLs such as:

        /8726006/utme-top-scorer-credits-prep50

    Reject things such as:

        /topics/
        /topics/2
        /politics/
        /login
        /register

    Only links belonging to Nairaland are accepted.
    """

    try:
        parsed = urlparse(href)

        # If a domain is explicitly present, it must be Nairaland.
        if parsed.netloc and parsed.netloc.lower() not in {
            "www.nairaland.com",
            "nairaland.com",
        }:
            return False

        path = parsed.path.strip("/")

        parts = path.split("/", 1)

        # A topic URL must contain:
        # 1. Numeric topic ID
        # 2. Topic slug
        if len(parts) != 2:
            return False

        topic_id, slug = parts

        return topic_id.isdigit() and bool(slug)

    except Exception:
        return False


# ------------------------------------------------------------
# FETCH ONLY THE NAIRALAND HOMEPAGE
# ------------------------------------------------------------

def get_homepage_topics() -> list[tuple[str, str]]:
    """
    Fetch ONLY:

        https://www.nairaland.com/

    and extract topic links that are displayed on that page.
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

    # Look at every link on the homepage.
    for a in soup.find_all("a", href=True):

        href = a.get("href", "").strip()

        # Ignore anything that isn't a topic link.
        if not is_homepage_topic_url(href):
            continue

        # Get the visible text of the link.
        title = " ".join(a.stripped_strings)

        title = re.sub(r"\s+", " ", title).strip()

        title = html.unescape(title)

        # Ignore links without a title.
        if not title:
            continue

        # Convert relative URLs to complete URLs.
        link = urljoin(BASE, href)

        # Remove query strings and fragments.
        parsed_link = urlparse(link)

        link = parsed_link._replace(
            query="",
            fragment="",
        ).geturl()

        # Prevent duplicate topics.
        if link in seen_urls:
            continue

        seen_urls.add(link)

        results.append((title, link))

    return results


# ------------------------------------------------------------
# RSS XML
# ------------------------------------------------------------

def xml_escape(value: str) -> str:
    """Safely escape text for XML."""
    return html.escape(value, quote=True)


def build_feed(items: list[tuple[str, str]]) -> str:

    now = datetime.now(timezone.utc).strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )

    xml_items = []

    for title, link in items:

        # Each RSS item contains ONLY:
        # - title
        # - link
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
        "    <title>Nairaland Homepage - Topics</title>\n"
        f"    <link>{HOME_URL}</link>\n"
        "    <description>"
        "Topics displayed on the Nairaland homepage."
        "</description>\n"
        f"    <lastBuildDate>{now}</lastBuildDate>\n"
        + "\n".join(xml_items)
        + "\n  </channel>\n"
        "</rss>\n"
    )


# ------------------------------------------------------------
# MAIN PROGRAM
# ------------------------------------------------------------

def main() -> None:

    # Fetch topics ONLY from the Nairaland homepage.
    items = get_homepage_topics()

    # If nothing was found, do NOT overwrite the existing feed.
    if not items:
        raise RuntimeError(
            "No topic links were found on the Nairaland homepage. "
            "Refusing to overwrite feed.xml."
        )

    # Keep only the first 100 topics found on the homepage.
    items = items[:MAX_ITEMS]

    # Generate the RSS file.
    OUTPUT.write_text(
        build_feed(items),
        encoding="utf-8",
    )

    print(
        f"Wrote {len(items)} homepage topics to {OUTPUT}"
    )


if __name__ == "__main__":
    main()
