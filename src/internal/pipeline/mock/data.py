"""Aggregator for fake pipeline test scenarios.

Combines data_fictitious.py (FlobberFlopper-specific insults whose severity
the LLM cannot infer without lore knowledge), data_general.py (universally
understood strong language on fictional topics), and data_real_world.py
(structurally identical content on real-world topics) into a single registry.

Scenario keys:
  fake_polarized_fictitious    — fictional insults,        expected ~100
  fake_moderate_fictitious     — fictional insults,        expected ~35-70
  fake_neutral_fictitious      — no animosity,             expected ~0
  fake_polarized_general       — universal language,       expected ~100
  fake_moderate_general        — universal language,       expected ~35-70
  fake_neutral_general         — no animosity,             expected ~0
  fake_polarized_real_context  — Donald Trump (US),        expected ~100
  fake_moderate_real_context   — Federal Carbon Tax (US),  expected ~35-70
  fake_neutral_real_context    — New Orleans Mardi Gras,   expected ~0
"""

from __future__ import annotations

from src.internal.pipeline.domain import NormalizedItem
from src.internal.pipeline.mock.data_fictitious import (
    FAKE_SCENARIOS as _FICTITIOUS,
)
from src.internal.pipeline.mock.data_general import (
    FAKE_SCENARIOS as _GENERAL,
)
from src.internal.pipeline.mock.data_real_world import (
    FAKE_SCENARIOS as _REAL_CONTEXT,
)

FAKE_SCENARIOS: dict[str, tuple[str, list[NormalizedItem]]] = {
    **_FICTITIOUS,
    **_GENERAL,
    **_REAL_CONTEXT,
}


def get_fake_data(mode: str) -> tuple[str, list[NormalizedItem]]:
    """Return (query, items) for a fake scenario.

    Raises KeyError if mode is not a known fake scenario.
    """
    return FAKE_SCENARIOS[mode]
