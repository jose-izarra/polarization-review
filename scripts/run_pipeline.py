"""Full pipeline runner — config-driven.

Runs the live pipeline (collect → filter → assess → score) for a single query,
repeated `runs` times.  Results are saved to `output_dir` as JSON + TXT.

Usage
-----
    python scripts/run_pipeline.py
    python scripts/run_pipeline.py --config path/to/other_config.json
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.internal.pipeline.domain import SearchRequest
from src.internal.pipeline.llm.run import run_search

_DEFAULT_CONFIG = Path(__file__).parent / "run_pipeline_config.json"

W = 72


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


def load_config(path: Path) -> dict:
    raw = json.loads(path.read_text())
    required = {"query", "runs", "output_dir"}
    missing = required - raw.keys()
    if missing:
        raise ValueError(f"Config missing required fields: {missing}")
    return raw


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_once(request: SearchRequest, model_id: str | None, run_idx: int, n_runs: int) -> dict:
    t0 = time.perf_counter()
    try:
        result = run_search(request)
        status = result.status or "ok"
        error = result.error_message
    except Exception as exc:
        result = None
        status = "error"
        error = str(exc)
    elapsed = time.perf_counter() - t0

    if result is not None:
        score = result.polarization_score
        sample_size = result.sample_size
        rationale = result.rationale or ""
        stance_dist = result.stance_distribution or {"for": 0, "against": 0, "neutral": 0}
        source_breakdown = result.source_breakdown or {}
        evidence = [asdict(e) for e in result.evidence]
    else:
        score = None
        sample_size = 0
        rationale = ""
        stance_dist = {"for": 0, "against": 0, "neutral": 0}
        source_breakdown = {}
        evidence = []

    score_str = f"{score:.2f}" if score is not None else "ERR"
    print(
        f"  run {run_idx + 1}/{n_runs} … score={score_str}"
        f"  n={sample_size}  ({elapsed:.1f}s)",
        flush=True,
    )

    return {
        "run": run_idx + 1,
        "polarization_score": score,
        "sample_size": sample_size,
        "rationale": rationale,
        "stance_distribution": stance_dist,
        "stance_averages": {"for": None, "against": None, "neutral": None},
        "source_breakdown": source_breakdown,
        "elapsed_seconds": round(elapsed, 2),
        "status": status,
        "error": error,
        "evidence": evidence,
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
# Report writers
# ---------------------------------------------------------------------------


def _write_txt(path: Path, config: dict, runs: list[dict], stats: dict, ts: str) -> None:
    dt_str = datetime.strptime(ts, "%Y-%m-%d_%H-%M-%S").strftime("%Y-%m-%d %H:%M UTC")
    sc = stats["score"]
    el = stats["elapsed"]
    lines: list[str] = []

    lines += [
        "=" * W,
        "  PIPELINE RUN",
        "=" * W,
        f"  Date        : {dt_str}",
        f"  Query       : {config['query']}",
        f"  Model       : {config.get('model') or 'default'}",
        f"  Runs        : {config['runs']}",
        f"  Time filter : {config.get('time_filter', 'week')}",
        f"  Max posts   : {config.get('max_posts', 30)}",
        f"  Max comments: {config.get('max_comments_per_post', 30)}",
    ]
    if config.get("note"):
        lines.append(f"  Note        : {config['note']}")
    lines += ["=" * W, ""]

    for run in runs:
        sd = run["stance_distribution"]
        lines += [
            f"  Run {run['run']} of {len(runs)}",
            "  " + "-" * (W - 2),
            f"  Polarization : {f'{run['polarization_score']:.2f} / 100' if run['polarization_score'] is not None else 'N/A'}",
            f"  Sample size  : {run['sample_size']}",
            f"  Elapsed      : {run['elapsed_seconds']}s",
            f"  Status       : {run['status']}",
        ]
        if run.get("error"):
            lines.append(f"  Error        : {run['error']}")
        lines += [
            f"  Rationale    : {run['rationale']}",
            "",
            "  Stance Distribution",
            f"    For        : {sd['for']}",
            f"    Against    : {sd['against']}",
            f"    Neutral    : {sd['neutral']}",
            "",
        ]
        bd = run.get("source_breakdown") or {}
        platforms = bd.get("platforms") or bd  # handle flat or nested breakdown
        if platforms:
            lines.append("  Source Breakdown")
            for platform, count in sorted(platforms.items()):
                lines.append(f"    {platform:<14}: {count}")
            lines.append("")

    lines += [
        "=" * W,
        "  AGGREGATE",
        "=" * W,
    ]
    if sc["mean"] is not None:
        lines += [
            f"  Mean score   : {sc['mean']:.2f}",
            f"  Std dev      : {sc['std']:.2f}",
            f"  Min / Max    : {sc['min']:.2f} / {sc['max']:.2f}",
            f"  Mean elapsed : {el['mean']:.2f}s",
        ]
    else:
        lines.append("  Mean score   : N/A (all runs errored)")
    lines += ["=" * W, ""]

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_json(path: Path, config: dict, runs: list[dict], stats: dict, ts: str) -> None:
    # Strip evidence from the top-level runs to keep the summary compact;
    # evidence is preserved inside each run dict when writing the raw file.
    payload = {
        "config": config,
        "timestamp": ts,
        "runs": {
            config["query"]: [
                {k: v for k, v in r.items() if k != "evidence"} for r in runs
            ]
        },
        "stats": {config["query"]: stats},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_raw_json(path: Path, config: dict, runs: list[dict], stats: dict, ts: str) -> None:
    payload = {
        "config": config,
        "timestamp": ts,
        "runs": {config["query"]: runs},
        "stats": {config["query"]: stats},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default=str(_DEFAULT_CONFIG),
        metavar="PATH",
        help=f"Path to JSON config file (default: {_DEFAULT_CONFIG.name})",
    )
    parser.add_argument(
        "--topic",
        metavar="QUERY",
        help="Override the query from the config file",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = _PROJECT_ROOT / config_path
    config = load_config(config_path)

    query: str = args.topic if args.topic else config["query"]
    n_runs: int = config["runs"]
    model_id: str | None = config.get("model")
    time_filter: str = config.get("time_filter", "week")
    max_posts: int = config.get("max_posts", 30)
    max_comments: int = config.get("max_comments_per_post", 30)

    out_dir = Path(config["output_dir"])
    if not out_dir.is_absolute():
        out_dir = _PROJECT_ROOT / out_dir

    if model_id:
        os.environ["POLARIZATION_MODEL"] = model_id

    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")

    print(
        f"\nPipeline run\n"
        f"  Query  : {query}\n"
        f"  Model  : {model_id or 'default'}\n"
        f"  Runs   : {n_runs}",
        flush=True,
    )
    if config.get("note"):
        print(f"  Note   : {config['note']}", flush=True)
    print()

    request = SearchRequest(
        query=query,
        time_filter=time_filter,
        max_posts=max_posts,
        max_comments_per_post=max_comments,
        mode="live",
    )

    runs: list[dict] = [run_once(request, model_id, i, n_runs) for i in range(n_runs)]
    stats = compute_stats(runs)

    slug = query.lower().replace(" ", "_")
    summary_json = out_dir / f"summary_{slug}_{ts}.json"
    raw_json = out_dir / f"results_{slug}_{ts}.json"
    txt_path = out_dir / f"summary_{slug}_{ts}.txt"

    _write_json(summary_json, config, runs, stats, ts)
    _write_raw_json(raw_json, config, runs, stats, ts)
    _write_txt(txt_path, config, runs, stats, ts)

    sc = stats["score"]
    print(f"\nSummary JSON → {summary_json}")
    print(f"Results JSON → {raw_json}")
    print(f"Report TXT   → {txt_path}")
    if sc["mean"] is not None:
        print(f"\nMean score : {sc['mean']:.2f}  (std={sc['std']:.2f})")
    else:
        print("\nAll runs errored.")


if __name__ == "__main__":
    main()
