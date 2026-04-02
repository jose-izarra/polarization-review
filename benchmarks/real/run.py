"""Real-topic benchmark runner.

Runs the full live pipeline against a curated set of topics known to be either
highly polarized or broadly agreed-upon (consensus).  Results are saved to
benchmarks/real/results/ as JSON + a human-readable .txt report.

Usage
-----
# Run all topics (expensive — hits real APIs and Gemini)
python -m benchmarks.run_real

# Run a single topic by key
python -m benchmarks.run_real --topic abortion

# Print topics and thresholds without hitting any API
python -m benchmarks.run_real --dry-run

# Override output directory
python -m benchmarks.run_real --output-dir /tmp/bench
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.internal.pipeline.llm.run_search import run_search
from src.internal.pipeline.llm.types import SearchRequest

THRESHOLDS: dict[str, dict] = {
    "high_polarization": {"min_score": 50.0, "max_score": None},
    "consensus": {"min_score": None, "max_score": 35.0},
}

class TopicSpec(TypedDict):
    key: str
    query: str
    category: str  # must match a key in THRESHOLDS


TOPICS: list[TopicSpec] = [
    {"key": "abortion", "query": "abortion", "category": "high_polarization"},
    {
        "key": "gun_control",
        "query": "gun control",
        "category": "high_polarization",
    },
    {
        "key": "climate_change",
        "query": "climate change",
        "category": "high_polarization",
    },
    {
        "key": "childhood_vaccines",
        "query": "childhood vaccines",
        "category": "consensus",
    },
    {
        "key": "ai_regulation",
        "query": "ai regulation",
        "category": "consensus",
    },
    {"key": "inflation", "query": "inflation", "category": "consensus"},
]

TOPIC_BY_KEY: dict[str, TopicSpec] = {t["key"]: t for t in TOPICS}

def _threshold_label(category: str) -> str:
    t = THRESHOLDS[category]
    if t["min_score"] is not None:
        return f"> {t['min_score']}"
    if t["max_score"] is not None:
        return f"< {t['max_score']}"
    return "n/a"


def _evaluate(score: float | None, category: str) -> bool:
    if score is None:
        return False
    t = THRESHOLDS[category]
    if t["min_score"] is not None and score < t["min_score"]:
        return False
    if t["max_score"] is not None and score > t["max_score"]:
        return False
    return True


def _score_label(score: float | None) -> str:
    if score is None:
        return "n/a"
    if score >= 70:
        return "very high"
    if score >= 50:
        return "high"
    if score >= 30:
        return "moderate"
    if score >= 10:
        return "low"
    return "very low"


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_topic(spec: TopicSpec) -> dict:
    request = SearchRequest(
        query=spec["query"],
        time_filter="week",
        max_posts=30,
        max_comments_per_post=30,
        mode="live",
    )
    t0 = time.monotonic()
    result = run_search(request)
    elapsed = round(time.monotonic() - t0, 2)

    score = result.polarization_score
    passed = _evaluate(score, spec["category"])

    return {
        "key": spec["key"],
        "query": spec["query"],
        "category": spec["category"],
        "threshold": _threshold_label(spec["category"]),
        "score": score,
        "score_label": _score_label(score),
        "confidence": result.confidence,
        "confidence_label": result.confidence_label,
        "sample_size": result.sample_size,
        "stance_distribution": result.stance_distribution,
        "source_breakdown": result.source_breakdown,
        "status": result.status,
        "error_message": result.error_message,
        "passed": passed,
        "elapsed_s": elapsed,
        "evidence": [asdict(e) for e in result.evidence],
    }


# ---------------------------------------------------------------------------
# Report writers
# ---------------------------------------------------------------------------


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


def _write_txt_report(path: Path, results: list[dict], timestamp: str) -> None:
    dt_str = datetime.strptime(timestamp, "%Y-%m-%d_%H-%M-%S").strftime(
        "%Y-%m-%d %H:%M UTC"
    )
    width = 88
    sep = "=" * width
    thin = "-" * width

    lines: list[str] = [
        sep,
        f"  Real-Topic Benchmark — {dt_str}",
        sep,
        f" {'Topic':<24} {'Category':<20} {'Expected':<10} {'Score':>7}",
        f" {'Label':<12} {'Conf':>6} {'n':>5} {'OK':>5} {'s':>6}",
        thin,
    ]

    for group_label, category in [
        ("High-polarization topics", "high_polarization"),
        ("Consensus topics", "consensus"),
    ]:
        lines.append(f"  {group_label}")
        for r in (r for r in results if r["category"] == category):
            score_str = f"{r['score']:.1f}" if r["score"] is not None else "n/a"
            conf_str = (
                f"{r['confidence']:.3f}" if r["confidence"] is not None else "n/a"
            )
            ok_str = "PASS" if r["passed"] else "FAIL"
            lines.append(
                f"  {r['key']:<22} {r['category']:<20} {r['threshold']:<10} "
                f"{score_str:>7} {r['score_label']:<12} {conf_str:>6} "
                f"{r['sample_size']:>5} {ok_str:>5} {r['elapsed_s']:>6.1f}"
            )
        lines.append("")

    # Stance distribution breakdown
    lines += [thin, "  Stance distribution", thin]
    for r in results:
        dist = r.get("stance_distribution") or {}
        n_for = dist.get("for", 0)
        n_against = dist.get("against", 0)
        n_neutral = dist.get("neutral", 0)
        lines.append(
            f"  {r['key']:<24} for={n_for:>3}  against={n_against:>3}"
            f"  neutral={n_neutral:>3}"
            f"  total={r['sample_size']:>3}"
        )

    lines += ["", sep]

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Real-topic polarization benchmark")
    parser.add_argument(
        "--topic",
        metavar="KEY",
        help=f"Run a single topic by key. Available: {', '.join(TOPIC_BY_KEY)}",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print topics and thresholds without calling any API.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).parent / "results"),
        metavar="DIR",
        help="Directory to write results (default: benchmarks/real/results)",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    output_dir = Path(args.output_dir)

    if args.dry_run:
        print(f"\n{'Key':<24} {'Category':<22} {'Threshold':<12} Query")
        print("-" * 80)
        for spec in TOPICS:
            print(
                f"{spec['key']:<24} {spec['category']:<22} "
                f"{_threshold_label(spec['category']):<12} {spec['query']}"
            )
        print()
        return

    topics_to_run: list[TopicSpec]
    if args.topic:
        if args.topic not in TOPIC_BY_KEY:
            print(
                f"ERROR: unknown topic key '{args.topic}'. "
                f"Available: {', '.join(TOPIC_BY_KEY)}",
                file=sys.stderr,
            )
            sys.exit(1)
        topics_to_run = [TOPIC_BY_KEY[args.topic]]
    else:
        topics_to_run = TOPICS

    timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    results: list[dict] = []

    for i, spec in enumerate(topics_to_run, 1):
        print(f"[{i}/{len(topics_to_run)}] {spec['key']} …", flush=True)
        try:
            row = run_topic(spec)
        except Exception as exc:
            print(f"  ERROR: {exc}", file=sys.stderr)
            row = {
                "key": spec["key"],
                "query": spec["query"],
                "category": spec["category"],
                "threshold": _threshold_label(spec["category"]),
                "score": None,
                "score_label": "n/a",
                "confidence": None,
                "confidence_label": "",
                "sample_size": 0,
                "stance_distribution": None,
                "source_breakdown": None,
                "status": "error",
                "error_message": str(exc),
                "passed": False,
                "elapsed_s": 0.0,
                "evidence": [],
            }
        results.append(row)
        score_str = f"{row['score']:.1f}" if row["score"] is not None else "n/a"
        ok_str = "PASS" if row["passed"] else "FAIL"
        print(
            f"  score={score_str}  conf={row['confidence_label']} "
            f"n={row['sample_size']}  [{ok_str}]"
        )

    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    high_scores = [
        r["score"]
        for r in results
        if r["category"] == "high_polarization" and r["score"] is not None
    ]
    low_scores = [
        r["score"]
        for r in results
        if r["category"] == "consensus" and r["score"] is not None
    ]

    # ── Raw results JSON (includes evidence) ─────────────────────────────
    results_path = output_dir / f"results_{timestamp}.json"
    _write_json(results_path, {"timestamp": timestamp, "results": results})

    # ── Summary JSON (no evidence) ────────────────────────────────────────
    summary_rows = [{k: v for k, v in r.items() if k != "evidence"} for r in results]
    summary = {
        "timestamp": timestamp,
        "pass_rate": f"{passed}/{total}",
        "mean_score_high_polarization": round(sum(high_scores) / len(high_scores), 3)
        if high_scores
        else None,
        "mean_score_consensus": round(sum(low_scores) / len(low_scores), 3)
        if low_scores
        else None,
        "topics": summary_rows,
    }
    summary_json_path = output_dir / f"summary_{timestamp}.json"
    _write_json(summary_json_path, summary)

    # ── Human-readable TXT ────────────────────────────────────────────────
    summary_txt_path = output_dir / f"summary_{timestamp}.txt"
    _write_txt_report(summary_txt_path, results, timestamp)

    print(f"\nResults  → {results_path}")
    print(f"Summary  → {summary_json_path}")
    print(f"Report   → {summary_txt_path}")
    print(f"\nPass rate: {passed}/{total}")
    if high_scores:
        print(
            f"Mean score (high-polarization): {sum(high_scores) / len(high_scores):.1f}"
        )
    if low_scores:
        print(
            f"Mean score (consensus):         {sum(low_scores) / len(low_scores):.1f}"
        )


if __name__ == "__main__":
    main()
