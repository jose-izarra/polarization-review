from __future__ import annotations

from .types import ItemScore


def compute_polarization(item_scores: list[ItemScore]) -> float:
    """Return a 0-100 polarization score.

    Formula: distribution * animosity_score * opinionated_ratio * 20
    - distribution: 1 - |n_for - n_against| / (n_for + n_against)
    - animosity_score: mean animosity of opinionated items
    - opinionated_ratio: fraction of items with stance != 0
    """
    if not item_scores:
        return 0.0

    total = len(item_scores)
    n_for = sum(1 for s in item_scores if s.stance == 1)
    n_against = sum(1 for s in item_scores if s.stance == -1)
    n_opinionated = n_for + n_against

    if n_opinionated == 0:
        return 0.0

    eps = 1e-9
    distribution = 1 - abs(n_for - n_against) / (n_opinionated + eps)

    opinionated_items = [s for s in item_scores if s.stance != 0]
    animosity_score = (
        sum(s.animosity for s in opinionated_items)
        / len(opinionated_items)
    )

    opinionated_ratio = n_opinionated / total

    raw = distribution * animosity_score * opinionated_ratio
    return min(round(raw * 20, 2), 100.0)
