"""Source ablation study: effect of different source combinations on polarization score.

Loads pre-collected items from a data/items_*.json file, filters by platform for
each source configuration, then runs the LLM assessment + scoring pipeline.
Collection is skipped entirely, so results are reproducible across runs.

All configuration is read from a JSON file (default: config.json next to this script).

Usage:
    python studies/source_effects/run_source_ablation.py
    python studies/source_effects/run_source_ablation.py --config path/to/config.json

Config file fields:
    description    (str)   Human-readable label printed in the output file.
    runs           (int)   How many times to repeat each source config.
                           LLM assessment is stochastic, so >1 run is recommended.
    items_file     (str)   Path to a data/items_*.json file (absolute or relative
                           to the project root).
    out_dir        (str)   Directory where result files are written (absolute or
                           relative to the project root).
    source_configs (list)  Each entry:
                             label   (str)        Name used in output tables.
                             sources (list[str])  Platforms to include.
                                                  Allowed values: reddit, gnews, youtube.
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
from src.internal.pipeline.domain import NormalizedItem  # noqa: E402
from src.internal.pipeline.llm.assess import assess_items  # noqa: E402
from src.internal.pipeline.llm.score import compute_polarization  # noqa: E402
from src.internal.pipeline.llm.sources.registry import get_processors  # noqa: E402

_DEFAULT_CONFIG = Path(__file__).parent / "config.json"

W = 60  # section width


def load_config(path: Path) -> dict:
    raw = json.loads(path.read_text())
    missing = {"runs", "items_file", "out_dir", "source_configs"} - raw.keys()
    if missing:
        raise ValueError(f"Config missing required fields: {missing}")
    for entry in raw["source_configs"]:
        if "label" not in entry or "sources" not in entry:
            raise ValueError(f"Each source_config entry needs 'label' and 'sources': {entry}")
    return raw


def load_items(items_file: Path) -> tuple[str, list[NormalizedItem]]:
    data = json.loads(items_file.read_text())
    return data["query"], [NormalizedItem(**item) for item in data["items"]]


def filter_by_sources(items: list[NormalizedItem], sources: list[str]) -> list[NormalizedItem]:
    return [item for item in items if item.platform in sources]


def _build_rationale(item_scores: list, items: list[NormalizedItem]) -> str:
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
    """Return mean sentiment and animosity per stance group."""
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


def run_once(
    query: str,
    items: list[NormalizedItem],
    sources: list[str],
    run_idx: int,
    label: str,
) -> dict:
    t0 = time.perf_counter()

    item_scores = assess_items(query, items)
    for processor in get_processors():
        item_scores = processor.post_assess(query, items, item_scores)
    score = compute_polarization(item_scores)

    elapsed = time.perf_counter() - t0

    n_for = sum(1 for s in item_scores if s.stance == 1)
    n_against = sum(1 for s in item_scores if s.stance == -1)
    n_neutral = sum(1 for s in item_scores if s.stance == 0)

    platform_counts: dict[str, int] = defaultdict(int)
    for item in items:
        platform_counts[item.platform] += 1

    score_str = f"{score:6.2f}" if score is not None else "  None"
    print(
        f"  [{label}] run {run_idx + 1:>2} … "
        f"score={score_str}  n={len(item_scores):>3}  ({elapsed:.1f}s)",
        flush=True,
    )

    return {
        "label": label,
        "sources": sources,
        "run": run_idx + 1,
        "polarization_score": score,
        "sample_size": len(item_scores),
        "rationale": _build_rationale(item_scores, items),
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
    lines.append(f"  Sources        : {', '.join(run['sources'])}")
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


def _fmt_config_block(entry: dict, runs: list[dict], stats: dict | None) -> str:
    lines: list[str] = []
    label = entry["label"]
    sources_str = ", ".join(entry["sources"])

    lines.append("=" * W)
    lines.append(f"  Config : {label}")
    lines.append(f"  Sources: {sources_str}")
    lines.append("=" * W)

    if not runs:
        lines.append("  [SKIPPED — no items for these sources]")
        lines.append("")
        return "\n".join(lines)

    for run in runs:
        lines.append(f"\n  Run {run['run']} of {len(runs)}")
        lines.append("  " + "-" * (W - 2))
        lines.append(_fmt_run(run))
        lines.append("")

    # Per-config aggregate
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
    items_file: str,
    all_runs: dict[str, list[dict]],
    stats: dict[str, dict],
    items_per_config: dict[str, int],
) -> str:
    lines: list[str] = []
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # ── Header ────────────────────────────────────────────────────────────────
    lines.append("=" * W)
    lines.append("  SOURCE ABLATION STUDY")
    lines.append("=" * W)
    if config.get("description"):
        lines.append(f"  Description : {config['description']}")
    lines.append(f"  Date        : {ts}")
    lines.append(f"  Query       : {query!r}")
    lines.append(f"  Items file  : {items_file}")
    lines.append(f"  Runs        : {config['runs']} per source config")
    lines.append(f"  Configs     : {len(config['source_configs'])}")
    lines.append("=" * W)
    lines.append("")

    # ── Per-config detailed blocks ─────────────────────────────────────────────
    for entry in config["source_configs"]:
        label = entry["label"]
        runs = all_runs.get(label, [])
        block = _fmt_config_block(entry, runs, stats.get(label))
        lines.append(block)

    # ── Summary table ─────────────────────────────────────────────────────────
    lines.append("=" * W)
    lines.append("  SUMMARY TABLE")
    lines.append("=" * W)
    header = (
        f"  {'Config':<20} {'Sources':<22} {'n':>4}"
        f" {'Mean':>7} {'Std':>6} {'Min':>7} {'Max':>7}"
    )
    lines.append(header)
    lines.append("  " + "-" * (W - 2))

    for entry in config["source_configs"]:
        label = entry["label"]
        runs = all_runs.get(label, [])
        sources_str = "+".join(entry["sources"])
        n = items_per_config.get(label, 0)
        if not runs:
            lines.append(f"  {label:<20} {sources_str:<22} {n:>4}   SKIP")
            continue
        sc = stats[label]["score"]
        mean_s = f"{sc['mean']:7.2f}" if sc["mean"] is not None else "   None"
        std_s = f"{sc['std']:6.2f}" if sc["std"] is not None else "  None"
        min_s = f"{sc['min']:7.2f}" if sc["min"] is not None else "   None"
        max_s = f"{sc['max']:7.2f}" if sc["max"] is not None else "   None"
        lines.append(
            f"  {label:<20} {sources_str:<22} {n:>4}"
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

    items_path = Path(config["items_file"])
    if not items_path.is_absolute():
        items_path = _PROJECT_ROOT / items_path
    query, all_items = load_items(items_path)

    platforms = {item.platform for item in all_items}
    print(f"Loaded {len(all_items)} items for {query!r}  (platforms: {sorted(platforms)})", flush=True)

    out_dir = Path(config["out_dir"])
    if not out_dir.is_absolute():
        out_dir = _PROJECT_ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    query_slug = query.lower().replace(" ", "_")[:30]

    all_runs: dict[str, list[dict]] = {}
    items_per_config: dict[str, int] = {}

    for entry in config["source_configs"]:
        label = entry["label"]
        sources = entry["sources"]
        filtered = filter_by_sources(all_items, sources)
        items_per_config[label] = len(filtered)
        print(
            f"\n{'=' * 50}\nConfig: {label}  sources={sources}  n={len(filtered)}\n{'=' * 50}",
            flush=True,
        )
        if not filtered:
            print(f"  [SKIP] no items for sources {sources}", flush=True)
            all_runs[label] = []
            continue

        all_runs[label] = [
            run_once(query, filtered, sources, i, label) for i in range(config["runs"])
        ]

    stats = {label: compute_stats(runs) for label, runs in all_runs.items()}
    output_text = format_output(query, config, str(items_path), all_runs, stats, items_per_config)

    txt_path = out_dir / f"{query_slug}_{ts}.txt"
    json_path = out_dir / f"{query_slug}_{ts}.json"
    txt_path.write_text(output_text)
    json_path.write_text(
        json.dumps(
            {
                "config": config,
                "query": query,
                "items_file": str(items_path),
                "runs": all_runs,
                "stats": stats,
            },
            indent=2,
        )
    )

    print(f"\nSummary  → {txt_path}")
    print(f"Raw JSON → {json_path}")


if __name__ == "__main__":
    main()
