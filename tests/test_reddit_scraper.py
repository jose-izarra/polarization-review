"""
Tests for the Reddit scraper's dynamic subreddit discovery logic.

All tests mock PRAW objects — no live API calls are made.
"""

import unittest
from unittest.mock import MagicMock, patch

import prawcore
from src.internal.pipeline.scrape.reddit.fetch import (
    collect_reddit_data,
    discover_subreddits,
)
from src.internal.pipeline.scrape.reddit.utils import (
    QUICK_CONFIG,
    _extract_top_subreddits,
)


def _make_sub(name: str, subscribers: int) -> MagicMock:
    """Build a fake PRAW Subreddit object."""
    sub = MagicMock()
    sub.display_name = name
    sub.subscribers = subscribers
    return sub


def _make_post(subreddit: str, platform_id: str, score: int = 10) -> dict:
    """Build a minimal post dict matching the reddit.py output schema."""
    return {
        "id": f"reddit_post_{platform_id}",
        "source": "reddit",
        "platform_id": platform_id,
        "search_term": "test",
        "text": "some text long enough to pass quality filter",
        "author": "user",
        "timestamp": "2024-01-01T00:00:00+00:00",
        "url": f"https://reddit.com/r/{subreddit}/comments/{platform_id}",
        "engagement": {"likes": score, "replies": 0, "shares": 0, "score": score},
        "metadata": {
            "subreddit": subreddit,
            "content_type": "post",
            "parent_id": None,
            "is_self_post": True,
            "link_url": None,
            "flair": None,
        },
    }


class TestDiscoverSubreddits(unittest.TestCase):
    def test_empty_search_returns_all(self):
        reddit = MagicMock()
        reddit.subreddits.search.return_value = iter([])
        result = discover_subreddits(reddit, "test query")
        self.assertEqual(result, ["all"])

    def test_filters_by_min_subscribers(self):
        reddit = MagicMock()
        reddit.subreddits.search.return_value = iter(
            [
                _make_sub("SmallSub", 500),
                _make_sub("BigSub", 50_000),
            ]
        )
        result = discover_subreddits(reddit, "test", min_subscribers=10_000)
        self.assertIn("BigSub", result)
        self.assertNotIn("SmallSub", result)

    def test_always_starts_with_all(self):
        reddit = MagicMock()
        reddit.subreddits.search.return_value = iter([_make_sub("BigSub", 50_000)])
        result = discover_subreddits(reddit, "test")
        self.assertEqual(result[0], "all")

    def test_does_not_duplicate_all(self):
        reddit = MagicMock()
        # subreddits.search returns a sub literally named "all"
        reddit.subreddits.search.return_value = iter([_make_sub("all", 999_999)])
        result = discover_subreddits(reddit, "test")
        self.assertEqual(result.count("all"), 1)

    def test_api_failure_degrades_to_all(self):
        reddit = MagicMock()
        reddit.subreddits.search.side_effect = prawcore.exceptions.RequestException(
            MagicMock(), MagicMock(), MagicMock()
        )
        result = discover_subreddits(reddit, "test")
        self.assertEqual(result, ["all"])

    def test_limit_zero_skips_api(self):
        reddit = MagicMock()
        result = discover_subreddits(reddit, "test", limit=0)
        self.assertEqual(result, ["all"])
        reddit.subreddits.search.assert_not_called()

    def test_sub_attribute_error_is_skipped(self):
        """If accessing sub.subscribers raises, that sub is skipped gracefully."""
        bad_sub = MagicMock()
        bad_sub.display_name = "BadSub"
        bad_sub.subscribers  # access registers the attribute
        type(bad_sub).subscribers = property(
            lambda self: (_ for _ in ()).throw(Exception("403"))
        )

        good_sub = _make_sub("GoodSub", 50_000)

        reddit = MagicMock()
        reddit.subreddits.search.return_value = iter([bad_sub, good_sub])
        result = discover_subreddits(reddit, "test", min_subscribers=1_000)
        self.assertIn("GoodSub", result)

    def test_no_duplicate_subreddits(self):
        reddit = MagicMock()
        reddit.subreddits.search.return_value = iter(
            [
                _make_sub("politics", 50_000),
                _make_sub("politics", 50_000),  # duplicate
            ]
        )
        result = discover_subreddits(reddit, "test")
        self.assertEqual(result.count("politics"), 1)


class TestExtractTopSubreddits(unittest.TestCase):
    def _make_posts(self, distribution: dict[str, int]) -> list[dict]:
        """Build a post list from {subreddit: count} distribution."""
        posts = []
        counter = 0
        for sub, count in distribution.items():
            for _ in range(count):
                posts.append(_make_post(sub, f"id{counter}"))
                counter += 1
        return posts

    def test_returns_correct_ranking(self):
        posts = self._make_posts({"worldnews": 3, "politics": 5, "news": 1})
        result = _extract_top_subreddits(posts, top_n=3)
        self.assertEqual(result[0], "politics")
        self.assertEqual(result[1], "worldnews")
        self.assertEqual(result[2], "news")

    def test_excludes_specified_subs(self):
        posts = self._make_posts({"all": 10, "politics": 5})
        result = _extract_top_subreddits(posts, top_n=5, exclude={"all"})
        self.assertNotIn("all", result)
        self.assertIn("politics", result)

    def test_respects_top_n_limit(self):
        posts = self._make_posts({"a": 5, "b": 4, "c": 3, "d": 2, "e": 1})
        result = _extract_top_subreddits(posts, top_n=2)
        self.assertEqual(len(result), 2)

    def test_empty_posts_returns_empty(self):
        result = _extract_top_subreddits([], top_n=5)
        self.assertEqual(result, [])


