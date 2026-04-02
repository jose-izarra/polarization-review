from __future__ import annotations

import re

from src.internal.pipeline.domain import NormalizedItem

_WHITESPACE_RE = re.compile(r"\s+")


def clean_text(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text or "").strip()


def normalize_raw_item(raw: dict) -> NormalizedItem:
    metadata = raw.get("metadata", {})
    engagement = raw.get("engagement", {})
    content_type = metadata.get("content_type", "comment")
    if content_type not in {"post", "comment"}:
        content_type = "comment"

    platform = raw.get("source", "unknown")
    source_lean = raw.get("source_lean")
    parent_video_id = metadata.get("parent_video_id")

    return NormalizedItem(
        id=str(raw.get("platform_id") or raw.get("id") or ""),
        text=clean_text(raw.get("text", "")),
        url=str(raw.get("url") or ""),
        timestamp=str(raw.get("timestamp") or ""),
        engagement_score=int(engagement.get("score", 0) or 0),
        content_type=content_type,
        platform=platform,
        source_lean=source_lean,
        parent_video_id=parent_video_id,
    )
