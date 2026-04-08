"""Platform cap ablation study: effect of max items per platform on polarization score.

Collects items once from all configured sources, then applies different
max_per_platform caps before running the LLM relevance filter, assessment,
and scoring pipeline. Collection is shared across all cap values so that
differences in score are attributable solely to the cap, not to scraping variance.

All configuration is read from a JSON file (default: config.json next to this script).

Usage:
    python studies/platform_cap/run.py
    python studies/platform_cap/run.py --config path/to/config.json

Config file fields:
    description            (str)        Human-readable label printed in the output file.
    runs                   (int)        How many times to repeat each cap value.
                                        LLM assessment is stochastic, so >1 run recommended.
    query                  (str)        Topic/query to analyze.
    time_filter            (str)        "day" | "week" | "month" (default: "month").
    max_posts              (int)        Max posts to scrape per source (sets collection ceiling).
    max_comments_per_post  (int)        Max comments per Reddit post.
    out_dir                (str)        Directory where result files are written (absolute or
                                        relative to the project root).
    platform_caps          (list[int])  Max items per platform values to test.
                                        e.g. [20, 50, 100, 500]
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import src.internal.pipeline.llm.sources  # noqa — triggers processor registration
from src.internal.pipeline.domain import SearchRequest  # noqa: E402
from src.internal.pipeline.llm.assess import assess_items, filter_relevant_items  # noqa: E402
from src.internal.pipeline.llm.run import _collect_and_normalize, _select_per_platform  # noqa: E402
from src.internal.pipeline.llm.score import compute_polarization  # noqa: E402
from src.internal.pipeline.llm.sources.registry import get_processors  # noqa: E402

_DEFAULT_CONFIG = Path(__file__).parent / "config.json"

W = 60  # section width


def load_config(path: Path) -> dict:
    raw = json.loads(path.read_text())
    missing = {"runs", "query", "out_dir", "platform_caps"} - raw.keys()
    if missing:
        raise ValueError(f"Config missing required fields: {missing}")
    if not raw["platform_caps"]:
        raise ValueError("platform_caps must be a non-empty list")
    return raw


def _build_rationale(item_scores: list, items: list) -> str:
    n = len(item_scores)
    n_for = sum(1 for s in item_scores if s.stance == 1)
    n_against = sum(1 for s in item_scores if s.stance == -1)
    n_neutral = sum(1 for s in item_scores if s.stance == 0)
    parts = [
        f"{n} items scored. Stance distribution: {n_for} for / "
        f"{n_against} against / {n_neutral} neutral."
    ]
    platform_counts: dict[str, int] = defaultdict(int)
    lean_counts: dict[str, int] = defaultdict(int)
    for item in items:
        platform_counts[item.platform] += 1
        if item.source_lean and item.source_lean != "unknown":
            lean_counts[item.source_lean] += 1
    if platform_counts:
        parts.append(
            "Platforms: "
            + ", ".join(f"{k}: {v}" for k, v in sorted(platform_counts.items()))
            + "."
        )
    if lean_counts:
        parts.append(
            "Source lean: "
            + ", ".join(f"{k}: {v}" for k, v in sorted(lean_counts.items()))
            + "."
        )
    return " ".join(parts)


def _stance_averages(item_scores: list) -> dict[str, dict]:
    groups = {"for": 1, "against": -1, "neutral": 0}
    result: dict[str, dict] = {}
    for name, stance_val in groups.items():
        group = [s for s in item_scores if s.stance == stance_val]
        if group:
            result[name] = {
                "sentiment": round(statistics.mean(s.sentiment for s in group), 2),
                "animosity": round(statistics.mean(s.animosity for s in group), 2),
                "n": len(group),
            }
        else:
            result[name] = None
    return result


def run_once(query: str, capped_items: list, cap: int, run_idx: int) -> dict:
    t0 = time.perf_counter()

    relevant = filter_relevant_items(query, capped_items)
    item_scores = assess_items(query, relevant)
    for processor in get_processors():
        item_scores = processor.post_assess(query, relevant, item_scores)
    score = compute_polarization(item_scores)

    elapsed = time.perf_counter() - t0

    n_for = sum(1 for s in item_scores if s.stance == 1)
    n_against = sum(1 for s in item_scores if s.stance == -1)
    n_neutral = sum(1 for s in item_scores if s.stance == 0)

    platform_counts: dict[str, int] = defaultdict(int)
    for item in relevant:
        platform_counts[item.platform] += 1

    score_str = f"{score:6.2f}" if score is not None else "  None"
    print(
        f"  [cap={cap}] run {run_idx + 1:>2} … "
        f"score={score_str}  n_capped={len(capped_items):>3}"
        f"  n_relevant={len(relevant):>3}  n_scored={len(item_scores):>3}  ({elapsed:.1f}s)",
        flush=True,
    )

    return {
        "cap": cap,
        "run": run_idx + 1,
        "polarization_score": score,
        "items_after_cap": len(capped_items),
        "items_after_filter": len(relevant),
        "sample_size": len(item_scores),
        "rationale": _build_rationale(item_scores, relevant),
        "stance_distribution": {"for": n_for, "against": n_against, "neutral": n_neutral},
        "stance_averages": _stance_averages(item_scores),
        "source_breakdown": dict(platform_counts),
        "elapsed_seconds": round(elapsed, 2),
        "status": "ok" if score is not None else "degraded",
    }


def compute_stats(runs: list[dict]) -> dict:
    scores = [r["polarization_score"] for r in runs if r["polarization_score"] is not None]
    times = [r["elapsed_seconds"] for r in runs]

    def _s(vals: list[float]) -> dict:
        if not vals:
            return {"n": 0, "mean": None, "std": None, "min": None, "max": None}
        return {
            "n": len(vals),
            "mean": round(statistics.mean(vals), 3),
            "std": round(statistics.stdev(vals), 3) if len(vals) > 1 else 0.0,
            "min": round(min(vals), 3),
            "max": round(max(vals), 3),
        }

    return {"score": _s(scores), "elapsed": _s(times), "total_runs": len(runs)}


# ── Text formatting ────────────────────────────────────────────────────────────

def _fmt_run(run: dict) -> str:
    lines: list[str] = []
    score = run["polarization_score"]
    score_str = f"{score:.2f} / 100" if score is not None else "N/A"
    sd = run["stance_distribution"]
    avgs = run["stance_averages"]

    lines.append(f"  --- Score ---")
    lines.append(f"  Polarization   : {score_str}")
    lines.append(f"  Sample size    : {run['sample_size']}")
    lines.append(f"  Cap            : {run['cap']}")
    lines.append(f"  After cap      : {run['items_after_cap']}")
    lines.append(f"  After filter   : {run['items_after_filter']}")
    lines.append(f"  Rationale      : {run['rationale']}")
    lines.append(f"  Elapsed        : {run['elapsed_seconds']}s")
    lines.append(f"  Status         : {run['status']}")
    lines.append("")
    lines.append(f"  --- Stance Distribution ---")
    lines.append(f"    For       : {sd['for']}")
    lines.append(f"    Against   : {sd['against']}")
    lines.append(f"    Neutral   : {sd['neutral']}")
    lines.append("")
    lines.append(f"  --- Item Averages By Stance ---")
    for stance_name in ("for", "against", "neutral"):
        a = avgs.get(stance_name)
        if a:
            lines.append(
                f"    {stance_name.capitalize():<8} | Sentiment: {a['sentiment']:.2f}"
                f" | Animosity: {a['animosity']:.2f}"
            )
        else:
            lines.append(f"    {stance_name.capitalize():<8} | (no items)")

    return "\n".join(lines)


def _fmt_cap_block(cap: int, runs: list[dict], stats: dict | None) -> str:
    lines: list[str] = []

    lines.append("=" * W)
    lines.append(f"  Cap  : {cap} items per platform")
    lines.append("=" * W)

    if not runs:
        lines.append("  [SKIPPED — no items after cap]")
        lines.append("")
        return "\n".join(lines)

    for run in runs:
        lines.append(f"\n  Run {run['run']} of {len(runs)}")
        lines.append("  " + "-" * (W - 2))
        lines.append(_fmt_run(run))
        lines.append("")

    if stats:
        sc = stats["score"]
        lines.append("  " + "-" * (W - 2))
        lines.append("  Aggregate across runs")
        lines.append("  " + "-" * (W - 2))
        if sc["mean"] is not None:
            lines.append(f"    Mean score : {sc['mean']:.2f}")
            lines.append(f"    Std dev    : {sc['std']:.2f}")
            lines.append(f"    Min / Max  : {sc['min']:.2f} / {sc['max']:.2f}")
        else:
            lines.append("    Mean score : N/A")
        lines.append("")

    return "\n".join(lines)


def format_output(
    query: str,
    config: dict,
    n_collected: int,
    all_runs: dict[int, list[dict]],
    stats: dict[int, dict],
    items_per_cap: dict[int, int],
) -> str:
    lines: list[str] = []
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines.append("=" * W)
    lines.append("  PLATFORM CAP ABLATION STUDY")
    lines.append("=" * W)
    if config.get("description"):
        lines.append(f"  Description : {config['description']}")
    lines.append(f"  Date        : {ts}")
    lines.append(f"  Query       : {query!r}")
    lines.append(f"  Collected   : {n_collected} items (before any cap)")
    lines.append(f"  Runs        : {config['runs']} per cap value")
    lines.append(f"  Caps tested : {config['platform_caps']}")
    lines.append("=" * W)
    lines.append("")

    for cap in config["platform_caps"]:
        runs = all_runs.get(cap, [])
        block = _fmt_cap_block(cap, runs, stats.get(cap))
        lines.append(block)

    # Summary table
    lines.append("=" * W)
    lines.append("  SUMMARY TABLE")
    lines.append("=" * W)
    header = (
        f"  {'Cap':>6} {'n_capped':>8} {'n_relevant':>10}"
        f" {'Mean':>7} {'Std':>6} {'Min':>7} {'Max':>7}"
    )
    lines.append(header)
    lines.append("  " + "-" * (W - 2))

    for cap in config["platform_caps"]:
        runs = all_runs.get(cap, [])
        n_capped = items_per_cap.get(cap, 0)
        if not runs:
            lines.append(f"  {cap:>6} {n_capped:>8}{'':>10}   SKIP")
            continue
        n_relevant_mean = round(statistics.mean(r["items_after_filter"] for r in runs), 1)
        sc = stats[cap]["score"]
        mean_s = f"{sc['mean']:7.2f}" if sc["mean"] is not None else "   None"
        std_s = f"{sc['std']:6.2f}" if sc["std"] is not None else "  None"
        min_s = f"{sc['min']:7.2f}" if sc["min"] is not None else "   None"
        max_s = f"{sc['max']:7.2f}" if sc["max"] is not None else "   None"
        lines.append(
            f"  {cap:>6} {n_capped:>8} {n_relevant_mean:>10}"
            f" {mean_s} {std_s} {min_s} {max_s}"
        )

    lines.append("=" * W)
    lines.append("")
    return "\n".join(lines)


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default=str(_DEFAULT_CONFIG),
        help=f"Path to JSON config file (default: {_DEFAULT_CONFIG.name} next to this script)",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = _PROJECT_ROOT / config_path
    config = load_config(config_path)

    query = config["query"]
    time_filter = config.get("time_filter", "month")
    max_posts = config.get("max_posts")
    max_comments_per_post = config.get("max_comments_per_post")

    out_dir = Path(config["out_dir"])
    if not out_dir.is_absolute():
        out_dir = _PROJECT_ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Step 1: Collect once ───────────────────────────────────────────────────
    print(
        f"\nCollecting items for {query!r}  "
        f"(time_filter={time_filter}, max_posts={max_posts}, "
        f"max_comments_per_post={max_comments_per_post}) ...",
        flush=True,
    )

    request = SearchRequest(
        query=query,
        time_filter=time_filter,
        max_posts=max_posts,
        max_comments_per_post=max_comments_per_post,
    )
    collected = _collect_and_normalize(request)
    platforms = {item.platform for item in collected}
    print(
        f"Collected {len(collected)} items  (platforms: {sorted(platforms)})",
        flush=True,
    )

    # ── Step 2: Run pipeline for each cap ─────────────────────────────────────
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    query_slug = query.lower().replace(" ", "_")[:30]

    all_runs: dict[int, list[dict]] = {}
    items_per_cap: dict[int, int] = {}

    for cap in config["platform_caps"]:
        capped = _select_per_platform(collected, max_per_platform=cap)
        items_per_cap[cap] = len(capped)
        print(
            f"\n{'=' * 50}\n"
            f"Cap: {cap} items/platform  →  {len(capped)} items total\n"
            f"{'=' * 50}",
            flush=True,
        )
        if not capped:
            print(f"  [SKIP] no items after applying cap={cap}", flush=True)
            all_runs[cap] = []
            continue

        all_runs[cap] = [
            run_once(query, capped, cap, i) for i in range(config["runs"])
        ]

    stats = {cap: compute_stats(runs) for cap, runs in all_runs.items()}
    output_text = format_output(
        query, config, len(collected), all_runs, stats, items_per_cap
    )

    txt_path = out_dir / f"{query_slug}_{ts}.txt"
    json_path = out_dir / f"{query_slug}_{ts}.json"
    txt_path.write_text(output_text)
    json_path.write_text(
        json.dumps(
            {
                "config": config,
                "query": query,
                "n_collected": len(collected),
                "runs": {str(cap): runs for cap, runs in all_runs.items()},
                "stats": {str(cap): s for cap, s in stats.items()},
            },
            indent=2,
        )
    )

    print(f"\nSummary  → {txt_path}")
    print(f"Raw JSON → {json_path}")


if __name__ == "__main__":
    main()
