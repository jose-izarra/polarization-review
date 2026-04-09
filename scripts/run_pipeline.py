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

def load_config(path: Path) -> dict:
    raw = json.loads(path.read_text())
    required = {"query", "runs", "output_dir"}
    missing = required - raw.keys()
    if missing:
        raise ValueError(f"Config missing required fields: {missing}")
    return raw

def _stance_averages_from_evidence(evidence: list[dict]) -> dict[str, dict | None]:
    """Mean sentiment and animosity per stance group (-1 / 0 / 1)."""
    groups = {"for": 1, "against": -1, "neutral": 0}
    result: dict[str, dict | None] = {}
    for name, stance_val in groups.items():
        group = [
            e
            for e in evidence
            if e.get("stance") == stance_val
            and e.get("sentiment") is not None
            and e.get("animosity") is not None
        ]
        if group:
            result[name] = {
                "sentiment": round(statistics.mean(e["sentiment"] for e in group), 2),
                "animosity": round(statistics.mean(e["animosity"] for e in group), 2),
                "n": len(group),
            }
        else:
            result[name] = None
    return result


def _aggregate_stance_across_runs(runs: list[dict]) -> dict[str, dict | None]:
    """Mean of per-run stance-group averages (when multiple runs)."""
    out: dict[str, dict | None] = {}
    for g in ("for", "against", "neutral"):
        s_vals: list[float] = []
        a_vals: list[float] = []
        for r in runs:
            block = (r.get("stance_averages") or {}).get(g)
            if block and block.get("sentiment") is not None:
                s_vals.append(block["sentiment"])
                a_vals.append(block["animosity"])
        if s_vals:
            out[g] = {
                "sentiment": round(statistics.mean(s_vals), 2),
                "animosity": round(statistics.mean(a_vals), 2),
            }
        else:
            out[g] = None
    return out

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
        stance_averages = _stance_averages_from_evidence(evidence)
    else:
        score = None
        sample_size = 0
        rationale = ""
        stance_dist = {"for": 0, "against": 0, "neutral": 0}
        source_breakdown = {}
        evidence = []
        stance_averages = {"for": None, "against": None, "neutral": None}

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
        "stance_averages": stance_averages,
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


def _write_txt(path: Path, query: str,config: dict, runs: list[dict], stats: dict, ts: str) -> None:
    dt_str = datetime.strptime(ts, "%Y-%m-%d_%H-%M-%S").strftime("%Y-%m-%d %H:%M UTC")
    sc = stats["score"]
    el = stats["elapsed"]
    lines: list[str] = []

    lines += [
        "=" * W,
        "  PIPELINE RUN",
        "=" * W,
        f"  Date        : {dt_str}",
        f"  Query       : {query}",
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
        avgs = run.get("stance_averages") or {}
        lines += ["  --- Item Averages By Stance ---"]
        for label in ("For", "Against", "Neutral"):
            key = label.lower()
            a = avgs.get(key)
            if a:
                lines.append(
                    f"    {label:<9}| Sentiment: {a['sentiment']:.2f} | "
                    f"Animosity: {a['animosity']:.2f}"
                )
            else:
                lines.append(f"    {label:<9}| (no items)")
        lines.append("")
        bd = run.get("source_breakdown") or {}
        platforms = bd.get("platforms") or bd  # handle flat or nested breakdown
        if platforms:
            lines.append("  Source Breakdown")
            for platform, count in sorted(platforms.items()):
                lines.append(f"    {platform:<14}: {count}")
            lines.append("")
        # Add items from the run (if present)
        evidence = run.get("evidence", [])
        if evidence:
            lines.append("  Items")
            for idx, item in enumerate(evidence, 1):
                snippet = item.get("snippet", "")[:256].replace("\n", " ")
                stance = item.get("stance", "")
                sentiment = item.get("sentiment", "")
                animosity = item.get("animosity", "")
                url = item.get("url", "")
                lines.append(
                    f"    [{idx}] Stance: {stance} | Sentiment: {sentiment} | Animosity: {animosity}\n"
                    f"         Snippet: {snippet}"
                )
                if url:
                    lines.append(f"         URL: {url}")
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
    if len(runs) > 1:
        agg_st = _aggregate_stance_across_runs(runs)
        lines += ["", "  --- Item Averages By Stance (mean across runs) ---"]
        for label in ("For", "Against", "Neutral"):
            key = label.lower()
            a = agg_st.get(key)
            if a:
                lines.append(
                    f"    {label:<9}| Sentiment: {a['sentiment']:.2f} | "
                    f"Animosity: {a['animosity']:.2f}"
                )
            else:
                lines.append(f"    {label:<9}| (no data)")
        lines.append("")
    lines += ["=" * W, ""]



    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")

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
    txt_path = out_dir / f"summary_{slug}_{ts}.txt"

    _write_txt(txt_path, query, config, runs, stats, ts)

    sc = stats["score"]
    print(f"Report TXT   → {txt_path}")
    if sc["mean"] is not None:
        print(f"\nMean score : {sc['mean']:.2f}  (std={sc['std']:.2f})")
    else:
        print("\nAll runs errored.")


if __name__ == "__main__":
    main()
