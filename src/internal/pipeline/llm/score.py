from __future__ import annotations

import math

from .types import ItemScore

# Maximum possible population stdev: perfect 50/50 split with r = ±7.5
# (stance=±1, sentiment=5, animosity=5 → r = ±(5 + 0.5*5) = ±7.5)
_P_MAX = 7.5


def compute_polarization(item_scores: list[ItemScore]) -> float:
    """Return a 0-100 polarization score.

    Formula: pstdev(r_values) / P_MAX * 100
    where r_i = stance * (sentiment + 0.5 * animosity)

    Neutral items contribute r=0, pulling stdev toward centre but less
    aggressively than a hard opinionated_ratio multiplier.
    All-neutral or all-one-side → stdev=0 → score=0.
    """
    if not item_scores:
        return 0.0

    r_values = [s.r for s in item_scores]
    n = len(r_values)
    mean = sum(r_values) / n
    variance = sum((r - mean) ** 2 for r in r_values) / n
    std = math.sqrt(variance)

    raw = std / _P_MAX * 100
    return min(round(raw, 2), 100.0)
