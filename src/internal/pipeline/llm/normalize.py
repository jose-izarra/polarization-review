from __future__ import annotations

import re

from src.internal.pipeline.domain import NormalizedItem

_WHITESPACE_RE = re.compile(r"\s+")
_MIN_TEXT_LENGTH = 10

def clean_text(text: str) -> str:
    """Collapse whitespace and trim content."""
    return _WHITESPACE_RE.sub(" ", text or "").strip()


def filter_item(item: dict) -> bool:
    """Minimal quality filters for v0."""
    text = clean_text(item.get("text", ""))
    if len(text) < _MIN_TEXT_LENGTH:
        return False
    if text in {"[deleted]", "[removed]"}:
        return False
    if not item.get("id"):
        return False
    return True


def dedupe_items(items: list[NormalizedItem]) -> list[NormalizedItem]:
    """Deduplicate by id and by exact text content (catches syndicated articles)."""
    seen_ids: set[str] = set()
    seen_texts: set[str] = set()
    deduped: list[NormalizedItem] = []
    for item in items:
        if item.id in seen_ids:
            continue
        normalized_text = item.text.lower()
        if normalized_text in seen_texts:
            continue
        seen_ids.add(item.id)
        seen_texts.add(normalized_text)
        deduped.append(item)
    return deduped


def select_top_items(
    items: list[NormalizedItem], max_items: int = 40
) -> list[NormalizedItem]:
    """Rank by engagement descending and keep top N."""
    ranked = sorted(items, key=lambda x: x.engagement_score, reverse=True)
    return ranked[:max_items]
