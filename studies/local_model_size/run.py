"""Local model size ablation study: same fake items assessed by Ollama models
of increasing parameter count within a chosen model family.

Runs ALL models in the family set by "model_family" in config.json sequentially
and produces a side-by-side comparison table showing how score quality changes
with model size.

Prerequisites:
    - Ollama running locally  (https://ollama.com)
    - Models pulled:  ollama pull gemma3:1b  (etc.)
    - Override host:  OLLAMA_HOST=http://host:11434

Usage:
    python studies/local_model_size/run_that.py
    python studies/local_model_size/run_that.py --config path/to/other_config.json

To switch family or tweak any parameter, edit config.json.
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
from src.internal.pipeline.llm.assess import assess_items  # noqa: E402
from src.internal.pipeline.llm.score import compute_polarization  # noqa: E402
from src.internal.pipeline.llm.sources.registry import get_processors  # noqa: E402
from src.internal.pipeline.mock.data import get_fake_data  # noqa: E402

_DEFAULT_CONFIG = Path(__file__).parent / "config.json"

EXPECTED = {
    "fake_polarized_fictitious":   "~100",
    "fake_moderate_fictitious":    "~35-70",
    "fake_neutral_fictitious":     "~0",
    "fake_polarized_general":      "~100",
    "fake_moderate_general":       "~35-70",
    "fake_neutral_general":        "~0",
    "fake_polarized_real_context": "~100",
    "fake_moderate_real_context":  "~35-70",
    "fake_neutral_real_context":   "~0",
}

W = 72


# ── Config ─────────────────────────────────────────────────────────────────────

def load_config(path: Path) -> dict:
    raw = json.loads(path.read_text())
    required = {"model_family", "model_families", "scenarios", "runs", "out_dir"}
    missing = required - raw.keys()
    if missing:
        raise ValueError(f"Config missing required fields: {missing}")
    return raw


def resolve_family(config: dict) -> tuple[str, list[dict]]:
    family_key = config["model_family"]
    families = config["model_families"]
    if family_key not in families:
        raise ValueError(
            f"model_family {family_key!r} not found in model_families. Available: {list(families)}"
        )
    models = families[family_key]["models"]
    for m in models:
        if "label" not in m or "model_id" not in m or "params_billions" not in m:
            raise ValueError(f"Each model entry needs 'label', 'model_id', 'params_billions': {m}")
    return family_key, sorted(models, key=lambda m: m["params_billions"])


# ── Per-run helpers ────────────────────────────────────────────────────────────

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
        f"{n} items scored. Stance: {n_for} for / {n_against} against / {n_neutral} neutral."
    ]
    bd = _source_breakdown(items)
    if bd["platforms"]:
        parts.append(
            "Platforms: "
            + ", ".join(f"{k}: {v}" for k, v in sorted(bd["platforms"].items()))
            + "."
        )
    return " ".join(parts)


def run_once(
    query: str,
    items: list,
    model_id: str,
    model_label: str,
    params_billions: float,
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
        f"  [{model_label} | {scenario.replace('fake_', '')}]"
        f" run {run_idx + 1}/{n_runs}"
        f" … score={score_str}  ({elapsed:.1f}s)",
        flush=True,
    )

    return {
        "model_label": model_label,
        "model_id": model_id,
        "params_billions": params_billions,
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


# ── Text formatting ────────────────────────────────────────────────────────────

def _fmt_model_block(model_entry: dict, scenario_stats: dict[str, dict]) -> str:
    lines: list[str] = []
    lines.append(f"  {model_entry['label']}  ({model_entry['params_billions']}B params)")
    lines.append("  " + "-" * (W - 2))
    for scenario, stats in scenario_stats.items():
        sc = stats["score"]
        exp = EXPECTED.get(scenario, "?")
        short = scenario.replace("fake_", "")
        if sc["mean"] is not None:
            lines.append(
                f"    {short:<30} expected={exp:<8}"
                f" mean={sc['mean']:6.2f}  std={sc['std']:5.2f}"
                f"  elapsed={stats['elapsed']['mean']:.1f}s"
            )
        else:
            lines.append(f"    {short:<30} expected={exp:<8} ERR")
    return "\n".join(lines)


def format_output(
    family_key: str,
    family_config: dict,
    config: dict,
    models: list[dict],
    active_scenarios: list[str],
    n_runs: int,
    all_stats: dict[str, dict[str, dict]],
) -> str:
    lines: list[str] = []
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines.append("=" * W)
    lines.append("  LOCAL MODEL SIZE ABLATION STUDY")
    lines.append("=" * W)
    if config.get("description"):
        lines.append(f"  Description : {config['description']}")
    lines.append(f"  Date        : {ts}")
    lines.append(f"  Family      : {family_key}  — {family_config.get('description', '')}")
    lines.append(f"  Ollama host : {config.get('ollama_host', 'http://localhost:11434')}")
    lines.append(f"  Runs        : {n_runs} per scenario per model")
    lines.append(f"  Scenarios   : {', '.join(active_scenarios)}")
    lines.append("=" * W)
    lines.append("")

    for model_entry in models:
        label = model_entry["label"]
        scenario_stats = all_stats.get(label, {})
        lines.append(_fmt_model_block(model_entry, scenario_stats))
        lines.append("")

    lines.append("=" * W)
    lines.append("  SUMMARY — Score by model size")
    lines.append("=" * W)

    col_w = 12
    header_parts = [f"  {'Model':<20} {'Params':>7}B"]
    for scenario in active_scenarios:
        short = scenario.replace("fake_", "")[:col_w]
        header_parts.append(f"  {short:>{col_w}}")
    lines.append("".join(header_parts))
    lines.append("  " + "-" * (W - 2))

    for model_entry in models:
        label = model_entry["label"]
        row = [f"  {label:<20} {model_entry['params_billions']:>7.1f}B"]
        for scenario in active_scenarios:
            sc = all_stats.get(label, {}).get(scenario, {}).get("score", {})
            mean = sc.get("mean")
            if mean is not None:
                row.append(f"  {mean:>{col_w}.2f}")
            else:
                row.append(f"  {'ERR':>{col_w}}")
        lines.append("".join(row))

    lines.append("  " + "-" * (W - 2))
    lines.append("  Expected ranges:")
    for scenario in active_scenarios:
        short = scenario.replace("fake_", "")
        lines.append(f"    {short:<30} {EXPECTED.get(scenario, '?')}")
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

    family_key, models = resolve_family(config)
    family_config = config["model_families"][family_key]
    n_runs = config["runs"]
    active_scenarios = config["scenarios"]

    out_dir = Path(config["out_dir"])
    if not out_dir.is_absolute():
        out_dir = _PROJECT_ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")

    print(
        f"\nLocal model size study — family: {family_key}\n"
        f"Models    : {[m['label'] for m in models]}\n"
        f"Scenarios : {active_scenarios}\n"
        f"Runs      : {n_runs} per scenario per model",
        flush=True,
    )

    all_runs: dict[str, dict[str, list[dict]]] = {}
    all_stats: dict[str, dict[str, dict]] = {}

    for model_entry in models:
        label = model_entry["label"]
        model_id = model_entry["model_id"]
        params = model_entry["params_billions"]

        print(
            f"\n{'=' * W}\n"
            f"Model: {label}  ({params}B)  [{model_id}]\n"
            f"{'=' * W}",
            flush=True,
        )

        all_runs[label] = {}
        all_stats[label] = {}

        for scenario in active_scenarios:
            try:
                query, items = get_fake_data(scenario)
            except KeyError:
                print(f"  WARNING: unknown scenario {scenario!r}, skipping", flush=True)
                continue

            print(f"\n  Scenario: {scenario}  (expected: {EXPECTED.get(scenario, '?')})", flush=True)
            runs = [
                run_once(query, items, model_id, label, params, scenario, i, n_runs)
                for i in range(n_runs)
            ]
            all_runs[label][scenario] = runs
            all_stats[label][scenario] = compute_stats(runs)

    output_text = format_output(
        family_key, family_config, config, models,
        active_scenarios, n_runs, all_stats,
    )

    slug = family_key.replace("/", "-")
    txt_path = out_dir / f"{slug}_{ts}.txt"
    json_path = out_dir / f"{slug}_{ts}.json"

    txt_path.write_text(output_text, encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "family": family_key,
                "family_config": family_config,
                "active_scenarios": active_scenarios,
                "n_runs": n_runs,
                "runs": all_runs,
                "stats": all_stats,
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
