import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import List

import feedparser
@dataclass
class PaperInput:
    fingerprint: str
    title: str
    authors: str
    summary: str
    link: str
    published_at: datetime | None
    source: str


def _to_datetime(parsed_time) -> datetime | None:
    if not parsed_time:
        return None
    try:
        return datetime(*parsed_time[:6])
    except Exception:
        return None


def _fingerprint(entry_id: str, link: str, published: datetime | None) -> str:
    base = entry_id or link or ""
    stamp = published.isoformat() if published else ""
    raw = f"{base}::{stamp}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def fetch_feed(url: str, timeout: int = 30) -> List[PaperInput]:
    """
    Fetch and parse RSS feed with timeout control.
    
    Args:
        url: RSS feed URL
        timeout: Request timeout in seconds (default: 30)
    """
    try:
        feed = feedparser.parse(url, request_headers={'User-Agent': 'RSS Email Bot/1.0'})
        if feed.get('bozo', False) and feed.get('bozo_exception'):
            print(f"Warning: Feed parsing error for {url}: {feed.bozo_exception}")
    except Exception as e:
        print(f"Error fetching feed {url}: {e}")
        return []
    results: List[PaperInput] = []
    for entry in feed.entries:
        published = _to_datetime(getattr(entry, "published_parsed", None))
        entry_id = getattr(entry, "id", "") or getattr(entry, "guid", "")
        link = getattr(entry, "link", "")
        title = getattr(entry, "title", "(no title)")
        summary = getattr(entry, "summary", "")
        authors = ", ".join(a.get("name") for a in getattr(entry, "authors", []) if a.get("name"))

        fp = _fingerprint(entry_id, link, published)
        results.append(
            PaperInput(
                fingerprint=fp,
                title=title,
                authors=authors,
                summary=summary,
                link=link,
                published_at=published,
                source=url,
            )
        )
    return results
