from __future__ import annotations

import math

from .types import ItemScore

ALPHA = 0.5
# Theoretical max std dev: stance=±1, sentiment=5, animosity=5
# r_max = 1 * (5 + 0.5*5) = 7.5; half items at +7.5, half at -7.5 → std dev = 7.5
P_MAX = (1 + ALPHA) * 5  # = 7.5


def compute_polarization(item_scores: list[ItemScore], alpha: float = ALPHA) -> float:
    """Return a 0–100 polarization score derived from per-item r values.

    Neutral items (stance=0) contribute r=0, which dampens polarization as
    intended by the formula — a fully neutral sample scores near zero.
    """
    r_values = [s.r for s in item_scores]
    if not r_values:
        return 0.0
    r_mean = sum(r_values) / len(r_values)
    variance = sum((r - r_mean) ** 2 for r in r_values) / len(r_values)
    P = math.sqrt(variance)
    p_max = (1 + alpha) * 5
    return min(round((P / p_max) * 100, 2), 100.0)
