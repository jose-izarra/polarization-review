"""
GNews Data Collection Module for Polarization Analysis

Collects news articles from GNews for a given search term,
returning them in the unified raw item format consumed by normalize_raw_item().

Environment Variables Required:
    GNEWS_API_KEY: GNews API key
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from urllib import error, request
from urllib.parse import urlencode, urlparse

from src.internal.config.config import config as app_config

logger = logging.getLogger(__name__)

MAX_ARTICLES = 3

_DEFAULT_LANG = "en"
_DEFAULT_SORTBY = "relevance"

_TIME_DELTA_DAYS = {"day": 1, "week": 7, "month": 30}

SOURCE_LEAN_LOOKUP: dict[str, str] = {
    "cnn.com": "left",
    "msnbc.com": "left",
    "nytimes.com": "left",
    "washingtonpost.com": "left",
    "theguardian.com": "left",
    "huffpost.com": "left",
    "vox.com": "left",
    "npr.org": "left",
    "foxnews.com": "right",
    "breitbart.com": "right",
    "dailywire.com": "right",
    "nypost.com": "right",
    "washingtontimes.com": "right",
    "newsmax.com": "right",
    "theblaze.com": "right",
    "oann.com": "right",
    "reuters.com": "center",
    "apnews.com": "center",
    "bbc.com": "center",
    "bbc.co.uk": "center",
    "usatoday.com": "center",
    "thehill.com": "center",
}


def _get_source_lean(url: str) -> str:
    """Extract domain from URL and look up its lean."""
    try:
        domain = urlparse(url).netloc.lower()
        # Strip www. prefix
        if domain.startswith("www."):
            domain = domain[4:]
        return SOURCE_LEAN_LOOKUP.get(domain, "unknown")
    except Exception:
        return "unknown"


def collect_gnews_data(
    query: str,
    time_filter: str = "month",
) -> dict:
    """Collect GNews articles for the given query.

    Returns:
        {"data": {"posts": [...], "comments": []}}
    """
    if not app_config.gnews_api_key:
        raise RuntimeError("GNEWS_API_KEY is required for GNews scraping")
    api_key = app_config.gnews_api_key

    days = _TIME_DELTA_DAYS.get(time_filter, 7)
    from_date = (datetime.now(tz=timezone.utc) - timedelta(days=days)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    params = urlencode(
        {
            "q": query,
            "lang": _DEFAULT_LANG,
            "max": MAX_ARTICLES,
            "sortby": _DEFAULT_SORTBY,
            "from": from_date,
            "apikey": api_key,
        }
    )
    url = f"https://gnews.io/api/v4/search?{params}"

    req = request.Request(url, method="GET")

    try:
        with request.urlopen(req, timeout=30) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GNews API error: {exc.code} {details}") from exc

    articles = raw.get("articles", [])
    posts = []
    for article in articles:
        title = article.get("title", "")
        description = article.get("description", "") or ""
        text = f"{title}. {description}"
        article_url = article.get("url", "")

        posts.append(
            {
                "platform_id": f"gnews_{article_url or title}",
                "source": "gnews",
                "text": text,
                "url": article_url,
                "timestamp": article.get("publishedAt", ""),
                "engagement": {"score": 0},
                "metadata": {"content_type": "post"},
                "source_lean": _get_source_lean(article_url),
            }
        )

    return {"data": {"posts": posts, "comments": []}}
