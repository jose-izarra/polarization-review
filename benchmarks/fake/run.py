"""Benchmark the three fake pipeline scenarios 10 times each.

Runs fake_polarized, fake_moderate, and fake_neutral through the real LLM
pipeline (Gemini API) and saves per-run results plus a summary table.

Usage:
    python benchmarks/fake/run.py [--runs N] [--out DIR]

Outputs (written to --out, default: benchmarks/fake/results/):
    results_<timestamp>.json   — raw per-run PolarizationResult dicts
    summary_<timestamp>.txt    — human-readable summary table
    summary_<timestamp>.json   — machine-readable summary stats
"""

from __future__ import annotations

import argparse
import statistics
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root is on sys.path so src.* imports work when called
# from any working directory.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.internal.pipeline.domain import SearchRequest  # noqa: E402
from src.internal.pipeline.llm.run import run_search  # noqa: E402

SCENARIOS_FICTITIOUS = [
    "fake_polarized_fictitious",
    "fake_moderate_fictitious",
    "fake_neutral_fictitious",
]

SCENARIOS_GENERAL = [
    "fake_polarized_general",
    "fake_moderate_general",
    "fake_neutral_general",
]

DATASETS: dict[str, list[str]] = {
    "fictitious": SCENARIOS_FICTITIOUS,
    "general": SCENARIOS_GENERAL,
}

# Default dataset used when --dataset is not specified
DEFAULT_DATASET = "general"
SCENARIOS = SCENARIOS_GENERAL

EXPECTED = {
    "fake_polarized_fictitious": "~100",
    "fake_moderate_fictitious": "~35-70",
    "fake_neutral_fictitious": "~0",
    "fake_polarized_general": "~100",
    "fake_moderate_general": "~35-70",
    "fake_neutral_general": "~0",
}


_print_lock = threading.Lock()


def run_scenario(mode: str, run_idx: int) -> dict:
    """Run one pass of a fake scenario and return a result dict."""
    t0 = time.perf_counter()
    request = SearchRequest(query="benchmark", mode=mode)
    result = run_search(request)
    elapsed = time.perf_counter() - t0

    score = result.polarization_score
    status = result.status
    with _print_lock:
        print(
            f"  [{mode}] run {run_idx + 1:>2} … "
            f"score={score:6.2f} "
            f"  status={status}  ({elapsed:.1f}s)",
            flush=True,
        )

    return {
        "mode": mode,
        "run": run_idx + 1,
        "polarization_score": score,
        "sample_size": result.sample_size,
        "stance_distribution": result.stance_distribution,
        "source_breakdown": result.source_breakdown,
        "status": status,
        "error_message": result.error_message,
        "elapsed_seconds": round(elapsed, 2),
        "collected_at": result.collected_at,
        "rationale": result.rationale,
    }


def run_scenario_group(mode: str, n_runs: int) -> tuple[str, list[dict]]:
    """Run all iterations for one scenario and return (mode, runs)."""
    with _print_lock:
        print(
            f"\n{'=' * 50}\nScenario: {mode}  (expected: {EXPECTED[mode]})\n{'=' * 50}",
            flush=True,
        )
    runs = [run_scenario(mode, i) for i in range(n_runs)]
    return mode, runs


def compute_stats(runs: list[dict]) -> dict:
    """Compute summary statistics for a list of run dicts."""
    scores = [
        r["polarization_score"] for r in runs if r["polarization_score"] is not None
    ]
    times = [r["elapsed_seconds"] for r in runs]
    ok = sum(1 for r in runs if r["status"] == "ok")

    def _stats(vals: list[float]) -> dict:
        if not vals:
            return {"n": 0, "mean": None, "std": None, "min": None, "max": None}
        return {
            "n": len(vals),
            "mean": round(statistics.mean(vals), 3),
            "std": round(statistics.stdev(vals), 3) if len(vals) > 1 else 0.0,
            "min": round(min(vals), 3),
            "max": round(max(vals), 3),
        }

    return {
        "score": _stats(scores),
        "elapsed": _stats(times),
        "ok_runs": ok,
        "total_runs": len(runs),
    }


def format_summary(all_runs: dict[str, list[dict]], stats: dict[str, dict]) -> str:
    lines: list[str] = []
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines.append("=" * 72)
    lines.append(f"  Fake Scenario Benchmark — {ts}")
    lines.append("=" * 72)

    header = (
        f"{'Scenario':<20} {'Expected':>10} {'Mean':>8} {'Std':>7}"
        f" {'Min':>7} {'Max':>7} {'Conf':>6} {'OK':>5} {'Avg s':>7}"
    )
    lines.append(header)
    lines.append("-" * 72)

    for mode in SCENARIOS:
        s = stats[mode]
        sc = s["score"]
        el = s["elapsed"]
        name = mode.replace("fake_", "")
        lines.append(
            f"{name:<20} {EXPECTED[mode]:>10}"
            f" {sc['mean']:>8.2f} {sc['std']:>7.2f}"
            f" {sc['min']:>7.2f} {sc['max']:>7.2f}"
            f" {s['ok_runs']:>3}/{s['total_runs']:<2}"
            f" {el['mean']:>7.1f}"
        )

    lines.append("=" * 72)
    lines.append("")
    lines.append("Per-run scores:")
    for mode in SCENARIOS:
        name = mode.replace("fake_", "")
        scores = [
            f"{r['polarization_score']:.1f}"
            if r["polarization_score"] is not None
            else "ERR"
            for r in all_runs[mode]
        ]
        lines.append(f"  {name:<18} {', '.join(scores)}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runs", type=int, default=10, help="Iterations per scenario (default: 10)"
    )
    parser.add_argument(
        "--out",
        type=str,
        default=str(Path(__file__).parent / "results"),
        help="Output directory (default: benchmarks/fake/results)",
    )
    parser.add_argument(
        "--dataset",
        choices=list(DATASETS.keys()),
        default=DEFAULT_DATASET,
        help=(
            "Which dataset variant to benchmark: "
            "'general' (universally understood language, default) or "
            "'fictitious' (FlobberFlopper-specific insults)."
        ),
    )
    parser.add_argument(
        "--scenarios",
        nargs="+",
        choices=SCENARIOS_FICTITIOUS + SCENARIOS_GENERAL,
        default=None,
        help=(
            "Override individual scenarios to run. "
            "When omitted, all scenarios for --dataset are used."
        ),
    )
    args = parser.parse_args()
    active_scenarios = args.scenarios if args.scenarios else DATASETS[args.dataset]

    out_dir = Path(args.out)
    if not out_dir.is_absolute():
        out_dir = _PROJECT_ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    summary_txt_path = out_dir / f"summary_{ts}.txt"

    all_runs: dict[str, list[dict]] = {}

    with ThreadPoolExecutor(max_workers=len(active_scenarios)) as executor:
        futures = {
            executor.submit(run_scenario_group, mode, args.runs): mode
            for mode in active_scenarios
        }
        for future in as_completed(futures):
            mode, runs = future.result()
            all_runs[mode] = runs

    # Compute stats and format summary
    stats = {mode: compute_stats(runs) for mode, runs in all_runs.items()}
    summary_text = format_summary(all_runs, stats)

    print("\n" + summary_text)

    summary_txt_path.write_text(summary_text)
    print(f"Summary txt  → {summary_txt_path}")


if __name__ == "__main__":
    main()
