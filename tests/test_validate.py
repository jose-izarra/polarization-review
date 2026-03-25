import unittest

from src.internal.pipeline.llm.score import compute_polarization
from src.internal.pipeline.llm.validate import (
    generate_synthetic_dataset,
    run_known_topics,
)

import logging


class TestGenerateSyntheticDataset(unittest.TestCase):
    def test_correct_counts(self):
        ds = generate_synthetic_dataset(3, 4, 5)
        self.assertEqual(len(ds), 12)
        self.assertEqual(sum(1 for s in ds if s.stance == 1), 3)
        self.assertEqual(sum(1 for s in ds if s.stance == -1), 4)
        self.assertEqual(sum(1 for s in ds if s.stance == 0), 5)

    def test_animosity_applied(self):
        ds = generate_synthetic_dataset(2, 2, 0, animosity_level=4)
        for s in ds:
            if s.stance != 0:
                self.assertEqual(s.animosity, 4)

    def test_50_50_high_animosity_near_100(self):
        ds = generate_synthetic_dataset(10, 10, 0, animosity_level=5)
        score = compute_polarization(ds)
        self.assertGreaterEqual(score, 80.0)

    def test_50_50_low_animosity(self):
        ds = generate_synthetic_dataset(10, 10, 0, animosity_level=1)
        score = compute_polarization(ds)
        print(f"50/50 low animosity score: {score}")
        self.assertGreaterEqual(score, 10.0)
        self.assertLessEqual(score, 80.0)

    def test_all_one_side_zero(self):
        ds = generate_synthetic_dataset(20, 0, 0, animosity_level=5)
        self.assertEqual(compute_polarization(ds), 0.0)

    def test_all_neutral_zero(self):
        ds = generate_synthetic_dataset(0, 0, 20)
        self.assertEqual(compute_polarization(ds), 0.0)

    def test_animosity_scales_score(self):
        ds_low = generate_synthetic_dataset(5, 5, 0, animosity_level=1)
        ds_high = generate_synthetic_dataset(5, 5, 0, animosity_level=5)
        self.assertLess(
            compute_polarization(ds_low), compute_polarization(ds_high)
        )


class TestRunKnownTopics(unittest.TestCase):
    def test_all_scenarios_pass(self):
        results = run_known_topics()
        for r in results:
            self.assertTrue(r["passed"], f"Failed: {r['name']} — {r['reason']}")


if __name__ == "__main__":
    unittest.main()
