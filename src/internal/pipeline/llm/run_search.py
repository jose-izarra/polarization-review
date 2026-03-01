from __future__ import annotations

import argparse
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime, timezone

from .llm_assess import assess_items
from .normalize import dedupe_items, filter_item, normalize_raw_item, select_top_items
from .score import compute_polarization
from .types import EvidenceItem, ItemScore, PolarizationResult, SearchRequest

_MIN_SAMPLE_FOR_FULL_CONFIDENCE = 10
_LOW_SAMPLE_CONFIDENCE_CAP = 0.4

logger = logging.getLogger(__name__)


def _build_reddit_config(request: SearchRequest) -> dict:
    return {
        "subreddits": ["all"],
        "sorts": ["relevance"],
        "time_filter": request.time_filter,
        "posts_per_subreddit_all": request.max_posts,
        "top_posts_for_comments": min(10, request.max_posts),
        "comments_per_post": request.max_comments_per_post,
        "min_text_length": 20,
    }


def _collect_and_normalize(request: SearchRequest) -> list:
    from src.internal.pipeline.scrape.gnews import collect_gnews_data
    from src.internal.pipeline.scrape.reddit import collect_reddit_data
    from src.internal.pipeline.scrape.youtube import collect_youtube_data

    tasks = {
        "reddit": lambda: collect_reddit_data(
            request.query, scrape_config=_build_reddit_config(request)
        ),
        "youtube": lambda: collect_youtube_data(
            request.query,
            config={
                "max_videos": 10,
                "max_comments_per_video": request.max_comments_per_post,
            },
        ),
        "gnews": lambda: collect_gnews_data(
            request.query,
            request.time_filter,
            config={"max_articles": request.max_posts},
        ),
    }

    all_raw: list[dict] = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futs = {pool.submit(fn): name for name, fn in tasks.items()}
        for fut in as_completed(futs):
            name = futs[fut]
            try:
                result = fut.result()
                all_raw.extend(result.get("data", {}).get("posts", []))
                all_raw.extend(result.get("data", {}).get("comments", []))
            except Exception as exc:
                logger.warning("Source %s failed: %s", name, exc)

    candidates = [normalize_raw_item(item) for item in all_raw]
    kept = [
        item for item in candidates if filter_item(asdict(item), min_text_length=20)
    ]
    deduped = dedupe_items(kept)
    return select_top_items(deduped, max_items=40)


def _build_rationale(item_scores: list[ItemScore]) -> str:
    n = len(item_scores)
    n_for = sum(1 for s in item_scores if s.stance == 1)
    n_against = sum(1 for s in item_scores if s.stance == -1)
    n_neutral = sum(1 for s in item_scores if s.stance == 0)
    return (
        f"{n} items scored. Score distribution: {n_for} for / "
        f"{n_against} against / {n_neutral} neutral."
    )


def _compute_confidence(items: list, item_scores: list[ItemScore]) -> float:
    n = len(items)
    if n == 0:
        return 0.0
    base = 1.0 if n >= _MIN_SAMPLE_FOR_FULL_CONFIDENCE else _LOW_SAMPLE_CONFIDENCE_CAP
    opinionated = sum(1 for s in item_scores if s.stance != 0)
    opinion_ratio = opinionated / max(len(item_scores), 1)
    return round(base * opinion_ratio, 4)


def run_search(request: SearchRequest) -> PolarizationResult:
    query = request.query.strip()
    if not query:
        raise ValueError("query must not be empty")

    collected_at = datetime.now(tz=timezone.utc).isoformat()

    try:
        items = _collect_and_normalize(request)
    except Exception as exc:
        return PolarizationResult(
            query=query,
            collected_at=collected_at,
            sample_size=0,
            polarization_score=None,
            confidence=None,
            rationale="Failed while collecting data.",
            evidence=[],
            status="error",
            error_message=str(exc),
        )

    if not items:
        return PolarizationResult(
            query=query,
            collected_at=collected_at,
            sample_size=0,
            polarization_score=None,
            confidence=None,
            rationale="Insufficient data for this query.",
            evidence=[],
            status="degraded",
            error_message=None,
        )

    try:
        item_scores = assess_items(query, items)
    except Exception as exc:
        fallback = items[:3]
        evidence = [
            EvidenceItem(
                id=item.id,
                snippet=item.text if len(item.text) <= 240 else f"{item.text[:237]}...",
                url=item.url,
            )
            for item in fallback
        ]

        return PolarizationResult(
            query=query,
            collected_at=collected_at,
            sample_size=len(items),
            polarization_score=None,
            confidence=None,
            rationale=(
                "LLM assessment unavailable; collected evidence is returned "
                "for inspection."
            ),
            evidence=evidence,
            status="degraded",
            error_message=str(exc),
        )

    polarization_score = compute_polarization(item_scores)
    confidence = _compute_confidence(items, item_scores)
    rationale = _build_rationale(item_scores)

    scored_ids = {s.id for s in item_scores}
    evidence_items = [
        EvidenceItem(
            id=item.id,
            snippet=item.text if len(item.text) <= 240 else f"{item.text[:237]}...",
            url=item.url,
        )
        for item in items
        if item.id in scored_ids
    ][:5]
    if not evidence_items:
        evidence_items = [
            EvidenceItem(
                id=item.id,
                snippet=item.text if len(item.text) <= 240 else f"{item.text[:237]}...",
                url=item.url,
            )
            for item in items[:3]
        ]

    return PolarizationResult(
        query=query,
        collected_at=collected_at,
        sample_size=len(items),
        polarization_score=polarization_score,
        confidence=confidence,
        rationale=rationale,
        evidence=evidence_items,
        status="ok",
        error_message=None,
    )


def _parse_args() -> SearchRequest:
    parser = argparse.ArgumentParser(description="Run minimal polarization pipeline")
    parser.add_argument("query", type=str, help="Search term/topic")
    parser.add_argument(
        "--time-filter", choices=["day", "week", "month"], default="week"
    )
    parser.add_argument("--max-posts", type=int, default=30)
    parser.add_argument("--max-comments-per-post", type=int, default=10)
    args = parser.parse_args()

    return SearchRequest(
        query=args.query,
        time_filter=args.time_filter,
        max_posts=args.max_posts,
        max_comments_per_post=args.max_comments_per_post,
    )


def main() -> None:
    request = _parse_args()
    result = run_search(request)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
