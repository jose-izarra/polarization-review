from __future__ import annotations

import re

from .types import NormalizedItem

_WHITESPACE_RE = re.compile(r"\s+")


def clean_text(text: str) -> str:
    """Collapse whitespace and trim content."""
    return _WHITESPACE_RE.sub(" ", text or "").strip()


def filter_item(item: dict, min_text_length: int = 20) -> bool:
    """Minimal quality filters for v0."""
    text = clean_text(item.get("text", ""))
    if len(text) < min_text_length:
        return False
    if text in {"[deleted]", "[removed]"}:
        return False
    if not item.get("id"):
        return False
    return True


def dedupe_items(items: list[NormalizedItem]) -> list[NormalizedItem]:
    """Deduplicate by content id."""
    seen: set[str] = set()
    deduped: list[NormalizedItem] = []
    for item in items:
        if item.id in seen:
            continue
        seen.add(item.id)
        deduped.append(item)
    return deduped


def select_top_items(
    items: list[NormalizedItem], max_items: int = 40
) -> list[NormalizedItem]:
    """Rank by engagement descending and keep top N."""
    ranked = sorted(items, key=lambda x: x.engagement_score, reverse=True)
    return ranked[:max_items]


def normalize_raw_item(raw: dict) -> NormalizedItem:
    metadata = raw.get("metadata", {})
    engagement = raw.get("engagement", {})
    content_type = metadata.get("content_type", "comment")
    if content_type not in {"post", "comment"}:
        content_type = "comment"

    return NormalizedItem(
        id=str(raw.get("platform_id") or raw.get("id") or ""),
        text=clean_text(raw.get("text", "")),
        url=str(raw.get("url") or ""),
        timestamp=str(raw.get("timestamp") or ""),
        engagement_score=int(engagement.get("score", 0) or 0),
        content_type=content_type,
    )
