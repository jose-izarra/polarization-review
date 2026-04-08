"""Model size ablation study: same fake items assessed by each model size in the family.

Loads all models from config.json, runs LLM assessment for each one, and
produces a single txt file comparing all models side-by-side.

Usage:
    python studies/model_size/run_that.py
    python studies/model_size/run_that.py --config path/to/other_config.json

To change the model family or add/remove sizes, edit config.json.
"""

from __future__ import annotations

import argparse
import json
import os
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
from src.internal.pipeline.mock.data import get_fake_data  # noqa: E402

_DEFAULT_CONFIG = Path(__file__).parent / "config.json"

W = 72


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


_DEFAULT_ITEMS_DIR = _PROJECT_ROOT / "data"


def load_config(path: Path) -> dict:
    raw = json.loads(path.read_text())
    required = {"models", "scenarios", "runs", "out_dir"}
    missing = required - raw.keys()
    if missing:
        raise ValueError(f"Config missing required fields: {missing}")
    for m in raw["models"]:
        if "label" not in m or "model_id" not in m:
            raise ValueError(f"Each model entry needs 'label' and 'model_id': {m}")
    return raw


def load_scenario(scenario: str, items_dir: Path) -> tuple[str, list[NormalizedItem]]:
    """Return (query, items) for a scenario.

    Scenarios starting with 'fake_' are loaded from mock data; all others are
    loaded from items_dir/items_<scenario>.json.
    """
    if scenario.startswith("fake_"):
        return get_fake_data(scenario)
    path = items_dir / f"items_{scenario}.json"
    raw = json.loads(path.read_text())
    return raw["query"], [
        NormalizedItem(
            id=it["id"],
            text=it["text"],
            url=it["url"],
            timestamp=it["timestamp"],
            engagement_score=it["engagement_score"],
            content_type=it["content_type"],
            platform=it.get("platform", "unknown"),
            source_lean=it.get("source_lean"),
            relevance_score=it.get("relevance_score"),
            parent_video_stance=it.get("parent_video_stance"),
            parent_video_id=it.get("parent_video_id"),
        )
        for it in raw["items"]
    ]


# ---------------------------------------------------------------------------
# Per-run helpers (shared with model_bias study)
# ---------------------------------------------------------------------------


def _stance_averages(item_scores: list) -> dict:
    groups = {"for": 1, "against": -1, "neutral": 0}
    result: dict = {}
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


def _source_breakdown(items: list) -> dict:
    platforms: dict[str, int] = defaultdict(int)
    lean: dict[str, int] = defaultdict(int)
    for item in items:
        platforms[item.platform] += 1
        if item.source_lean and item.source_lean != "unknown":
            lean[item.source_lean] += 1
    return {"platforms": dict(platforms), "lean": dict(lean)}


def _build_rationale(item_scores: list, items: list) -> str:
    n = len(item_scores)
    n_for = sum(1 for s in item_scores if s.stance == 1)
    n_against = sum(1 for s in item_scores if s.stance == -1)
    n_neutral = sum(1 for s in item_scores if s.stance == 0)
    parts = [
        f"{n} items scored. Stance distribution: {n_for} for / "
        f"{n_against} against / {n_neutral} neutral."
    ]
    bd = _source_breakdown(items)
    if bd["platforms"]:
        parts.append(
            "Platforms: "
            + ", ".join(f"{k}: {v}" for k, v in sorted(bd["platforms"].items()))
            + "."
        )
    if bd["lean"]:
        parts.append(
            "Source lean: "
            + ", ".join(f"{k}: {v}" for k, v in sorted(bd["lean"].items()))
            + "."
        )
    return " ".join(parts)


