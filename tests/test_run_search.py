import unittest
from unittest.mock import patch

from src.pipeline.run_search import run_search
from src.pipeline.types import LLMAssessment, NormalizedItem, SearchRequest


class RunSearchTests(unittest.TestCase):
    @patch("src.pipeline.run_search.assess_polarization")
    @patch("src.pipeline.run_search._collect_and_normalize")
    def test_happy_path(self, mock_collect_normalized, mock_assess):
        mock_collect_normalized.return_value = [
            NormalizedItem("p1", "this is a sufficiently long post text for testing", "https://reddit.com/p1", "2026", 10, "post"),
            NormalizedItem("c1", "this is a sufficiently long comment text for testing", "https://reddit.com/c1", "2026", 5, "comment"),
        ]
        mock_assess.return_value = LLMAssessment(
            polarization_score=62.0,
            confidence=0.9,
            rationale="Debate is strong across opposing sides.",
            evidence_ids=["p1", "c1"],
        )

        result = run_search(SearchRequest(query="immigration"))
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.polarization_score, 62.0)
        self.assertEqual(len(result.evidence), 2)

    @patch("src.pipeline.run_search.assess_polarization")
    @patch("src.pipeline.run_search._collect_and_normalize")
    def test_low_sample_caps_confidence(self, mock_collect_normalized, mock_assess):
        mock_collect_normalized.return_value = [
            NormalizedItem("p1", "this is a sufficiently long post text for testing", "https://reddit.com/p1", "2026", 10, "post")
        ]
        mock_assess.return_value = LLMAssessment(
            polarization_score=50.0,
            confidence=0.95,
            rationale="Some disagreement appears.",
            evidence_ids=["p1"],
        )

        result = run_search(SearchRequest(query="topic"))
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.confidence, 0.4)

    @patch("src.pipeline.run_search._collect_and_normalize")
    def test_sparse_data_returns_degraded(self, mock_collect_normalized):
        mock_collect_normalized.return_value = []
        result = run_search(SearchRequest(query="rare topic"))
        self.assertEqual(result.status, "degraded")
        self.assertIsNone(result.polarization_score)

    def test_empty_query_raises(self):
        with self.assertRaises(ValueError):
            run_search(SearchRequest(query="   "))


if __name__ == "__main__":
    unittest.main()
