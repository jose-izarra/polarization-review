from __future__ import annotations

from .base import SourceAdapter

_registry: dict[str, SourceAdapter] = {}


def register_source(name: str, adapter: SourceAdapter) -> None:
    _registry[name] = adapter


def get_sources() -> list[SourceAdapter]:
    return list(_registry.values())
