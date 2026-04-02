from __future__ import annotations

import argparse
import json
import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, replace
from datetime import datetime, timezone

from src.internal.pipeline.scrape.youtube.adapters import _determine_video_stances

from .llm_assess import assess_items, filter_relevant_items
from .normalize import dedupe_items, filter_item
from .score import compute_polarization
from src.internal.pipeline.domain import (
    EvidenceItem,
    ItemScore,
    NormalizedItem,
    PolarizationResult,
    SearchRequest,
)

logger = logging.getLogger(__name__)



def _select_per_platform(
    items: list[NormalizedItem], max_per_platform: int = 20
) -> list[NormalizedItem]:
    """Take the top N items per platform by engagement, then combine.

    This prevents high-volume sources (Reddit) from crowding out low-engagement
    sources (GNews) in the pool that reaches the LLM relevance filter.
    """
    by_platform: dict[str, list[NormalizedItem]] = defaultdict(list)
    for item in items:
        by_platform[item.platform].append(item)
    result: list[NormalizedItem] = []
    for platform_items in by_platform.values():
        ranked = sorted(platform_items, key=lambda x: x.engagement_score, reverse=True)
        result.extend(ranked[:max_per_platform])
    return result



def _collect_and_normalize(request: SearchRequest) -> list[NormalizedItem]:
    import src.internal.pipeline.scrape  # noqa — triggers registration
    from src.internal.pipeline.scrape.registry import get_sources

    sources = get_sources()
    all_items: list[NormalizedItem] = []

    with ThreadPoolExecutor(max_workers=len(sources)) as pool:
        futs = {
            pool.submit(adapter.fetch, request.query, adapter.build_config(request)): adapter
            for adapter in sources
        }
        for fut in as_completed(futs):
            adapter = futs[fut]
            try:
                all_items.extend(fut.result())
            except Exception as exc:
                logger.warning("Source %s failed: %s", adapter.name, exc)

    # Source-specific post-processing (balancing, stance pruning, etc.)
    for adapter in sources:
        all_items = adapter.post_process(all_items, request.query)

    kept = [item for item in all_items if filter_item(asdict(item), min_text_length=20)]
    return dedupe_items(kept)


def _build_rationale(
    item_scores: list[ItemScore],
    items: list[NormalizedItem] | None = None,
) -> str:
    n = len(item_scores)
    n_for = sum(1 for s in item_scores if s.stance == 1)
    n_against = sum(1 for s in item_scores if s.stance == -1)
    n_neutral = sum(1 for s in item_scores if s.stance == 0)

    parts = [
        f"{n} items scored. Stance distribution: {n_for} for / "
        f"{n_against} against / {n_neutral} neutral."
    ]

    if items:
        platform_counts: dict[str, int] = defaultdict(int)
        lean_counts: dict[str, int] = defaultdict(int)
        for item in items:
            platform_counts[item.platform] += 1
            if item.source_lean and item.source_lean != "unknown":
                lean_counts[item.source_lean] += 1
        if platform_counts:
            breakdown = ", ".join(
                f"{k}: {v}" for k, v in sorted(platform_counts.items())
            )
            parts.append(f"Platforms: {breakdown}.")
        if lean_counts:
            breakdown = ", ".join(f"{k}: {v}" for k, v in sorted(lean_counts.items()))
            parts.append(f"Source lean: {breakdown}.")

    return " ".join(parts)


def _compute_confidence(n: int) -> float:
    """Linear ramp: 0 -> 1 over 10 items."""
    if n == 0:
        return 0.0
    return round(min(n / 10, 1.0), 4)


def _compute_confidence_label(n: int) -> str:
    if n >= 30:
        return "high"
    if n >= 10:
        return "moderate"
    if n >= 5:
        return "low"
    return "very_low"


def _determine_video_stances(
    query: str,
    items: list[NormalizedItem],
    call_model=None,
) -> dict[str, int]:
    """Send video title+transcript to LLM and get stance per video."""
    from .llm_assess import _get_invoke

    videos = [i for i in items if i.platform == "youtube" and i.content_type == "post"]
    if not videos:
        return {}

    invoke = _get_invoke(call_model, model=None, timeout_seconds=45)

    system_prompt = (
        "For each video, determine its overall stance on the given topic. "
        "Return a JSON array where each element has: id (string), stance (-1/0/1). "
        "Use -1 for against, 0 for neutral, 1 for the topic. "
        "Return only valid JSON."
    )
    payload = {
        "query": query,
        "videos": [{"id": item.id, "title": item.text[:200]} for item in videos],
    }
    raw_response = invoke(system_prompt, json.dumps(payload))

    from .llm_assess import _extract_json_array

    stances: dict[str, int] = {}
    try:
        parsed = _extract_json_array(raw_response)
        for elem in parsed:
            if isinstance(elem, dict) and "id" in elem and "stance" in elem:
                stance = int(elem["stance"])
                if stance in (-1, 0, 1):
                    stances[str(elem["id"])] = stance
    except Exception:
        logger.warning("Failed to parse video stances")
    return stances


