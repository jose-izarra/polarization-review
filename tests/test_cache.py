from __future__ import annotations

import asyncio
from unittest.mock import patch

from src.api.cache import (
    _cache,
    _make_key,
    _pending,
    clear_pending,
    get_cached_result,
    mark_pending,
    store_result,
    wait_for_pending,
)
from src.internal.pipeline.domain import PolarizationResult


def _make_result(query: str = "test") -> PolarizationResult:
    return PolarizationResult(
        query=query,
        collected_at="2026-03-17T00:00:00Z",
        sample_size=10,
        polarization_score=42.0,
        rationale="test rationale",
        evidence=[],
        status="ok",
        error_message=None,
    )


_ARGS = ("test", "week", 30, 10, "live")


class TestMakeKey:
    def test_normalizes_case(self):
        k1 = _make_key("Gun Control", "week", 30, 10, "live")
        k2 = _make_key("gun control", "week", 30, 10, "live")
        assert k1 == k2

    def test_normalizes_whitespace(self):
        k1 = _make_key("  gun control  ", "week", 30, 10, "live")
        k2 = _make_key("gun control", "week", 30, 10, "live")
        assert k1 == k2

    def test_different_params_different_keys(self):
        k1 = _make_key("test", "week", 30, 10, "live")
        k2 = _make_key("test", "month", 30, 10, "live")
        assert k1 != k2

        k3 = _make_key("test", "week", 50, 10, "live")
        assert k1 != k3

        k4 = _make_key("test", "week", 30, 20, "live")
        assert k1 != k4

    def test_different_mode_different_keys(self):
        k1 = _make_key("test", "week", 30, 10, "live")
        k2 = _make_key("test", "week", 30, 10, "fake_polarized")
        assert k1 != k2

    @patch("src.api.cache.datetime")
    def test_different_dates_different_keys(self, mock_dt):
        from datetime import UTC, datetime

        mock_dt.now.return_value = datetime(2026, 3, 17, tzinfo=UTC)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        k1 = _make_key("test", "week", 30, 10, "live")

        mock_dt.now.return_value = datetime(2026, 3, 18, tzinfo=UTC)
        k2 = _make_key("test", "week", 30, 10, "live")

        assert k1 != k2


class TestCacheOperations:
    def setup_method(self):
        _cache.clear()
        _pending.clear()

    def test_miss_returns_none(self):
        assert get_cached_result(*_ARGS) is None

    def test_store_and_retrieve(self):
        result = _make_result()
        store_result("gun control", "week", 30, 10, "live", result)
        cached = get_cached_result(
            "gun control",
            "week",
            30,
            10,
            "live",
        )
        assert cached is result

    def test_hit_with_normalized_query(self):
        result = _make_result()
        store_result("Gun Control", "week", 30, 10, "live", result)
        cached = get_cached_result(
            "  gun control  ",
            "week",
            30,
            10,
            "live",
        )
        assert cached is result

    def test_different_params_no_hit(self):
        result = _make_result()
        store_result("test", "week", 30, 10, "live", result)
        assert get_cached_result("test", "month", 30, 10, "live") is None


class TestPendingMechanism:
    def setup_method(self):
        _cache.clear()
        _pending.clear()

    def test_mark_pending_returns_true_first_time(self):
        assert mark_pending(*_ARGS) is True

    def test_mark_pending_returns_false_if_already_pending(self):
        mark_pending(*_ARGS)
        assert mark_pending(*_ARGS) is False

    def test_mark_pending_returns_false_if_cached(self):
        store_result(*_ARGS, result=_make_result())
        assert mark_pending(*_ARGS) is False

    def test_store_result_clears_pending_and_signals(self):
        mark_pending(*_ARGS)
        key = _make_key(*_ARGS)
        assert key in _pending
        store_result(*_ARGS, result=_make_result())
        assert key not in _pending

    def test_clear_pending_removes_marker(self):
        mark_pending(*_ARGS)
        key = _make_key(*_ARGS)
        clear_pending(*_ARGS)
        assert key not in _pending

    def test_wait_for_pending_returns_none_if_not_pending(self):
        result = asyncio.get_event_loop().run_until_complete(
            wait_for_pending(*_ARGS),
        )
        assert result is None

    def test_wait_for_pending_gets_result_after_store(self):
        mark_pending(*_ARGS)
        expected = _make_result()

        async def run():
            async def waiter():
                return await wait_for_pending(*_ARGS)

            async def storer():
                await asyncio.sleep(0.01)
                store_result(*_ARGS, result=expected)

            waiter_task = asyncio.create_task(waiter())
            asyncio.create_task(storer())
            return await waiter_task

        result = asyncio.get_event_loop().run_until_complete(run())
        assert result is expected
