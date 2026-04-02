from __future__ import annotations

import json
import logging
from collections import defaultdict

from src.internal.pipeline.domain import NormalizedItem, SearchRequest
from src.internal.pipeline.scrape.normalize import normalize_raw_item

from .fetch import collect_youtube_data

logger = logging.getLogger(__name__)


def _determine_video_stances(
    query: str,
    items: list[NormalizedItem],
    call_model=None,
) -> dict[str, int]:
    """Send video title+transcript to LLM and get stance per video."""
    from src.internal.pipeline.llm.llm_assess import _get_invoke

    videos = [i for i in items if i.platform == "youtube" and i.content_type == "post"]
    if not videos:
        return {}

    invoke = _get_invoke(call_model, model=None, timeout_seconds=45)

    system_prompt = (
        "For each video, determine its overall stance on the given topic. "
        "Return a JSON array where each element has: id (string), stance (-1/0/1). "
        "Use -1 for against, 0 for neutral, 1 for the topic. "
        "Return only valid JSON."
    )
    payload = {
        "query": query,
        "videos": [{"id": item.id, "title": item.text[:200]} for item in videos],
    }
    raw_response = invoke(system_prompt, json.dumps(payload))

    from src.internal.pipeline.llm.llm_assess import _extract_json_array

    stances: dict[str, int] = {}
    try:
        parsed = _extract_json_array(raw_response)
        for elem in parsed:
            if isinstance(elem, dict) and "id" in elem and "stance" in elem:
                stance = int(elem["stance"])
                if stance in (-1, 0, 1):
                    stances[str(elem["id"])] = stance
    except Exception:
        logger.warning("Failed to parse video stances")
    return stances


def _balance_youtube_by_stance(
    query: str,
    items: list[NormalizedItem],
    max_per_stance: int = 4,
    call_model=None,
) -> list[NormalizedItem]:
    """Cap YouTube video posts to at most *max_per_stance* per stance category.

    Assesses the stance of each YouTube video post via LLM, then drops excess
    same-stance videos together with all comments belonging to those videos.
    Non-YouTube items are always kept unchanged.
    """
    video_stances = _determine_video_stances(query, items, call_model=call_model)
    if not video_stances:
        return items

    stance_counts: dict[int, int] = defaultdict(int)
    dropped_video_ids: set[str] = set()

    for item in items:
        if item.platform != "youtube" or item.content_type != "post":
            continue
        stance = video_stances.get(item.id)
        if stance is None:
            continue  # Unassessed — keep
        if stance_counts[stance] < max_per_stance:
            stance_counts[stance] += 1
        else:
            dropped_video_ids.add(item.id)

    if not dropped_video_ids:
        return items

    logger.info(
        "YouTube stance balance: dropped %d over-represented video(s), "
        "kept distribution %s",
        len(dropped_video_ids),
        dict(stance_counts),
    )

    result: list[NormalizedItem] = []
    for item in items:
        if item.platform != "youtube":
            result.append(item)
        elif item.content_type == "post":
            if item.id not in dropped_video_ids:
                result.append(item)
        else:
            # Comment: keep only if its parent video was not dropped
            parent_norm_id = f"youtube_video_{item.parent_video_id}"
            if parent_norm_id not in dropped_video_ids:
                result.append(item)
    return result


class YouTubeAdapter:
    name = "youtube"

    def build_config(self, request: SearchRequest) -> dict:
        return {
            "max_videos": 10,
            "max_comments_per_video": max(request.max_comments_per_post, 30),
        }

    def fetch(self, query: str, config: dict) -> list[NormalizedItem]:
        from src.internal.pipeline.llm.llm_assess import generate_youtube_queries

        youtube_queries = generate_youtube_queries(query)
        result = collect_youtube_data(query, config=config, queries=youtube_queries)
        raw_items = result.get("data", {}).get("posts", []) + result.get("data", {}).get("comments", [])
        return [normalize_raw_item(r) for r in raw_items]

    def post_process(self, items: list[NormalizedItem], query: str, **kwargs) -> list[NormalizedItem]:
        call_model = kwargs.get("call_model")
        return _balance_youtube_by_stance(query, items, call_model=call_model)