def _apply_echo_chamber_dampening(
    item_scores: list[ItemScore],
    items: list[NormalizedItem],
    video_stances: dict[str, int],
) -> list[ItemScore]:
    """Dampen animosity of comments that agree with their parent video's stance."""
    if not video_stances:
        return item_scores

    # Build map: item_id -> parent_video_stance
    item_video_stance: dict[str, int] = {}
    for item in items:
        if item.parent_video_id:
            # Find the NormalizedItem ID for this video
            video_norm_id = f"youtube_video_{item.parent_video_id}"
            if video_norm_id in video_stances:
                item_video_stance[item.id] = video_stances[video_norm_id]

    dampened: list[ItemScore] = []
    for score in item_scores:
        parent_stance = item_video_stance.get(score.id)
        if (
            parent_stance is not None
            and score.stance == parent_stance
            and score.stance != 0
        ):
            new_animosity_f = score.animosity * 0.7
            new_r = score.stance * (score.sentiment + 0.5 * new_animosity_f)
            dampened.append(replace(score, r=new_r))
        else:
            dampened.append(score)
    return dampened


def _build_evidence(
    item_scores: list[ItemScore],
    items: list[NormalizedItem],
) -> list[EvidenceItem]:
    """Build enriched evidence items by joining scores with normalized items."""
    item_map = {i.id: i for i in items}
    evidence: list[EvidenceItem] = []
    for score in item_scores:
        item = item_map.get(score.id)
        if not item:
            continue
        snippet = item.text if len(item.text) <= 240 else f"{item.text[:237]}..."
        evidence.append(
            EvidenceItem(
                id=score.id,
                snippet=snippet,
                url=item.url,
                stance=score.stance,
                animosity=score.animosity,
                sentiment=score.sentiment,
                rationale=score.reason or None,
                source_lean=item.source_lean,
                platform=item.platform,
            )
        )
    return evidence


def run_search(request: SearchRequest) -> PolarizationResult:
    query = request.query.strip()
    if not query:
        raise ValueError("query must not be empty")

    collected_at = datetime.now(tz=timezone.utc).isoformat()

    # Fake mode: skip scraping, use synthetic data
    if request.mode.startswith("fake_"):
        from .fake_data import get_fake_data

        try:
            query, items = get_fake_data(request.mode)
        except KeyError:
            return PolarizationResult(
                query=query,
                collected_at=collected_at,
                sample_size=0,
                polarization_score=None,
                confidence=None,
                rationale=f"Unknown fake mode: {request.mode}",
                evidence=[],
                status="error",
                error_message=f"Unknown mode: {request.mode}",
            )
    else:
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

        # Per-platform cap (post_process balancing already ran inside _collect_and_normalize)
        items = _select_per_platform(items, max_per_platform=20)

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

    # Step 2: Relevance filter
    items = filter_relevant_items(query, items)
    if not items:
        return PolarizationResult(
            query=query,
            collected_at=collected_at,
            sample_size=0,
            polarization_score=None,
            confidence=None,
            rationale="No relevant items found for this query.",
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

    # Step 4: YouTube echo chamber dampening
    video_stances = _determine_video_stances(query, items)
    item_scores = _apply_echo_chamber_dampening(item_scores, items, video_stances)

    # Update parent_video_stance on items
    for i, item in enumerate(items):
        if item.parent_video_id:
            video_norm_id = f"youtube_video_{item.parent_video_id}"
            if video_norm_id in video_stances:
                items[i] = replace(
                    item,
                    parent_video_stance=video_stances[video_norm_id],
                )

    polarization_score = compute_polarization(item_scores)
    n = len(items)
    confidence = _compute_confidence(n)
    confidence_label = _compute_confidence_label(n)
    rationale = _build_rationale(item_scores, items)

    n_for = sum(1 for s in item_scores if s.stance == 1)
    n_against = sum(1 for s in item_scores if s.stance == -1)
    n_neutral = sum(1 for s in item_scores if s.stance == 0)
    platform_counts: dict[str, int] = defaultdict(int)
    for item in items:
        platform_counts[item.platform] += 1

    evidence_items = _build_evidence(item_scores, items)
    if not evidence_items:
        evidence_items = [
            EvidenceItem(
                id=item.id,
                snippet=item.text if len(item.text) <= 240 else f"{item.text[:237]}...",
                url=item.url,
                platform=item.platform,
            )
            for item in items[:3]
        ]

    return PolarizationResult(
        query=query,
        collected_at=collected_at,
        sample_size=n,
        polarization_score=polarization_score,
        confidence=confidence,
        rationale=rationale,
        evidence=evidence_items,
        status="ok",
        error_message=None,
        confidence_label=confidence_label,
        stance_distribution={"for": n_for, "against": n_against, "neutral": n_neutral},
        source_breakdown=dict(platform_counts),
    )


def _parse_args() -> SearchRequest:
    parser = argparse.ArgumentParser(description="Run minimal polarization pipeline")
    parser.add_argument("query", type=str, help="Search term/topic")
    parser.add_argument(
        "--time-filter", choices=["day", "week", "month"], default="month"
    )
    parser.add_argument("--max-posts", type=int, default=30)
    parser.add_argument("--max-comments-per-post", type=int, default=10)
    parser.add_argument(
        "--mode",
        choices=[
            "live",
            "fake_polarized",
            "fake_moderate",
            "fake_neutral",
        ],
        default="live",
    )
    args = parser.parse_args()

    return SearchRequest(
        query=args.query,
        time_filter=args.time_filter,
        max_posts=args.max_posts,
        max_comments_per_post=args.max_comments_per_post,
        mode=args.mode,
    )


def main() -> None:
    request = _parse_args()
    result = run_search(request)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
