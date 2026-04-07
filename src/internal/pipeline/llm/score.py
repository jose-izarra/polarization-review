from __future__ import annotations

import math

from src.internal.pipeline.domain import ItemScore
from src.internal.pipeline.llm.assess import ALPHA_DEFAULT

# Maximum r magnitude for a single item: stance=±1, sentiment=5, animosity=5
# _P_MAX = max_sentiment + α * max_animosity = 5 + α*5
_P_MAX = 5 + ALPHA_DEFAULT * 5


def compute_polarization(item_scores: list[ItemScore]) -> float:
    """Return a 0-100 polarization score.

    Formula: pstdev(opinionated_r) * opinionated_ratio / P_MAX * 100
    where r_i = stance * (sentiment + α * animosity), P_MAX = 5 + α*5
    and opinionated_ratio = n_opinionated / n_total

    Only opinionated items (stance != 0) enter the stdev calculation.
    Requires both FOR and AGAINST items — consensus (all one-sided) returns 0
    because intensity variance within a single stance is not polarization.
    The ratio scales the score down when most items are neutral, so a fringe
    50/50 feud among a small minority scores lower than a society-wide split.
    """
    if not item_scores:
        return 0.0

    opinionated = [s for s in item_scores if s.stance != 0]
    if not opinionated:
        return 0.0

    # Polarization requires genuine opposition — if all opinionated items share
    # the same stance (consensus), intensity variance is not polarization.
    has_for = any(s.stance > 0 for s in opinionated)
    has_against = any(s.stance < 0 for s in opinionated)
    if not (has_for and has_against):
        return 0.0

    opinionated_r = [s.r for s in opinionated]
    ratio = len(opinionated) / len(item_scores)
    n = len(opinionated_r)
    mean = sum(opinionated_r) / n
    variance = sum((r - mean) ** 2 for r in opinionated_r) / n
    std = math.sqrt(variance)

    raw = std * ratio / _P_MAX * 100
    return min(round(raw, 2), 100.0)
