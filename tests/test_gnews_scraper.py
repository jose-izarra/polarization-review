import json
import os
import unittest
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse


def _make_gnews_response(articles: list[dict]) -> MagicMock:
    body = json.dumps({"totalArticles": len(articles), "articles": articles}).encode()
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def _sample_article(n: int = 1, url: str | None = None) -> dict:
    return {
        "title": f"Article title {n}",
        "description": f"Article description {n}",
        "url": url or f"https://example.com/article-{n}",
        "publishedAt": "2026-01-15T10:00:00Z",
        "source": {"name": "Example News", "url": "https://example.com"},
        "image": None,
        "content": f"Full content {n}...",
    }


class TestCollectGnewsData(unittest.TestCase):
    def setUp(self):
        os.environ["GNEWS_API_KEY"] = "fake-gnews-key"

    def tearDown(self):
        os.environ.pop("GNEWS_API_KEY", None)

    @patch("src.internal.pipeline.scrape.gnews.fetch.request.urlopen")
    def test_happy_path_returns_posts(self, mock_urlopen):
        articles = [_sample_article(i) for i in range(3)]
        mock_urlopen.return_value = _make_gnews_response(articles)

        from src.internal.pipeline.scrape.gnews.fetch import collect_gnews_data

        result = collect_gnews_data("climate change")
        data = result["data"]

        self.assertEqual(len(data["posts"]), 3)
        self.assertEqual(data["comments"], [])

    @patch("src.internal.pipeline.scrape.gnews.fetch.request.urlopen")
    def test_post_raw_item_shape(self, mock_urlopen):
        mock_urlopen.return_value = _make_gnews_response([_sample_article(1)])

        from src.internal.pipeline.scrape.gnews.fetch import collect_gnews_data

        result = collect_gnews_data("politics")
        post = result["data"]["posts"][0]

        self.assertTrue(post["platform_id"].startswith("gnews_"))
        self.assertEqual(post["source"], "gnews")
        self.assertEqual(post["metadata"]["content_type"], "post")
        self.assertEqual(post["engagement"], {"score": 0})
        self.assertIn("timestamp", post)
        self.assertIn("url", post)

    @patch("src.internal.pipeline.scrape.gnews.fetch.request.urlopen")
    def test_text_field_is_title_dot_description(self, mock_urlopen):
        article = _sample_article(1)
        mock_urlopen.return_value = _make_gnews_response([article])

        from src.internal.pipeline.scrape.gnews.fetch import collect_gnews_data

        result = collect_gnews_data("topic")
        post = result["data"]["posts"][0]

        expected = f"{article['title']}. {article['description']}"
        self.assertEqual(post["text"], expected)

    @patch("src.internal.pipeline.scrape.gnews.fetch.request.urlopen")
    def test_source_lean_lookup(self, mock_urlopen):
        articles = [
            _sample_article(1, url="https://www.cnn.com/article-1"),
            _sample_article(2, url="https://www.foxnews.com/article-2"),
            _sample_article(3, url="https://reuters.com/article-3"),
            _sample_article(4, url="https://unknownsite.com/article-4"),
        ]
        mock_urlopen.return_value = _make_gnews_response(articles)

        from src.internal.pipeline.scrape.gnews.fetch import collect_gnews_data

        result = collect_gnews_data("topic")
        posts = result["data"]["posts"]

        self.assertEqual(posts[0]["source_lean"], "left")
        self.assertEqual(posts[1]["source_lean"], "right")
        self.assertEqual(posts[2]["source_lean"], "center")
        self.assertEqual(posts[3]["source_lean"], "unknown")

    @patch("src.internal.pipeline.scrape.gnews.fetch.request.urlopen")
    def test_time_filter_day_maps_to_1_day(self, mock_urlopen):
        captured_url = {}

        def capture(req, timeout=None):
            captured_url["url"] = req.full_url
            return _make_gnews_response([])

        mock_urlopen.side_effect = capture

        from src.internal.pipeline.scrape.gnews.fetch import collect_gnews_data

        collect_gnews_data("topic", time_filter="day")
        url = captured_url["url"]
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        from_str = params["from"][0]
        from datetime import datetime, timezone

        from_dt = datetime.strptime(from_str, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
        delta = datetime.now(tz=timezone.utc) - from_dt
        self.assertLessEqual(delta.days, 2)
        self.assertGreaterEqual(delta.days, 0)

    @patch("src.internal.pipeline.scrape.gnews.fetch.request.urlopen")
    def test_time_filter_week_maps_to_7_days(self, mock_urlopen):
        captured_url = {}

        def capture(req, timeout=None):
            captured_url["url"] = req.full_url
            return _make_gnews_response([])

        mock_urlopen.side_effect = capture

        from src.internal.pipeline.scrape.gnews.fetch import collect_gnews_data

        collect_gnews_data("topic", time_filter="week")
        url = captured_url["url"]
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        from datetime import datetime, timezone

        from_dt = datetime.strptime(params["from"][0], "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
        delta = datetime.now(tz=timezone.utc) - from_dt
        self.assertLessEqual(delta.days, 8)
        self.assertGreaterEqual(delta.days, 6)

    @patch("src.internal.pipeline.scrape.gnews.fetch.request.urlopen")
    def test_time_filter_month_maps_to_30_days(self, mock_urlopen):
        captured_url = {}

        def capture(req, timeout=None):
            captured_url["url"] = req.full_url
            return _make_gnews_response([])

        mock_urlopen.side_effect = capture

        from src.internal.pipeline.scrape.gnews.fetch import collect_gnews_data

        collect_gnews_data("topic", time_filter="month")
        url = captured_url["url"]
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        from datetime import datetime, timezone

        from_dt = datetime.strptime(params["from"][0], "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
        delta = datetime.now(tz=timezone.utc) - from_dt
        self.assertLessEqual(delta.days, 31)
        self.assertGreaterEqual(delta.days, 29)

    def test_missing_api_key_raises_runtime_error(self):
        os.environ.pop("GNEWS_API_KEY", None)

        from src.internal.pipeline.scrape.gnews.fetch import collect_gnews_data

        with self.assertRaises(RuntimeError):
            collect_gnews_data("anything")

    @patch("src.internal.pipeline.scrape.gnews.fetch.request.urlopen")
    def test_empty_articles_returns_empty_posts(self, mock_urlopen):
        mock_urlopen.return_value = _make_gnews_response([])

        from src.internal.pipeline.scrape.gnews.fetch import collect_gnews_data

        result = collect_gnews_data("niche topic")
        self.assertEqual(result["data"]["posts"], [])
        self.assertEqual(result["data"]["comments"], [])

    @patch("src.internal.pipeline.scrape.gnews.fetch.request.urlopen")
    def test_api_key_in_request_url(self, mock_urlopen):
        captured_url = {}

        def capture(req, timeout=None):
            captured_url["url"] = req.full_url
            return _make_gnews_response([])

        mock_urlopen.side_effect = capture

        from src.internal.pipeline.scrape.gnews.fetch import collect_gnews_data

        collect_gnews_data("topic")
        self.assertIn("fake-gnews-key", captured_url["url"])


if __name__ == "__main__":
    unittest.main()
