from __future__ import annotations

from src.internal.pipeline.domain import NormalizedItem, SearchRequest
from src.internal.pipeline.scrape.normalize import normalize_raw_item

from .fetch import collect_reddit_data


class RedditAdapter:
    name = "reddit"

    def build_config(self, request: SearchRequest) -> dict:
        return {
            "subreddit_discovery_limit": 10,
            "min_subscribers": 10_000,
            "phase2_top_n": 5,
            "sorts": ["relevance"],
            "time_filter": request.time_filter,
            "posts_per_subreddit_all": request.max_posts,
            "top_posts_for_comments": min(10, request.max_posts),
            "comments_per_post": request.max_comments_per_post,
            "min_text_length": 20,
        }

    def fetch(self, query: str, config: dict, _client=None) -> list[NormalizedItem]:
        result = collect_reddit_data(query, scrape_config=config, reddit=_client)
        raw_items = result.get("data", {}).get("posts", []) + result.get(
            "data", {}
        ).get("comments", [])
        return [normalize_raw_item(r) for r in raw_items]

    def post_process(
        self, items: list[NormalizedItem], _query: str, **kwargs
    ) -> list[NormalizedItem]:
        return items  # Reddit has no source-specific balancing
