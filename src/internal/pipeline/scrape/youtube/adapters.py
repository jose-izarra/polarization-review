from __future__ import annotations

from collections import defaultdict

import logfire
from src.internal.pipeline.domain import NormalizedItem, SearchRequest
from src.internal.pipeline.scrape.normalize import normalize_raw_item

from .fetch import collect_youtube_data


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
    from src.internal.pipeline.llm.sources.youtube.calls import determine_video_stances

    video_stances = determine_video_stances(query, items, _override=call_model)
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

    logfire.info(
        "YouTube stance balance complete",
        dropped_count=len(dropped_video_ids),
        distribution=dict(stance_counts),
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
        from src.internal.pipeline.llm.sources.youtube.calls import generate_youtube_queries

        youtube_queries = generate_youtube_queries(query)
        result = collect_youtube_data(query, config=config, queries=youtube_queries)
        raw_items = result.get("data", {}).get("posts", []) + result.get(
            "data", {}
        ).get("comments", [])
        return [normalize_raw_item(r) for r in raw_items]

    def post_process(
        self, items: list[NormalizedItem], query: str, **kwargs
    ) -> list[NormalizedItem]:
        call_model = kwargs.get("call_model")
        return _balance_youtube_by_stance(query, items, call_model=call_model)
