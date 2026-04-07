#!/usr/bin/env python3
"""Run the assessment pipeline on previously collected items.

Loads a NormalizedItem JSON file saved by collect_items.py and runs
assess → post-process → score, returning a PolarizationResult.
saves a summary of the assessment in the data/results directory.

Edit scripts/pipeline_config.json to configure alpha and model, then run:
    python scripts/assess_from_file.py data/items/items_inflation.json
    python scripts/assess_from_file.py data/items/items_gun_control.json
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import src.internal.pipeline.llm.sources  # noqa — triggers processor registration
from src.internal.pipeline.domain import (
    EvidenceItem,
    ItemScore,
    NormalizedItem,
    PolarizationResult,
)
from src.internal.pipeline.llm.assess import assess_items
from src.internal.pipeline.llm.score import compute_polarization
from src.internal.pipeline.llm.sources.registry import get_processors

CONFIG_PATH = Path(__file__).parent / "pipeline_config.json"
RESULTS_DIR = Path(__file__).parents[1] / "data" / "results"


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text())["assess"]


def load_items(path: Path) -> tuple[str, list[NormalizedItem]]:
    data = json.loads(path.read_text())
    query = data["query"]
    items = [NormalizedItem(**item) for item in data["items"]]
    return query, items


def _build_evidence(item_scores: list[ItemScore], items: list[NormalizedItem]) -> list[EvidenceItem]:
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


def run_assessment(query: str, items: list[NormalizedItem], alpha: float, model: str | None) -> PolarizationResult:
    collected_at = datetime.now(tz=timezone.utc).isoformat()

    print(f"Assessing {len(items)} items (alpha={alpha}, model={model or 'default'})...", flush=True)
    item_scores = assess_items(query, items, model=model, alpha=alpha)
    print(f"Scored {len(item_scores)} items", flush=True)

    for processor in get_processors():
        item_scores = processor.post_assess(query, items, item_scores)

    polarization_score = compute_polarization(item_scores)

    n = len(item_scores)
    n_for = sum(1 for s in item_scores if s.stance == 1)
    n_against = sum(1 for s in item_scores if s.stance == -1)
    n_neutral = sum(1 for s in item_scores if s.stance == 0)
    avg_animosity = sum(s.animosity for s in item_scores) / n if n else 0.0
    avg_sentiment = sum(s.sentiment for s in item_scores) / n if n else 0.0

    platform_counts: dict[str, int] = defaultdict(int)
    for item in items:
        platform_counts[item.platform] += 1

    rationale = (
        f"{n} items scored. Stance distribution: {n_for} for / "
        f"{n_against} against / {n_neutral} neutral. "
        f"Avg animosity: {avg_animosity:.2f}. Avg sentiment: {avg_sentiment:.2f}. "
        f"Platforms: {', '.join(f'{k}: {v}' for k, v in sorted(platform_counts.items()))}."
    )

    return PolarizationResult(
        query=query,
        collected_at=collected_at,
        sample_size=n,
        polarization_score=polarization_score,
        rationale=rationale,
        evidence=_build_evidence(item_scores, items),
        status="ok",
        error_message=None,
        stance_distribution={"for": n_for, "against": n_against, "neutral": n_neutral},
        source_breakdown=dict(platform_counts),
    )


def _next_run_number(slug: str) -> int:
    existing = list(RESULTS_DIR.glob(f"{slug}_run*.txt"))
    if not existing:
        return 1
    nums = []
    for p in existing:
        try:
            nums.append(int(p.stem.rsplit("run", 1)[-1]))
        except ValueError:
            pass
    return max(nums, default=0) + 1


def save_summary(file_path: Path, result: PolarizationResult, full_config: dict) -> Path:
    slug = file_path.stem.removeprefix("items_")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    run_num = _next_run_number(slug)
    out_path = RESULTS_DIR / f"{slug}_run{run_num}.txt"

    stance_map = {1: "FOR", 0: "NEUTRAL", -1: "AGAINST"}

    lines: list[str] = [
        "=" * 60,
        f"POLARIZATION ASSESSMENT — Run #{run_num}",
        "=" * 60,
        f"Topic          : {result.query}",
        f"Assessed at    : {result.collected_at}",
        f"Model          : {full_config['assess'].get('model') or 'default'}",
        f"Alpha          : {full_config['assess'].get('alpha')}",
        "",
        "--- Score ---",
        f"Polarization   : {result.polarization_score:.2f} / 100" if result.polarization_score is not None else "Polarization   : N/A",
        f"Sample size    : {result.sample_size}",
        f"Rationale      : {result.rationale}",
        "",
        "--- Stance Distribution ---",
    ]

    if result.stance_distribution:
        for key, count in result.stance_distribution.items():
            lines.append(f"  {key.capitalize():<10}: {count}")

    evidence_count = len(result.evidence)
    avg_sentiment = (
        sum(ev.sentiment for ev in result.evidence) / evidence_count if evidence_count else 0.0
    )
    avg_animosity = (
        sum(ev.animosity for ev in result.evidence) / evidence_count if evidence_count else 0.0
    )
    lines += [
        "",
        "--- Item Averages ---",
        f"  Sentiment   : {avg_sentiment:.2f}",
        f"  Animosity   : {avg_animosity:.2f}",
    ]

    lines += ["", "--- Source Breakdown ---"]
    if result.source_breakdown:
        for platform, count in sorted(result.source_breakdown.items()):
            lines.append(f"  {platform:<12}: {count}")

    lines += ["", "--- Config ---"]
    lines.append(json.dumps(full_config, indent=2))

    lines += ["", "--- Evidence Items ---"]
    for i, ev in enumerate(result.evidence, 1):
        stance_label = stance_map.get(ev.stance, str(ev.stance))
        lines += [
            "",
            f"[{i}] {ev.platform or 'unknown'} | {ev.source_lean or 'unknown lean'} | Stance: {stance_label} | Sentiment: {ev.sentiment} | Animosity: {ev.animosity}",
            f"    URL      : {ev.url}",
            f"    Rationale: {ev.rationale or '—'}",
            f"    Snippet  : {ev.snippet}",
        ]

    lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/assess_from_file.py <path/to/items/<items_*.json>>", file=sys.stderr)
        sys.exit(1)

    full_config = json.loads(CONFIG_PATH.read_text())
    cfg = full_config["assess"]
    alpha: float = cfg["alpha"]
    model: str | None = cfg["model"]

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"Error: file not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    query, items = load_items(file_path)
    print(f"Loaded {len(items)} items for query: '{query}'", flush=True)
    print(f"Config: alpha={alpha}, model={model or 'default'}", flush=True)

    result = run_assessment(query, items, alpha=alpha, model=model)

    out_path = save_summary(file_path, result, full_config)
    print(f"\nSummary saved → {out_path}", flush=True)

    print("\n--- Summary ---")
    print(f"  Topic              : {result.query}")
    print(f"  Polarization score : {result.polarization_score:.2f}" if result.polarization_score is not None else "  Polarization score : N/A")
    print(f"  Sample size        : {result.sample_size}")
    print(f"  Stance distribution: {result.stance_distribution}")
    if result.evidence:
        avg_sentiment = sum(ev.sentiment for ev in result.evidence) / len(result.evidence)
        avg_animosity = sum(ev.animosity for ev in result.evidence) / len(result.evidence)
        print(f"  Avg sentiment      : {avg_sentiment:.2f}")
        print(f"  Avg animosity      : {avg_animosity:.2f}")
    print(f"  Source breakdown   : {result.source_breakdown}")


if __name__ == "__main__":
    main()
