from __future__ import annotations

import asyncio
import threading
from datetime import UTC, datetime

from src.internal.pipeline.llm.types import PolarizationResult

_SENTINEL = object()

_cache: dict[tuple, PolarizationResult] = {}
_pending: dict[tuple, asyncio.Event] = {}
_lock = threading.Lock()


def _make_key(
    query: str,
    time_filter: str,
    max_posts: int,
    max_comments_per_post: int,
    mode: str,
) -> tuple:
    normalized_query = query.strip().lower()
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    return (
        normalized_query, today, time_filter,
        max_posts, max_comments_per_post, mode,
    )


def get_cached_result(
    query: str,
    time_filter: str,
    max_posts: int,
    max_comments_per_post: int,
    mode: str,
) -> PolarizationResult | None:
    key = _make_key(
        query, time_filter, max_posts,
        max_comments_per_post, mode,
    )
    with _lock:
        return _cache.get(key)


async def wait_for_pending(
    query: str,
    time_filter: str,
    max_posts: int,
    max_comments_per_post: int,
    mode: str,
) -> PolarizationResult | None:
    """If another task is already running this query, wait for it."""
    key = _make_key(
        query, time_filter, max_posts,
        max_comments_per_post, mode,
    )
    with _lock:
        event = _pending.get(key)
    if event is None:
        return None
    await event.wait()
    with _lock:
        return _cache.get(key)


def mark_pending(
    query: str,
    time_filter: str,
    max_posts: int,
    max_comments_per_post: int,
    mode: str,
) -> bool:
    """Mark a query as in-progress. Returns False if already pending."""
    key = _make_key(
        query, time_filter, max_posts,
        max_comments_per_post, mode,
    )
    with _lock:
        if key in _cache or key in _pending:
            return False
        _pending[key] = asyncio.Event()
        return True


def store_result(
    query: str,
    time_filter: str,
    max_posts: int,
    max_comments_per_post: int,
    mode: str,
    result: PolarizationResult,
) -> None:
    key = _make_key(
        query, time_filter, max_posts,
        max_comments_per_post, mode,
    )
    with _lock:
        _cache[key] = result
        event = _pending.pop(key, None)
    if event is not None:
        event.set()


def clear_pending(
    query: str,
    time_filter: str,
    max_posts: int,
    max_comments_per_post: int,
    mode: str,
) -> None:
    """Remove pending marker without storing (e.g. on error)."""
    key = _make_key(
        query, time_filter, max_posts,
        max_comments_per_post, mode,
    )
    with _lock:
        event = _pending.pop(key, None)
    if event is not None:
        event.set()