def run_once(
    query: str,
    items: list,
    model_id: str,
    model_label: str,
    scenario: str,
    run_idx: int,
    n_runs: int,
) -> dict:
    t0 = time.perf_counter()
    try:
        item_scores = assess_items(query, items, model=model_id)
        for processor in get_processors():
            item_scores = processor.post_assess(query, items, item_scores)
        score = compute_polarization(item_scores)
        status = "ok"
        error = None
    except Exception as exc:
        score = None
        item_scores = []
        status = "error"
        error = str(exc)

    elapsed = time.perf_counter() - t0

    n_for = sum(1 for s in item_scores if s.stance == 1)
    n_against = sum(1 for s in item_scores if s.stance == -1)
    n_neutral = sum(1 for s in item_scores if s.stance == 0)

    score_str = f"{score:6.2f}" if score is not None else "   ERR"
    print(
        f"  [{model_label}] [{scenario.replace('fake_', '')}] run {run_idx + 1}/{n_runs}"
        f" … score={score_str}  ({elapsed:.1f}s)",
        flush=True,
    )

    return {
        "model_label": model_label,
        "model_id": model_id,
        "scenario": scenario,
        "run": run_idx + 1,
        "polarization_score": score,
        "sample_size": len(item_scores),
        "rationale": _build_rationale(item_scores, items) if item_scores else "—",
        "stance_distribution": {"for": n_for, "against": n_against, "neutral": n_neutral},
        "stance_averages": _stance_averages(item_scores),
        "source_breakdown": _source_breakdown(items),
        "elapsed_seconds": round(elapsed, 2),
        "status": status,
        "error": error,
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


# ---------------------------------------------------------------------------
# Text formatting
# ---------------------------------------------------------------------------


def _fmt_run(run: dict, total_runs: int) -> str:
    lines: list[str] = []
    score = run["polarization_score"]
    sd = run["stance_distribution"]
    avgs = run["stance_averages"]
    bd = run["source_breakdown"]

    lines.append(f"  Run {run['run']} of {total_runs}")
    lines.append("  " + "-" * (W - 2))
    lines.append(f"  Polarization : {f'{score:.2f} / 100' if score is not None else 'N/A'}")
    lines.append(f"  Sample size  : {run['sample_size']}")
    lines.append(f"  Elapsed      : {run['elapsed_seconds']}s")
    lines.append(f"  Status       : {run['status']}")
    if run.get("error"):
        lines.append(f"  Error        : {run['error']}")
    lines.append(f"  Rationale    : {run['rationale']}")
    lines.append("")
    lines.append("  Stance Distribution")
    lines.append(f"    For       : {sd['for']}")
    lines.append(f"    Against   : {sd['against']}")
    lines.append(f"    Neutral   : {sd['neutral']}")
    lines.append("")
    lines.append("  Item Averages By Stance")
    for stance_name in ("for", "against", "neutral"):
        a = avgs.get(stance_name)
        if a:
            lines.append(
                f"    {stance_name.capitalize():<8} | Sentiment: {a['sentiment']:.2f}"
                f" | Animosity: {a['animosity']:.2f} | n={a['n']}"
            )
        else:
            lines.append(f"    {stance_name.capitalize():<8} | (no items)")
    lines.append("")
    lines.append("  Source Breakdown")
    for platform, count in sorted(bd["platforms"].items()):
        lines.append(f"    {platform:<12}: {count}")
    if bd["lean"]:
        lines.append("  Source Lean")
        for lean_label, count in sorted(bd["lean"].items()):
            lines.append(f"    {lean_label:<12}: {count}")

    return "\n".join(lines)


def _fmt_model_section(model_entry: dict, scenario: str, runs: list[dict], stats: dict) -> str:
    lines: list[str] = []
    lines.append(f"  --- Model: {model_entry['label']}  ({model_entry['model_id']}) ---")
    lines.append("")

    if not runs:
        lines.append("  [SKIPPED — no runs recorded]")
        lines.append("")
        return "\n".join(lines)

    for run in runs:
        lines.append(_fmt_run(run, len(runs)))
        lines.append("")

    sc = stats["score"]
    lines.append("  " + "-" * (W - 2))
    lines.append("  Aggregate")
    lines.append("  " + "-" * (W - 2))
    if sc["mean"] is not None:
        lines.append(f"    Mean score : {sc['mean']:.2f}")
        lines.append(f"    Std dev    : {sc['std']:.2f}")
        lines.append(f"    Min / Max  : {sc['min']:.2f} / {sc['max']:.2f}")
    else:
        lines.append("    Mean score : N/A (all runs errored)")
    lines.append("")

    return "\n".join(lines)


def _fmt_summary_table(
    models: list[dict],
    scenarios: list[str],
    all_stats: dict[tuple[str, str], dict],
) -> str:
    lines: list[str] = []
    lines.append("=" * W)
    lines.append("  SUMMARY")
    lines.append("=" * W)

    col_w = 16
    scenario_w = 35

    header = f"  {'Scenario':<{scenario_w}}"
    for m in models:
        header += f"  {m['label']:>{col_w}}"
    lines.append(header)
    lines.append("  " + "-" * (W - 2))

    for scenario in scenarios:
        row = f"  {scenario:<{scenario_w}}"
        for m in models:
            sc = all_stats[(m["label"], scenario)]["score"]
            if sc["mean"] is None:
                cell = "ERR"
            else:
                cell = f"{sc['mean']:.2f} ± {sc['std']:.2f}"
            row += f"  {cell:>{col_w}}"
        lines.append(row)

    lines.append("=" * W)
    lines.append("")
    return "\n".join(lines)


def format_output(
    config: dict,
    models: list[dict],
    active_scenarios: list[str],
    n_runs: int,
    all_runs: dict[tuple[str, str], list[dict]],
    all_stats: dict[tuple[str, str], dict],
) -> str:
    lines: list[str] = []
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines += [
        "=" * W,
        "  MODEL SIZE ABLATION STUDY",
        "=" * W,
    ]
    if config.get("description"):
        lines.append(f"  Description : {config['description']}")
    lines += [
        f"  Date        : {ts}",
        f"  Models      : {', '.join(m['label'] for m in models)}",
        f"  Runs        : {n_runs} per (model, scenario) pair",
        f"  Scenarios   : {', '.join(active_scenarios)}",
        "=" * W,
        "",
    ]

    for scenario in active_scenarios:
        lines += [
            "=" * W,
            f"  Scenario : {scenario}",
            "=" * W,
        ]
        for model_entry in models:
            key = (model_entry["label"], scenario)
            runs = all_runs.get(key, [])
            stats = all_stats.get(key, {"score": {"mean": None}, "elapsed": {"mean": None}})
            lines.append(_fmt_model_section(model_entry, scenario, runs, stats))

    lines.append(_fmt_summary_table(models, active_scenarios, all_stats))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


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

    models: list[dict] = config["models"]
    n_runs: int = config["runs"]
    active_scenarios: list[str] = config["scenarios"]

    out_dir = Path(config["out_dir"])
    if not out_dir.is_absolute():
        out_dir = _PROJECT_ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    raw_items_dir = config.get("items_dir")
    items_dir = (
        Path(raw_items_dir) if raw_items_dir else _DEFAULT_ITEMS_DIR
    )
    if not items_dir.is_absolute():
        items_dir = _PROJECT_ROOT / items_dir

    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")

    print(
        f"\nModel size ablation study\n"
        f"Models    : {', '.join(m['label'] for m in models)}\n"
        f"Scenarios : {active_scenarios}\n"
        f"Runs      : {n_runs} per (model, scenario) pair",
        flush=True,
    )

    all_runs: dict[tuple[str, str], list[dict]] = {}

    for model_entry in models:
        model_id = model_entry["model_id"]
        model_label = model_entry["label"]
        os.environ["POLARIZATION_MODEL"] = model_id

        print(
            f"\n{'#' * W}\n  Model: {model_label}  ({model_id})\n{'#' * W}",
            flush=True,
        )

        for scenario in active_scenarios:
            print(f"\n{'=' * W}\n  Scenario: {scenario}\n{'=' * W}", flush=True)
            try:
                query, items = load_scenario(scenario, items_dir)
            except (FileNotFoundError, KeyError):
                print(f"  WARNING: could not load scenario {scenario!r}, skipping", flush=True)
                continue

            print(f"  Loaded {len(items)} items", flush=True)
            all_runs[(model_label, scenario)] = [
                run_once(query, items, model_id, model_label, scenario, i, n_runs)
                for i in range(n_runs)
            ]

    all_stats = {key: compute_stats(runs) for key, runs in all_runs.items()}
    output_text = format_output(config, models, active_scenarios, n_runs, all_runs, all_stats)

    txt_path = out_dir / f"model_size_{ts}.txt"
    json_path = out_dir / f"model_size_{ts}.json"

    txt_path.write_text(output_text, encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "timestamp": ts,
                "models": models,
                "active_scenarios": active_scenarios,
                "n_runs": n_runs,
                "results": {
                    f"{label}::{scenario}": {
                        "stats": all_stats[(label, scenario)],
                        "runs": all_runs[(label, scenario)],
                    }
                    for label, scenario in all_runs
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"\n{output_text}")
    print(f"Summary  → {txt_path}")
    print(f"Raw JSON → {json_path}")


if __name__ == "__main__":
    main()
