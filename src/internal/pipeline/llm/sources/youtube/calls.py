from __future__ import annotations

import json
from dataclasses import replace

import logfire

from src.internal.pipeline.domain import ItemScore, NormalizedItem
from src.internal.pipeline.llm.assess import _extract_json_array
from src.internal.pipeline.llm.client import call_llm
from src.internal.pipeline.llm.sources.youtube.prompts import (
    QUERY_GENERATION_PROMPT,
    VIDEO_STANCE_PROMPT,
)


def generate_youtube_queries(query: str, _override=None) -> list[str]:
    """Use LLM to generate 3 YouTube search queries covering opposing perspectives.
    Falls back to [query] on any failure.
    """
    try:
        raw = call_llm(
            QUERY_GENERATION_PROMPT,
            json.dumps({"query": query}),
            timeout_seconds=30,
            _override=_override,
        )
        parsed = _extract_json_array(raw)
        queries = [str(q).strip() for q in parsed if isinstance(q, str) and str(q).strip()]
        if len(queries) >= 2:
            return queries[:3]
    except Exception:
        logfire.warning("Failed to generate YouTube queries, falling back", query=query)
    return [query]


def determine_video_stances(
    query: str,
    items: list[NormalizedItem],
    _override=None,
) -> dict[str, int]:
    """Send video titles to LLM and return a stance dict keyed by item id."""
    videos = [i for i in items if i.platform == "youtube" and i.content_type == "post"]
    if not videos:
        return {}

    payload = {
        "query": query,
        "videos": [{"id": item.id, "title": item.text[:200]} for item in videos],
    }
    raw_response = call_llm(
        VIDEO_STANCE_PROMPT,
        json.dumps(payload),
        timeout_seconds=45,
        _override=_override,
    )
    stances: dict[str, int] = {}
    try:
        parsed = _extract_json_array(raw_response)
        for elem in parsed:
            if isinstance(elem, dict) and "id" in elem and "stance" in elem:
                stance = int(elem["stance"])
                if stance in (-1, 0, 1):
                    stances[str(elem["id"])] = stance
    except Exception:
        logfire.warning("Failed to parse video stances")
    return stances


def apply_echo_chamber_dampening(
    item_scores: list[ItemScore],
    items: list[NormalizedItem],
    video_stances: dict[str, int],
) -> list[ItemScore]:
    """Reduce animosity of YouTube comments that agree with their parent video's stance."""
    if not video_stances:
        return item_scores

    item_video_stance: dict[str, int] = {}
    for item in items:
        if item.parent_video_id:
            video_norm_id = f"youtube_video_{item.parent_video_id}"
            if video_norm_id in video_stances:
                item_video_stance[item.id] = video_stances[video_norm_id]

    dampened: list[ItemScore] = []
    for score in item_scores:
        parent_stance = item_video_stance.get(score.id)
        if (
            parent_stance is not None
            and score.stance == parent_stance
            and score.stance != 0
        ):
            new_animosity_f = score.animosity * 0.7
            new_r = score.stance * (score.sentiment + 0.5 * new_animosity_f)
            dampened.append(replace(score, r=new_r))
        else:
            dampened.append(score)
    return dampened


class YouTubeLLMProcessor:
    name = "youtube"

    def post_assess(
        self,
        query: str,
        items: list[NormalizedItem],
        scores: list[ItemScore],
        call_model=None,
    ) -> list[ItemScore]:
        video_stances = determine_video_stances(query, items, _override=call_model)
        return apply_echo_chamber_dampening(scores, items, video_stances)
