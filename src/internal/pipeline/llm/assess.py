from __future__ import annotations

import json
import re
from dataclasses import replace

import logfire
from src.internal.pipeline.domain import ItemScore, NormalizedItem
from src.internal.pipeline.llm.client import call_llm
from src.internal.pipeline.llm.prompts import (
    _RELEVANCE_SYSTEM_PROMPT,
    _SYSTEM_PROMPT,
    _SYSTEM_PROMPT_STRICT,
)

_BATCH_SIZE = 15
_RELEVANCE_BATCH_SIZE = 25
_JSON_ARRAY_RE = re.compile(r"\[.*\]", re.DOTALL)
ALPHA_DEFAULT = 2


def _truncate(text: str, limit: int = 280) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3]}..."


def _extract_json_array(text: str) -> list:
    text = text.strip()
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    match = _JSON_ARRAY_RE.search(text)
    if not match:
        raise ValueError("No JSON array found in LLM response")
    return json.loads(match.group(0))


def _validate_item_scores(
    raw_items: list, alpha: float = ALPHA_DEFAULT
) -> list[ItemScore]:
    scores: list[ItemScore] = []
    for elem in raw_items:
        if not isinstance(elem, dict):
            logfire.warning(
                "Skipping non-dict LLM response element", element=repr(elem)
            )
            continue
        missing = {"id", "sentiment", "stance", "animosity"} - set(elem)
        if missing:
            logfire.warning(
                "Skipping LLM response element — missing keys",
                missing_keys=sorted(missing),
                element=repr(elem),
            )
            continue
        try:
            item_id = str(elem["id"])
            sentiment = int(elem["sentiment"])
            stance = int(elem["stance"])
            animosity = int(elem["animosity"])
        except (ValueError, TypeError) as exc:
            logfire.warning(
                "Skipping LLM response element — bad types",
                element=repr(elem),
                error=str(exc),
            )
            continue

        if sentiment not in range(1, 11):
            logfire.warning(
                "Skipping item — sentiment out of range",
                item_id=item_id,
                sentiment=sentiment,
            )
            continue
        if stance not in (-1, 0, 1):
            logfire.warning(
                "Skipping item — invalid stance", item_id=item_id, stance=stance
            )
            continue
        if animosity not in range(1, 6):
            logfire.warning(
                "Skipping item — animosity out of range",
                item_id=item_id,
                animosity=animosity,
            )
            continue

        r = stance * (sentiment + alpha * animosity)
        reason = str(elem.get("reason", ""))
        scores.append(
            ItemScore(
                id=item_id,
                sentiment=sentiment,
                stance=stance,
                animosity=animosity,
                r=r,
                reason=reason,
            )
        )
    return scores


def _build_batch_payload(query: str, items: list[NormalizedItem]) -> str:
    payload = {
        "query": query,
        "items": [{"id": item.id, "text": _truncate(item.text)} for item in items],
    }
    return json.dumps(payload, ensure_ascii=True)


def _score_batch(
    query: str,
    batch: list[NormalizedItem],
    model: str | None,
    _override,
    alpha: float = ALPHA_DEFAULT,
) -> list[ItemScore]:
    user_payload = _build_batch_payload(query, batch)
    raw_response = call_llm(
        _SYSTEM_PROMPT,
        user_payload,
        model=model,
        _override=_override,
    )
    try:
        return _validate_item_scores(_extract_json_array(raw_response), alpha=alpha)
    except Exception:
        retry = call_llm(
            _SYSTEM_PROMPT_STRICT,
            user_payload,
            model=model,
            _override=_override,
        )
        return _validate_item_scores(_extract_json_array(retry), alpha=alpha)


def filter_relevant_items(
    query: str,
    items: list[NormalizedItem],
    _override=None,
) -> list[NormalizedItem]:
    """Filter items for relevance to the query using LLM."""
    if not items:
        return []

    relevant_ids: set[str] = set()
    for i in range(0, len(items), _RELEVANCE_BATCH_SIZE):
        batch = items[i : i + _RELEVANCE_BATCH_SIZE]
        payload = _build_batch_payload(query, batch)
        raw_response = call_llm(_RELEVANCE_SYSTEM_PROMPT, payload, _override=_override)
        try:
            parsed = _extract_json_array(raw_response)
        except ValueError:
            # If parsing fails, keep all items in this batch
            relevant_ids.update(item.id for item in batch)
            continue
        for elem in parsed:
            if isinstance(elem, dict) and elem.get("relevant", False):
                relevant_ids.add(str(elem.get("id", "")))

    return [
        replace(item, relevance_score=1.0) for item in items if item.id in relevant_ids
    ]


def assess_items(
    query: str,
    items: list[NormalizedItem],
    model: str | None = None,
    _override=None,
    alpha: float = ALPHA_DEFAULT,
) -> list[ItemScore]:
    """Score each item individually for sentiment, stance, and animosity.

    _override(system_prompt, user_payload) can be injected for tests.
    """
    if not items:
        raise ValueError("Cannot assess items with zero items")

    results: list[ItemScore] = []
    for i in range(0, len(items), _BATCH_SIZE):
        batch = items[i : i + _BATCH_SIZE]
        batch_scores = _score_batch(query, batch, model, _override, alpha=alpha)
        results.extend(batch_scores)

    return results
