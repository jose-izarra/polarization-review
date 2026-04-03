from __future__ import annotations

from src.internal.pipeline.llm.sources.base import LLMSourceProcessor

_processors: list[LLMSourceProcessor] = []


def register(processor: LLMSourceProcessor) -> None:
    _processors.append(processor)


def get_processors() -> list[LLMSourceProcessor]:
    return list(_processors)
