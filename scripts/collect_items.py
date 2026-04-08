#!/usr/bin/env python3
"""Collect, normalize, and relevance-filter items for a set of topics.

Runs the real scrapers (Reddit, GNews, YouTube) and saves the resulting
NormalizedItem list (post-relevance-filter, ready for LLM assessment) to
data/items_{slug}.json.

Edit scripts/pipeline_config.json to configure topics and parameters, then run:
    python scripts/collect_items.py
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from src.internal.pipeline.domain import NormalizedItem, SearchRequest
from src.internal.pipeline.llm.assess import filter_relevant_items
from src.internal.pipeline.llm.run import _collect_and_normalize, _select_per_platform

CONFIG_PATH = Path(__file__).parent / "pipeline_config.json"
DATA_DIR = Path(__file__).parents[1] / "data"


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text())["collect"]


def _slug(topic: str) -> str:
    return topic.lower().replace(" ", "_")


def collect_topic(topic: str, request: SearchRequest, apply_filter: bool) -> list[NormalizedItem]:
    print(f"\n[{topic}] Collecting from live scrapers...", flush=True)
    items = _collect_and_normalize(request)
    print(f"[{topic}] Raw items: {len(items)}", flush=True)

    items = _select_per_platform(items)
    print(f"[{topic}] After per-platform cap: {len(items)}", flush=True)

    if apply_filter:
        print(f"[{topic}] Running relevance filter...", flush=True)
        items = filter_relevant_items(topic, items)
        print(f"[{topic}] After relevance filter: {len(items)}", flush=True)
    else:
        print(f"[{topic}] Skipping relevance filter", flush=True)

    return items


def save_items(topic: str, items: list[NormalizedItem]) -> Path:
    DATA_DIR.mkdir(exist_ok=True)
    out_path = DATA_DIR / f"items_{_slug(topic)}.json"
    payload = {"query": topic, "items": [asdict(item) for item in items]}
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"[{topic}] Saved {len(items)} items → {out_path}", flush=True)
    return out_path


def main() -> None:
    cfg = load_config()
    print(f"Config: {cfg}", flush=True)

    for topic in cfg["topics"]:
        request = SearchRequest(
            query=topic,
            time_filter=cfg["time_filter"],
            max_posts=cfg["max_posts"],
            max_comments_per_post=cfg["max_comments_per_post"],
            mode="live",
        )
        try:
            items = collect_topic(topic, request, apply_filter=cfg["relevance_filter"])
            save_items(topic, items)
        except Exception as exc:
            print(f"[{topic}] ERROR: {exc}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
