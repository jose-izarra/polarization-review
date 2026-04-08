from __future__ import annotations

from collections import defaultdict

from src.internal.pipeline.domain import NormalizedItem, SearchRequest
from src.internal.pipeline.scrape.normalize import normalize_raw_item

from .fetch import collect_gnews_data

_MAX_PER_LEAN = 2

class GNewsAdapter:
    name = "gnews"

    def build_config(self, request: SearchRequest) -> dict:
        return {"time_filter": request.time_filter}

    def fetch(self, query: str, config: dict) -> list[NormalizedItem]:
        result = collect_gnews_data(query, config["time_filter"])
        raw_items = result.get("data", {}).get("posts", [])
        return [normalize_raw_item(r) for r in raw_items]

    def post_process(
        self, items: list[NormalizedItem], query: str, **kwargs
    ) -> list[NormalizedItem]:
        """Cap GNews items per source lean category to prevent bias."""
        lean_counts: dict[str, int] = defaultdict(int)
        result: list[NormalizedItem] = []
        for item in items:
            if item.platform == "gnews" and item.source_lean:
                lean = item.source_lean
                if lean_counts[lean] >= _MAX_PER_LEAN:
                    continue
                lean_counts[lean] += 1
            result.append(item)
        return result
