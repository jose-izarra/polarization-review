import unittest

from src.internal.pipeline.domain import ItemScore
from src.internal.pipeline.llm.assess import ALPHA_DEFAULT
from src.internal.pipeline.llm.score import compute_polarization


def _make_score(stance: int, animosity: int = 3, sentiment: int = 5) -> ItemScore:
    r = stance * (sentiment + ALPHA_DEFAULT * animosity)
    return ItemScore(
        id="x",
        sentiment=sentiment,
        stance=stance,
        animosity=animosity,
        r=r,
    )


class TestComputePolarization(unittest.TestCase):
    def test_empty_returns_zero(self):
        self.assertEqual(compute_polarization([]), 0.0)

    def test_all_neutral_returns_zero(self):
        scores = [
            ItemScore(id=str(i), sentiment=5, stance=0, animosity=1, r=0.0)
            for i in range(10)
        ]
        self.assertEqual(compute_polarization(scores), 0.0)

    def test_all_one_side_returns_zero(self):
        """All for, no against -> distribution = 0 -> score = 0."""
        scores = [_make_score(1, animosity=5) for _ in range(10)]
        self.assertEqual(compute_polarization(scores), 0.0)

    def test_50_50_split_high_animosity(self):
        """Equal for/against with high animosity -> substantial score.

        animosity=5, sentiment=5, α=0.5 → r=±7.5, pstdev=7.5,
        score = 7.5/12.5*100 = 60.0.
        """
        scores = [_make_score(1, animosity=5) for _ in range(10)]
        scores += [_make_score(-1, animosity=5) for _ in range(10)]
        result = compute_polarization(scores)
        self.assertGreaterEqual(result, 60.0)
        self.assertLessEqual(result, 100.0)

    def test_50_50_split_max_animosity_reaches_100(self):
        """Perfect 50/50 with max sentiment+animosity -> 100.

        sentiment=10, animosity=5, α=0.5 → r = ±(10+0.5*5) = ±12.5 = P_MAX,
        so pstdev = 12.5 → score = 100.
        """
        scores = [_make_score(1, animosity=5, sentiment=10) for _ in range(5)]
        scores += [_make_score(-1, animosity=5, sentiment=10) for _ in range(5)]
        result = compute_polarization(scores)
        self.assertEqual(result, 100.0)

    def test_animosity_scales_proportionally(self):
        """Higher animosity should produce higher score."""
        low = [_make_score(1, animosity=1) for _ in range(5)]
        low += [_make_score(-1, animosity=1) for _ in range(5)]

        high = [_make_score(1, animosity=4) for _ in range(5)]
        high += [_make_score(-1, animosity=4) for _ in range(5)]

        self.assertLess(compute_polarization(low), compute_polarization(high))

    def test_neutrals_dilute_score(self):
        """Adding neutrals reduces score via opinionated_ratio, not false variance."""
        pure = [_make_score(1, animosity=3) for _ in range(5)]
        pure += [_make_score(-1, animosity=3) for _ in range(5)]

        diluted = list(pure) + [
            ItemScore(id=str(i), sentiment=5, stance=0, animosity=1, r=0.0)
            for i in range(10)
        ]

        self.assertGreater(compute_polarization(pure), compute_polarization(diluted))

    def test_imbalanced_sides_reduces_score(self):
        """9 for vs 1 against should score lower than 5 vs 5."""
        balanced = [_make_score(1) for _ in range(5)]
        balanced += [_make_score(-1) for _ in range(5)]

        imbalanced = [_make_score(1) for _ in range(9)]
        imbalanced += [_make_score(-1)]

        self.assertGreater(
            compute_polarization(balanced),
            compute_polarization(imbalanced),
        )

    def test_score_capped_at_100(self):
        result = compute_polarization([_make_score(1, 5), _make_score(-1, 5)])
        self.assertLessEqual(result, 100.0)


if __name__ == "__main__":
    unittest.main()
