from __future__ import annotations

from typing import Protocol

from src.internal.pipeline.domain import ItemScore, NormalizedItem


class LLMSourceProcessor(Protocol):
    """Post-assessment processor for a specific data source.

    Each source that needs LLM-based post-processing (e.g. YouTube echo
    chamber dampening) implements this protocol and registers itself.
    Sources with no post-assessment step can skip registration entirely.
    """

    name: str

    def post_assess(
        self,
        query: str,
        items: list[NormalizedItem],
        scores: list[ItemScore],
        call_model=None,
    ) -> list[ItemScore]:
        """Apply source-specific adjustments after the main LLM assessment pass."""
        ...
