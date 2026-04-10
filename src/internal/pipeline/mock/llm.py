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
    {"sentiment": 4, "stance": 1, "animosity": 2, "reason": "mock positive stance"},
    {"sentiment": 3, "stance": -1, "animosity": 3, "reason": "mock negative stance"},
    {"sentiment": 5, "stance": 0, "animosity": 1, "reason": "mock neutral stance"},
    {"sentiment": 5, "stance": 1, "animosity": 4, "reason": "mock strong positive"},
    {"sentiment": 2, "stance": -1, "animosity": 2, "reason": "mock negative stance"},
]


def mock_call_model(system_prompt: str, user_payload: str) -> str:
    """Return a valid JSON array without calling any external API."""
    # Detect relevance filter prompt
    if "relevant" in system_prompt.lower():
        items = json.loads(user_payload).get("items", [])
        result = [{"id": item["id"], "relevant": True} for item in items]
        logger.debug(
            "mock_call_model: relevance — all %d relevant",
            len(result),
        )
        return json.dumps(result)

    # Detect YouTube query generation prompt
    if "youtube search quer" in system_prompt.lower():
        payload = json.loads(user_payload)
        original = payload.get("query", "topic")
        result = [
            original,
            f"against {original}",
            f"{original} debate analysis",
        ]
        logger.debug("mock_call_model: youtube queries for %r", original)
        return json.dumps(result)

    # Detect video stance prompt
    if "video" in system_prompt.lower() and "stance" in system_prompt.lower():
        items = json.loads(user_payload).get("videos", [])
        stances = [1, -1, 0]
        result = [
            {"id": item["id"], "stance": stances[i % len(stances)]}
            for i, item in enumerate(items)
        ]
        logger.debug("mock_call_model: video stances for %d videos", len(result))
        return json.dumps(result)

    # Default: scoring prompt
    items = json.loads(user_payload).get("items", [])
    scores = [
        {"id": item["id"], **_SCORE_CYCLE[i % len(_SCORE_CYCLE)]}
        for i, item in enumerate(items)
    ]
    logger.debug("mock_call_model: scored %d items", len(scores))
    return json.dumps(scores)
