from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime, timezone

from src.pipeline.llm_assess import assess_polarization
from src.pipeline.normalize import dedupe_items, filter_item, normalize_raw_item, select_top_items
from src.pipeline.types import EvidenceItem, PolarizationResult, SearchRequest


_MIN_SAMPLE_FOR_FULL_CONFIDENCE = 10
_LOW_SAMPLE_CONFIDENCE_CAP = 0.4


def _build_scrape_config(request: SearchRequest) -> dict:
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
    from src.scrape.reddit import collect_reddit_data

    cfg = _build_scrape_config(request)
    raw = collect_reddit_data(request.query, config=cfg)
    posts = raw.get("data", {}).get("posts", [])
    comments = raw.get("data", {}).get("comments", [])

    candidates = [normalize_raw_item(item) for item in [*posts, *comments]]
    kept = [item for item in candidates if filter_item(asdict(item), min_text_length=20)]
    deduped = dedupe_items(kept)
    return select_top_items(deduped, max_items=40)


def _evidence_from_ids(items_by_id: dict, evidence_ids: list[str]) -> list[EvidenceItem]:
    evidence: list[EvidenceItem] = []
    for evidence_id in evidence_ids:
        item = items_by_id.get(evidence_id)
        if not item:
            continue
        snippet = item.text if len(item.text) <= 240 else f"{item.text[:237]}..."
        evidence.append(EvidenceItem(id=item.id, snippet=snippet, url=item.url))
    return evidence


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
            rationale="Failed while collecting Reddit data.",
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
            rationale="Insufficient Reddit data for this query.",
            evidence=[],
            status="degraded",
            error_message=None,
        )

    try:
        assessment = assess_polarization(query, items)
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
            rationale="LLM assessment unavailable; collected evidence is returned for inspection.",
            evidence=evidence,
            status="degraded",
            error_message=str(exc),
        )

    confidence = assessment.confidence
    if len(items) < _MIN_SAMPLE_FOR_FULL_CONFIDENCE:
        confidence = min(confidence, _LOW_SAMPLE_CONFIDENCE_CAP)

    items_by_id = {item.id: item for item in items}
    evidence = _evidence_from_ids(items_by_id, assessment.evidence_ids)
    if not evidence:
        evidence = _evidence_from_ids(items_by_id, [item.id for item in items[:3]])

    return PolarizationResult(
        query=query,
        collected_at=collected_at,
        sample_size=len(items),
        polarization_score=assessment.polarization_score,
        confidence=confidence,
        rationale=assessment.rationale,
        evidence=evidence,
        status="ok",
        error_message=None,
    )


def _parse_args() -> SearchRequest:
    parser = argparse.ArgumentParser(description="Run minimal polarization pipeline")
    parser.add_argument("query", type=str, help="Search term/topic")
    parser.add_argument("--time-filter", choices=["day", "week", "month"], default="week")
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
