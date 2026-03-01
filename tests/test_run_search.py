import unittest
from unittest.mock import patch

from src.internal.pipeline.llm.run_search import run_search
from src.internal.pipeline.llm.types import ItemScore, NormalizedItem, SearchRequest


def _item_score(id: str, stance: int = 1) -> ItemScore:
    sentiment, animosity = 3, 2
    r = stance * (sentiment + 0.5 * animosity)
    return ItemScore(
        id=id, sentiment=sentiment, stance=stance, animosity=animosity, r=r
    )


class RunSearchTests(unittest.TestCase):
    @patch("src.internal.pipeline.llm.run_search.assess_items")
    @patch("src.internal.pipeline.llm.run_search._collect_and_normalize")
    def test_happy_path(self, mock_collect, mock_assess):
        mock_collect.return_value = [
            NormalizedItem(
                "p1",
                "this is a sufficiently long post text for testing",
                "https://reddit.com/p1",
                "2026",
                10,
                "post",
            ),
            NormalizedItem(
                "c1",
                "this is a sufficiently long comment text for testing",
                "https://reddit.com/c1",
                "2026",
                5,
                "comment",
            ),
        ]
        mock_assess.return_value = [
            _item_score("p1", stance=1),
            _item_score("c1", stance=-1),
        ]

        result = run_search(SearchRequest(query="immigration"))
        self.assertEqual(result.status, "ok")
        self.assertIsNotNone(result.polarization_score)
        self.assertGreater(len(result.evidence), 0)

    @patch("src.internal.pipeline.llm.run_search.assess_items")
    @patch("src.internal.pipeline.llm.run_search._collect_and_normalize")
    def test_low_sample_caps_confidence(self, mock_collect, mock_assess):
        mock_collect.return_value = [
            NormalizedItem(
                "p1",
                "this is a sufficiently long post text for testing",
                "https://reddit.com/p1",
                "2026",
                10,
                "post",
            ),
        ]
        mock_assess.return_value = [_item_score("p1", stance=1)]

        result = run_search(SearchRequest(query="topic"))
        self.assertEqual(result.status, "ok")
        self.assertLessEqual(result.confidence, 0.4)

    @patch("src.internal.pipeline.llm.run_search._collect_and_normalize")
    def test_sparse_data_returns_degraded(self, mock_collect):
        mock_collect.return_value = []
        result = run_search(SearchRequest(query="rare topic"))
        self.assertEqual(result.status, "degraded")
        self.assertIsNone(result.polarization_score)

    def test_empty_query_raises(self):
        with self.assertRaises(ValueError):
            run_search(SearchRequest(query="   "))

    @patch("src.internal.pipeline.llm.run_search.assess_items")
    @patch("src.internal.pipeline.llm.run_search._collect_and_normalize")
    def test_all_neutral_scores_zero_polarization(self, mock_collect, mock_assess):
        mock_collect.return_value = [
            NormalizedItem(
                "p1",
                "neutral text about the topic for testing here",
                "https://reddit.com/p1",
                "2026",
                5,
                "post",
            ),
        ]
        mock_assess.return_value = [
            ItemScore(id="p1", sentiment=3, stance=0, animosity=1, r=0.0),
        ]

        result = run_search(SearchRequest(query="bland topic"))
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.polarization_score, 0.0)


if __name__ == "__main__":
    unittest.main()
