from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.internal.pipeline.domain import NormalizedItem, SearchRequest


@runtime_checkable
class SourceAdapter(Protocol):
    name: str  # "reddit" | "gnews" | "youtube"

    def fetch(self, query: str, config: dict) -> list[NormalizedItem]:
        """Fetch items from the source and return them already normalized."""
        ...

    def build_config(self, request: SearchRequest) -> dict:
        """Translate a SearchRequest into source-specific config."""
        ...

    def post_process(
        self,
        items: list[NormalizedItem],
        query: str,
        **kwargs,
    ) -> list[NormalizedItem]:
        """Optional source-specific filtering on the collected item pool.
        Default implementation returns items unchanged.
        Only operates on items belonging to this source: filter
        by item.platform == self.name.
        """
        ...
