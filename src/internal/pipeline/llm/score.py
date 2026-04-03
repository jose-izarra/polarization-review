from __future__ import annotations

import math

from src.internal.pipeline.domain import ItemScore

# Maximum possible population stdev: perfect 50/50 split with r = ±7.5
# (stance=±1, sentiment=5, animosity=5 → r = ±(5 + 0.5*5) = ±7.5)
_P_MAX = 7.5


def compute_polarization(item_scores: list[ItemScore]) -> float:
    """Return a 0-100 polarization score.

    Formula: pstdev(opinionated_r) * opinionated_ratio / P_MAX * 100
    where r_i = stance * (sentiment + 0.5 * animosity)
    and opinionated_ratio = n_opinionated / n_total

    Only opinionated items (stance != 0) enter the stdev calculation,
    so neutral items cannot create false variance when everyone agrees.
    The ratio then scales the score down proportionally when most items
    are neutral, so a fringe 50/50 feud among a small minority scores
    lower than a society-wide split.

    All-neutral or all-one-side → stdev=0 → score=0.
    """
    if not item_scores:
        return 0.0

    opinionated = [s for s in item_scores if s.stance != 0]
    if not opinionated:
        return 0.0

    opinionated_r = [s.r for s in opinionated]
    ratio = len(opinionated) / len(item_scores)
    n = len(opinionated_r)
    mean = sum(opinionated_r) / n
    variance = sum((r - mean) ** 2 for r in opinionated_r) / n
    std = math.sqrt(variance)

    raw = std * ratio / _P_MAX * 100
    return min(round(raw, 2), 100.0)