class TestCollectRedditData(unittest.TestCase):
    def _make_reddit(self):
        reddit = MagicMock()
        reddit.subreddits.search.return_value = iter([])
        return reddit

    @patch("src.internal.pipeline.scrape.reddit.fetch.fetch_comments", return_value=[])
    @patch("src.internal.pipeline.scrape.reddit.fetch.fetch_posts", return_value=[])
    @patch(
        "src.internal.pipeline.scrape.reddit.fetch.discover_subreddits",
        return_value=["all"],
    )
    def test_calls_discover_with_search_term(
        self, mock_discover, mock_fetch, mock_comments
    ):
        reddit = self._make_reddit()
        collect_reddit_data("immigration", reddit=reddit)
        mock_discover.assert_called_once()
        call_args = mock_discover.call_args
        self.assertEqual(call_args[0][1], "immigration")

    @patch("src.internal.pipeline.scrape.reddit.fetch.fetch_comments", return_value=[])
    @patch("src.internal.pipeline.scrape.reddit.fetch.fetch_posts")
    @patch(
        "src.internal.pipeline.scrape.reddit.fetch.discover_subreddits",
        return_value=["all"],
    )
    def test_phase2_re_queries_top_subs(self, mock_discover, mock_fetch, mock_comments):
        """
        Phase 2: subreddits dominant in r/all results should
        be re-fetched directly.
        """
        # r/all returns posts from "politics" (3) and "worldnews" (2)
        all_posts = [_make_post("politics", f"p{i}") for i in range(3)]
        all_posts += [_make_post("worldnews", f"w{i}") for i in range(2)]

        # First calls (r/all) return the posts; subsequent calls return empty
        mock_fetch.side_effect = lambda *args, **kwargs: (
            all_posts if kwargs.get("subreddit_name") == "all" else []
        )

        reddit = self._make_reddit()
        collect_reddit_data(
            "test",
            scrape_config={"subreddit_discovery_limit": 0, "phase2_top_n": 2},
            reddit=reddit,
        )

        called_subs = {
            call.kwargs.get("subreddit_name") or call.args[2]
            for call in mock_fetch.call_args_list
        }
        self.assertIn("politics", called_subs)
        self.assertIn("worldnews", called_subs)

    @patch("src.internal.pipeline.scrape.reddit.fetch.fetch_comments", return_value=[])
    @patch("src.internal.pipeline.scrape.reddit.fetch.fetch_posts")
    @patch(
        "src.internal.pipeline.scrape.reddit.fetch.discover_subreddits",
        return_value=["all"],
    )
    def test_deduplicates_posts(self, mock_discover, mock_fetch, mock_comments):
        """
        Same platform_id appearing from multiple subreddit fetches
        should be deduped.
        """
        duplicate_post = _make_post("politics", "abc123")
        mock_fetch.return_value = [duplicate_post]

        reddit = self._make_reddit()
        result = collect_reddit_data(
            "test",
            scrape_config={"subreddit_discovery_limit": 0, "phase2_top_n": 0},
            reddit=reddit,
        )
        post_ids = [p["platform_id"] for p in result["data"]["posts"]]
        self.assertEqual(len(post_ids), len(set(post_ids)))

    @patch("src.internal.pipeline.scrape.reddit.fetch.fetch_comments", return_value=[])
    @patch("src.internal.pipeline.scrape.reddit.fetch.fetch_posts", return_value=[])
    @patch(
        "src.internal.pipeline.scrape.reddit.fetch.discover_subreddits",
        return_value=["all"],
    )
    def test_result_schema_unchanged(self, mock_discover, mock_fetch, mock_comments):
        """collect_reddit_data must still return the same top-level keys."""
        reddit = self._make_reddit()
        result = collect_reddit_data("topic", scrape_config={}, reddit=reddit)
        for key in ("search_term", "collected_at", "config_used", "data", "summary"):
            self.assertIn(key, result)
        for key in ("posts", "comments"):
            self.assertIn(key, result["data"])

    @patch("src.internal.pipeline.scrape.reddit.fetch.fetch_comments", return_value=[])
    @patch("src.internal.pipeline.scrape.reddit.fetch.fetch_posts", return_value=[])
    @patch(
        "src.internal.pipeline.scrape.reddit.fetch.discover_subreddits",
        return_value=["all"],
    )
    def test_summary_includes_subreddits_searched(
        self, mock_discover, mock_fetch, mock_comments
    ):
        reddit = self._make_reddit()
        result = collect_reddit_data("test", reddit=reddit)
        self.assertIn("subreddits_searched", result["summary"])
        self.assertIn("all", result["summary"]["subreddits_searched"])


class TestPresetConfigs(unittest.TestCase):
    def test_quick_config_skips_discovery(self):
        self.assertEqual(QUICK_CONFIG["subreddit_discovery_limit"], 0)
        self.assertEqual(QUICK_CONFIG["phase2_top_n"], 0)


if __name__ == "__main__":
    unittest.main()
