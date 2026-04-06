import unittest

from src.internal.pipeline.domain import NormalizedItem
from src.internal.pipeline.llm.normalize import (
    clean_text,
    dedupe_items,
    filter_item,
    select_top_items,
)
from src.internal.pipeline.scrape.normalize import normalize_raw_item


class NormalizeTests(unittest.TestCase):
    def test_clean_text_collapses_whitespace(self):
        self.assertEqual(clean_text("a\n\n b\t c"), "a b c")

    def test_filter_item_rejects_short_deleted_and_missing_id(self):
        self.assertFalse(filter_item({"id": "1", "text": "tiny"}, min_text_length=20))
        self.assertFalse(
            filter_item({"id": "1", "text": "[deleted]"}, min_text_length=1)
        )
        self.assertFalse(
            filter_item(
                {"id": "", "text": "this is long enough text"}, min_text_length=10
            )
        )

    def test_dedupe_and_select(self):
        items = [
            NormalizedItem("1", "a", "u", "t", 3, "post"),
            NormalizedItem("1", "a2", "u", "t", 2, "post"),
            NormalizedItem("2", "b", "u", "t", 10, "comment"),
        ]
        deduped = dedupe_items(items)
        self.assertEqual([x.id for x in deduped], ["1", "2"])

    def test_dedupe_by_content_catches_syndicated_articles(self):
        """Same text on different URLs (syndicated GNews) should be dropped."""
        same_text = "Climate bill passes senate with bipartisan support."
        items = [
            NormalizedItem("gnews_https://nytimes.com/article", same_text, "https://nytimes.com/article", "t", 0, "post", "gnews"),
            NormalizedItem("gnews_https://apnews.com/article", same_text, "https://apnews.com/article", "t", 0, "post", "gnews"),
            NormalizedItem("gnews_https://bbc.com/article", "Different article text here.", "https://bbc.com/article", "t", 0, "post", "gnews"),
        ]
        deduped = dedupe_items(items)
        self.assertEqual(len(deduped), 2)
        self.assertEqual(deduped[0].id, "gnews_https://nytimes.com/article")
        self.assertEqual(deduped[1].id, "gnews_https://bbc.com/article")

    def test_dedupe_content_comparison_is_case_insensitive(self):
        """Content dedup normalises to lowercase before comparing."""
        items = [
            NormalizedItem("id_1", "Hello World", "u1", "t", 0, "post"),
            NormalizedItem("id_2", "hello world", "u2", "t", 0, "post"),
        ]
        deduped = dedupe_items(items)
        self.assertEqual(len(deduped), 1)
        self.assertEqual(deduped[0].id, "id_1")

    def test_normalize_raw_item(self):
        raw = {
            "platform_id": "abc",
            "text": " some text ",
            "url": "https://x",
            "timestamp": "2026-01-01T00:00:00Z",
            "engagement": {"score": 7},
            "metadata": {"content_type": "post"},
        }
        n = normalize_raw_item(raw)
        self.assertEqual(n.id, "abc")
        self.assertEqual(n.text, "some text")
        self.assertEqual(n.engagement_score, 7)
        self.assertEqual(n.content_type, "post")
        self.assertEqual(n.platform, "unknown")

    def test_normalize_extracts_platform_and_source_lean(self):
        raw = {
            "platform_id": "gnews_1",
            "source": "gnews",
            "text": "some article text",
            "url": "https://x",
            "timestamp": "2026-01-01T00:00:00Z",
            "engagement": {"score": 0},
            "metadata": {"content_type": "post"},
            "source_lean": "left",
        }
        n = normalize_raw_item(raw)
        self.assertEqual(n.platform, "gnews")
        self.assertEqual(n.source_lean, "left")

    def test_normalize_extracts_parent_video_id(self):
        raw = {
            "platform_id": "yt_comment_1",
            "source": "youtube",
            "text": "some comment",
            "url": "https://youtube.com",
            "timestamp": "2026-01-01T00:00:00Z",
            "engagement": {"score": 5},
            "metadata": {"content_type": "comment", "parent_video_id": "abc123"},
        }
        n = normalize_raw_item(raw)
        self.assertEqual(n.parent_video_id, "abc123")
        self.assertEqual(n.platform, "youtube")


if __name__ == "__main__":
    unittest.main()
