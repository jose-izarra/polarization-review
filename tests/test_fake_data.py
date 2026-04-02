"""Tests for fake data scenarios running through the real pipeline."""

import unittest
from unittest.mock import patch

from src.internal.pipeline.domain import SearchRequest
from src.internal.pipeline.llm.fake_data import (
    FAKE_SCENARIOS,
    get_fake_data,
)
from src.internal.pipeline.llm.mock_llm import mock_call_model
from src.internal.pipeline.llm.run_search import run_search


class TestFakeDataModule(unittest.TestCase):
    def test_all_scenarios_exist(self):
        for mode in ("fake_polarized", "fake_moderate", "fake_neutral"):
            query, items = get_fake_data(mode)
            self.assertIsInstance(query, str)
            self.assertGreater(len(items), 0)

    def test_unknown_mode_raises(self):
        with self.assertRaises(KeyError):
            get_fake_data("fake_unknown")

    def test_items_have_required_fields(self):
        for mode in FAKE_SCENARIOS:
            _, items = get_fake_data(mode)
            for item in items:
                self.assertTrue(item.id)
                self.assertTrue(len(item.text) > 20)
                self.assertTrue(item.url)
                self.assertIn(item.content_type, ("post", "comment"))

    def test_polarized_has_balanced_sides(self):
        """Polarized scenario should have items from multiple platforms."""
        _, items = get_fake_data("fake_polarized")
        platforms = {item.platform for item in items}
        self.assertTrue(len(platforms) >= 2)

    def test_each_scenario_has_enough_items(self):
        for mode in FAKE_SCENARIOS:
            _, items = get_fake_data(mode)
            self.assertGreaterEqual(len(items), 20)


class TestFakeDataPipeline(unittest.TestCase):
    """Run fake data through the pipeline with mock LLM."""

    @patch("src.internal.pipeline.llm.run_search._determine_video_stances")
    @patch("src.internal.pipeline.llm.run_search.assess_items")
    @patch("src.internal.pipeline.llm.run_search.filter_relevant_items")
    def test_fake_polarized_runs_ok(self, mock_filter, mock_assess, mock_vs):
        mock_vs.return_value = {}
        # filter passes everything through
        mock_filter.side_effect = lambda q, items, **kw: items
        # assess uses mock LLM
        from src.internal.pipeline.llm.llm_assess import assess_items

        mock_assess.side_effect = lambda q, items, **kw: assess_items(
            q, items, call_model=mock_call_model
        )

        req = SearchRequest(query="ignored", mode="fake_polarized")
        result = run_search(req)
        self.assertEqual(result.status, "ok")
        self.assertIsNotNone(result.polarization_score)
        self.assertGreater(len(result.evidence), 0)
        self.assertEqual(result.query, "gun control in America")

    @patch("src.internal.pipeline.llm.run_search._determine_video_stances")
    @patch("src.internal.pipeline.llm.run_search.assess_items")
    @patch("src.internal.pipeline.llm.run_search.filter_relevant_items")
    def test_fake_moderate_runs_ok(self, mock_filter, mock_assess, mock_vs):
        mock_vs.return_value = {}
        mock_filter.side_effect = lambda q, items, **kw: items
        from src.internal.pipeline.llm.llm_assess import assess_items

        mock_assess.side_effect = lambda q, items, **kw: assess_items(
            q, items, call_model=mock_call_model
        )

        req = SearchRequest(query="ignored", mode="fake_moderate")
        result = run_search(req)
        self.assertEqual(result.status, "ok")
        self.assertIsNotNone(result.polarization_score)
        self.assertEqual(result.query, "mandatory return to office policies")

    @patch("src.internal.pipeline.llm.run_search._determine_video_stances")
    @patch("src.internal.pipeline.llm.run_search.assess_items")
    @patch("src.internal.pipeline.llm.run_search.filter_relevant_items")
    def test_fake_neutral_runs_ok(self, mock_filter, mock_assess, mock_vs):
        mock_vs.return_value = {}
        mock_filter.side_effect = lambda q, items, **kw: items
        from src.internal.pipeline.llm.llm_assess import assess_items

        mock_assess.side_effect = lambda q, items, **kw: assess_items(
            q, items, call_model=mock_call_model
        )

        req = SearchRequest(query="ignored", mode="fake_neutral")
        result = run_search(req)
        self.assertEqual(result.status, "ok")
        self.assertIsNotNone(result.polarization_score)
        self.assertEqual(result.query, "NASA funding and space exploration")

    def test_unknown_fake_mode_returns_error(self):
        req = SearchRequest(query="test", mode="fake_unknown")
        result = run_search(req)
        self.assertEqual(result.status, "error")
        self.assertIn("Unknown", result.error_message)

    @patch("src.internal.pipeline.llm.run_search._determine_video_stances")
    @patch("src.internal.pipeline.llm.run_search.assess_items")
    @patch("src.internal.pipeline.llm.run_search.filter_relevant_items")
    def test_fake_mode_skips_scraping(self, mock_filter, mock_assess, mock_vs):
        """Fake mode should never call _collect_and_normalize."""
        mock_vs.return_value = {}
        mock_filter.side_effect = lambda q, items, **kw: items
        from src.internal.pipeline.llm.llm_assess import assess_items

        mock_assess.side_effect = lambda q, items, **kw: assess_items(
            q, items, call_model=mock_call_model
        )

        with patch(
            "src.internal.pipeline.llm.run_search._collect_and_normalize"
        ) as mock_collect:
            req = SearchRequest(query="test", mode="fake_polarized")
            result = run_search(req)
            mock_collect.assert_not_called()
            self.assertEqual(result.status, "ok")


if __name__ == "__main__":
    unittest.main()
