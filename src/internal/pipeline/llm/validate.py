"""Validation suite for polarization formula and pipeline."""

from __future__ import annotations

from .score import compute_polarization
from src.internal.pipeline.domain import ItemScore


def generate_synthetic_dataset(
    n_for: int,
    n_against: int,
    n_neutral: int,
    animosity_level: int = 3,
) -> list[ItemScore]:
    """Generate a synthetic dataset with controlled parameters.

    Args:
        n_for: Number of items with stance=1
        n_against: Number of items with stance=-1
        n_neutral: Number of items with stance=0
        animosity_level: Animosity value (1-5) for all opinionated items
    """
    scores: list[ItemScore] = []
    idx = 0
    for _ in range(n_for):
        r = 1 * (3 + 0.5 * animosity_level)
        scores.append(
            ItemScore(
                id=str(idx),
                sentiment=3,
                stance=1,
                animosity=animosity_level,
                r=r,
            )
        )
        idx += 1
    for _ in range(n_against):
        r = -1 * (3 + 0.5 * animosity_level)
        scores.append(
            ItemScore(
                id=str(idx),
                sentiment=3,
                stance=-1,
                animosity=animosity_level,
                r=r,
            )
        )
        idx += 1
    for _ in range(n_neutral):
        scores.append(
            ItemScore(
                id=str(idx),
                sentiment=3,
                stance=0,
                animosity=1,
                r=0.0,
            )
        )
        idx += 1
    return scores


def run_known_topics() -> list[dict]:
    """Run formula against known synthetic scenarios and return pass/fail results."""
    cases = [
        {
            "name": "50/50 split high animosity",
            "dataset": generate_synthetic_dataset(10, 10, 0, animosity_level=5),
            "expect_high": True,
        },
        {
            "name": "all one side",
            "dataset": generate_synthetic_dataset(20, 0, 0, animosity_level=5),
            "expect_zero": True,
        },
        {
            "name": "all neutral",
            "dataset": generate_synthetic_dataset(0, 0, 20),
            "expect_zero": True,
        },
        {
            "name": "balanced low animosity",
            "dataset": generate_synthetic_dataset(10, 10, 0, animosity_level=1),
            "expect_moderate": True,
        },
    ]

    results = []
    for case in cases:
        score = compute_polarization(case["dataset"])
        passed = True
        reason = ""
        if case.get("expect_high"):
            passed = score >= 70
            reason = f"expected >= 80, got {score}"
        elif case.get("expect_zero"):
            passed = score == 0.0
            reason = f"expected 0, got {score}"
        elif case.get("expect_moderate"):
            passed = 0 < score < 80
            reason = f"expected 0 < score < 80, got {score}"
        results.append(
            {
                "name": case["name"],
                "score": score,
                "passed": passed,
                "reason": reason if not passed else "",
            }
        )
    return results
