"""Mock LLM backend for local development (ENV=local).

Returns deterministic scores derived from each item's position so results
are reproducible across runs without hitting the Gemini API.
"""

from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)

# Cycles through a mix of stances to produce a realistic polarization score.
_SCORE_CYCLE = [
    {"sentiment": 4, "stance": 1, "animosity": 2},
    {"sentiment": 3, "stance": -1, "animosity": 3},
    {"sentiment": 2, "stance": 0, "animosity": 1},
    {"sentiment": 5, "stance": 1, "animosity": 4},
    {"sentiment": 2, "stance": -1, "animosity": 2},
]


def mock_call_model(system_prompt: str, user_payload: str) -> str:
    """Return a valid JSON score array without calling any external API."""
    items = json.loads(user_payload).get("items", [])
    scores = [
        {"id": item["id"], **_SCORE_CYCLE[i % len(_SCORE_CYCLE)]}
        for i, item in enumerate(items)
    ]
    logger.debug("mock_call_model: scored %d items", len(scores))
    return json.dumps(scores)
