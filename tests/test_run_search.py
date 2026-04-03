import unittest
from unittest.mock import patch

from src.internal.pipeline.domain import ItemScore, NormalizedItem, SearchRequest
from src.internal.pipeline.llm.run_search import run_search


def _item_score(id: str, stance: int = 1) -> ItemScore:
    sentiment, animosity = 3, 2
    r = stance * (sentiment + 0.5 * animosity)
    return ItemScore(
        id=id, sentiment=sentiment, stance=stance, animosity=animosity, r=r
    )


def _make_item(
    id: str,
    text: str = "this is a sufficiently long post text for testing",
) -> NormalizedItem:
    return NormalizedItem(
        id,
        text,
        f"https://reddit.com/{id}",
        "2026",
        10,
        "post",
    )


class RunSearchTests(unittest.TestCase):
    @patch("src.internal.pipeline.llm.sources.registry.get_processors", return_value=[])
    @patch("src.internal.pipeline.llm.run_search.filter_relevant_items")
    @patch("src.internal.pipeline.llm.run_search.assess_items")
    @patch("src.internal.pipeline.llm.run_search._collect_and_normalize")
    def test_happy_path(
        self, mock_collect, mock_assess, mock_filter, mock_processors
    ):
        items = [_make_item("p1"), _make_item("c1")]
        mock_collect.return_value = items
        mock_filter.return_value = items
        mock_assess.return_value = [
            _item_score("p1", stance=1),
            _item_score("c1", stance=-1),
        ]

        result = run_search(SearchRequest(query="immigration"))
        self.assertEqual(result.status, "ok")
        self.assertIsNotNone(result.polarization_score)
        self.assertGreater(len(result.evidence), 0)
        self.assertIn(result.confidence_label, ("high", "moderate", "low", "very_low"))

    @patch("src.internal.pipeline.llm.sources.registry.get_processors", return_value=[])
    @patch("src.internal.pipeline.llm.run_search.filter_relevant_items")
    @patch("src.internal.pipeline.llm.run_search.assess_items")
    @patch("src.internal.pipeline.llm.run_search._collect_and_normalize")
    def test_confidence_linear_ramp(
        self, mock_collect, mock_assess, mock_filter, mock_processors
    ):
        """1 item -> confidence = 0.1"""
        items = [_make_item("p1")]
        mock_collect.return_value = items
        mock_filter.return_value = items
        mock_assess.return_value = [_item_score("p1", stance=1)]

        result = run_search(SearchRequest(query="topic"))
        self.assertEqual(result.status, "ok")
        self.assertAlmostEqual(result.confidence, 0.1)
        self.assertEqual(result.confidence_label, "very_low")

    @patch("src.internal.pipeline.llm.run_search._collect_and_normalize")
    def test_sparse_data_returns_degraded(self, mock_collect):
        mock_collect.return_value = []
        result = run_search(SearchRequest(query="rare topic"))
        self.assertEqual(result.status, "degraded")
        self.assertIsNone(result.polarization_score)

    def test_empty_query_raises(self):
        with self.assertRaises(ValueError):
            run_search(SearchRequest(query="   "))

    @patch("src.internal.pipeline.llm.sources.registry.get_processors", return_value=[])
    @patch("src.internal.pipeline.llm.run_search.filter_relevant_items")
    @patch("src.internal.pipeline.llm.run_search.assess_items")
    @patch("src.internal.pipeline.llm.run_search._collect_and_normalize")
    def test_all_neutral_scores_zero_polarization(
        self, mock_collect, mock_assess, mock_filter, mock_processors
    ):
        items = [_make_item("p1")]
        mock_collect.return_value = items
        mock_filter.return_value = items
        mock_assess.return_value = [
            ItemScore(id="p1", sentiment=3, stance=0, animosity=1, r=0.0),
        ]

        result = run_search(SearchRequest(query="bland topic"))
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.polarization_score, 0.0)

    @patch("src.internal.pipeline.llm.run_search.filter_relevant_items")
    @patch("src.internal.pipeline.llm.run_search._collect_and_normalize")
    def test_all_filtered_irrelevant_returns_degraded(self, mock_collect, mock_filter):
        mock_collect.return_value = [_make_item("p1")]
        mock_filter.return_value = []

        result = run_search(SearchRequest(query="off topic"))
        self.assertEqual(result.status, "degraded")
        self.assertIsNone(result.polarization_score)

    @patch("src.internal.pipeline.llm.sources.registry.get_processors", return_value=[])
    @patch("src.internal.pipeline.llm.run_search.filter_relevant_items")
    @patch("src.internal.pipeline.llm.run_search.assess_items")
    @patch("src.internal.pipeline.llm.run_search._collect_and_normalize")
    def test_evidence_includes_scores(
        self, mock_collect, mock_assess, mock_filter, mock_processors
    ):
        items = [_make_item("p1")]
        mock_collect.return_value = items
        mock_filter.return_value = items
        mock_assess.return_value = [_item_score("p1", stance=1)]

        result = run_search(SearchRequest(query="topic"))
        self.assertEqual(len(result.evidence), 1)
        ev = result.evidence[0]
        self.assertEqual(ev.stance, 1)
        self.assertIsNotNone(ev.sentiment)
        self.assertIsNotNone(ev.animosity)


if __name__ == "__main__":
    unittest.main()
