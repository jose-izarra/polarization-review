from __future__ import annotations

import json
import logging
import re
from dataclasses import replace

from src.internal.config.config import config

from .types import ItemScore, NormalizedItem

_DEFAULT_MODEL = "gemini-2.5-flash"
_BATCH_SIZE = 15
_RELEVANCE_BATCH_SIZE = 25
_JSON_ARRAY_RE = re.compile(r"\[.*\]", re.DOTALL)
_ALPHA = 0.5

logger = logging.getLogger(__name__)


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


def _validate_item_scores(raw_items: list, alpha: float = _ALPHA) -> list[ItemScore]:
    scores: list[ItemScore] = []
    for elem in raw_items:
        if not isinstance(elem, dict):
            logger.warning("Skipping non-dict element: %r", elem)
            continue
        missing = {"id", "sentiment", "stance", "animosity"} - set(elem)
        if missing:
            logger.warning(
                "Skipping element missing keys %s: %r", sorted(missing), elem
            )
            continue
        try:
            item_id = str(elem["id"])
            sentiment = int(elem["sentiment"])
            stance = int(elem["stance"])
            animosity = int(elem["animosity"])
        except (ValueError, TypeError) as exc:
            logger.warning("Skipping element with bad types: %r (%s)", elem, exc)
            continue

        if sentiment not in range(1, 6):
            logger.warning(
                "Skipping item %r: sentiment %d out of range 1-5", item_id, sentiment
            )
            continue
        if stance not in (-1, 0, 1):
            logger.warning(
                "Skipping item %r: stance %d not in {-1, 0, 1}", item_id, stance
            )
            continue
        if animosity not in range(1, 6):
            logger.warning(
                "Skipping item %r: animosity %d out of range 1-5", item_id, animosity
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


def _call_gemini_chat(
    system_prompt: str, user_payload: str, model: str, timeout_seconds: int
) -> str:
    from google import genai
    from google.genai import types

    if not config.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is required for LLM assessment")

    client = genai.Client(api_key=config.gemini_api_key)

    try:
        response = client.models.generate_content(
            model=model,
            contents=user_payload,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.0,
                response_mime_type="application/json",
            ),
        )
    except Exception as exc:
        raise RuntimeError(f"Gemini API error: {exc}") from exc

    return response.text


_SYSTEM_PROMPT = (
    "Rate each item for the given topic. Return a JSON array where each element has: "
    "id (string), sentiment (1-5), stance (-1/0/1), animosity (1-5), "
    "reason (string, 1-sentence explanation of your rating). "
    "Use only the provided text. Return only valid JSON, no extra text."
)
_SYSTEM_PROMPT_STRICT = (
    _SYSTEM_PROMPT + " Return only a valid JSON array and absolutely nothing else."
)

_RELEVANCE_SYSTEM_PROMPT = (
    "Determine whether each item is relevant to the given topic/query. "
    'Return a JSON array where each element has: id (string), relevant (boolean). '
    "An item is relevant if it directly discusses, argues about, or provides "
    "an opinion on the topic. Off-topic or tangential items should be marked false. "
    "Return only valid JSON, no extra text."
)


def _score_batch(
    query: str,
    batch: list[NormalizedItem],
    invoke,
    alpha: float = _ALPHA,
) -> list[ItemScore]:
    user_payload = _build_batch_payload(query, batch)
    raw_response = invoke(_SYSTEM_PROMPT, user_payload)
    try:
        raw_items = _extract_json_array(raw_response)
        return _validate_item_scores(raw_items, alpha=alpha)
    except Exception:
        retry_response = invoke(_SYSTEM_PROMPT_STRICT, user_payload)
        raw_items = _extract_json_array(retry_response)
        return _validate_item_scores(raw_items, alpha=alpha)


def _get_invoke(call_model, model: str | None, timeout_seconds: int):
    """Build the invoke callable from call_model or config."""
    if call_model is not None:
        return call_model

    if config.gemini_api_key is None:
        from .mock_llm import mock_call_model

        return mock_call_model

    chosen_model = model or config.polarization_model

    def invoke(sys_prompt, user_input):
        return _call_gemini_chat(
            sys_prompt,
            user_input,
            model=chosen_model,
            timeout_seconds=timeout_seconds,
        )

    return invoke


_YOUTUBE_QUERY_SYSTEM_PROMPT = (
    "Given a search query or claim, generate exactly 3 YouTube search queries to "
    "surface videos covering different perspectives on the topic: "
    "1) a query finding videos that support or argue for the claim, "
    "2) a query finding videos that oppose, criticise, or debunk the claim, "
    "3) a neutral debate or analysis framing of the same topic. "
    "Return a JSON array of exactly 3 short search strings. Return only valid JSON."
)


def generate_youtube_queries(query: str, call_model=None) -> list[str]:
    """Use LLM to generate 3 YouTube search queries covering opposing perspectives.

    Falls back to [query] on any failure so the pipeline is never blocked.
    """
    invoke = _get_invoke(call_model, model=None, timeout_seconds=30)
    try:
        raw = invoke(_YOUTUBE_QUERY_SYSTEM_PROMPT, json.dumps({"query": query}))
        parsed = _extract_json_array(raw)
        queries = [str(q).strip() for q in parsed if isinstance(q, str) and str(q).strip()]
        if len(queries) >= 2:
            return queries[:3]
    except Exception:
        logger.warning(
            "Failed to generate YouTube queries for %r, falling back to original", query
        )
    return [query]


def filter_relevant_items(
    query: str,
    items: list[NormalizedItem],
    call_model=None,
) -> list[NormalizedItem]:
    """Filter items for relevance to the query using LLM."""
    if not items:
        return []

    invoke = _get_invoke(call_model, model=None, timeout_seconds=45)

    relevant_ids: set[str] = set()
    for i in range(0, len(items), _RELEVANCE_BATCH_SIZE):
        batch = items[i : i + _RELEVANCE_BATCH_SIZE]
        payload = _build_batch_payload(query, batch)
        raw_response = invoke(_RELEVANCE_SYSTEM_PROMPT, payload)
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
        replace(item, relevance_score=1.0)
        for item in items
        if item.id in relevant_ids
    ]


def assess_items(
    query: str,
    items: list[NormalizedItem],
    model: str | None = None,
    timeout_seconds: int = 45,
    call_model=None,
    alpha: float = _ALPHA,
) -> list[ItemScore]:
    """Score each item individually for sentiment, stance, and animosity.

    call_model(system_prompt, user_payload) can be injected for tests.
    """
    if not items:
        raise ValueError("Cannot assess items with zero items")

    invoke = _get_invoke(call_model, model, timeout_seconds)

    results: list[ItemScore] = []
    for i in range(0, len(items), _BATCH_SIZE):
        batch = items[i : i + _BATCH_SIZE]
        batch_scores = _score_batch(query, batch, invoke, alpha=alpha)
        results.extend(batch_scores)

    return results
