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
from urllib.parse import urlencode

from src.internal.config.config import config as app_config

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "max_articles": 20,
    "lang": "en",
    "sortby": "relevance",
}

_TIME_DELTA_DAYS = {"day": 1, "week": 7, "month": 30}


def collect_gnews_data(
    query: str,
    time_filter: str = "week",
    config: dict | None = None,
) -> dict:
    """Collect GNews articles for the given query.

    Returns:
        {"data": {"posts": [...], "comments": []}}
    """
    if not app_config.gnews_api_key:
        raise RuntimeError("GNEWS_API_KEY is required for GNews scraping")
    api_key = app_config.gnews_api_key

    cfg = {**DEFAULT_CONFIG, **(config or {})}

    days = _TIME_DELTA_DAYS.get(time_filter, 7)
    from_date = (datetime.now(tz=timezone.utc) - timedelta(days=days)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    params = urlencode(
        {
            "q": query,
            "lang": cfg["lang"],
            "max": cfg["max_articles"],
            "sortby": cfg["sortby"],
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

        posts.append(
            {
                "platform_id": f"gnews_{article.get('url', title)}",
                "source": "gnews",
                "text": text,
                "url": article.get("url", ""),
                "timestamp": article.get("publishedAt", ""),
                "engagement": {"score": 0},
                "metadata": {"content_type": "post"},
            }
        )

    return {"data": {"posts": posts, "comments": []}}
