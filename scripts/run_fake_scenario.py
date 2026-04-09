"""Run each fake scenario once and write a combined txt summary.

Runs fake_polarized, fake_moderate, and fake_neutral through the real LLM
pipeline (Gemini API) and saves a single human-readable summary file in the
same format as data/results/ txt files.

Usage:
    uv run benchmarks/fake/run_fake_scenario.py [--note TEXT]

Output (written to OUT_DIR):
    summary_one_<timestamp>.txt  — one section per scenario
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.internal.pipeline.domain import EvidenceItem, SearchRequest  # noqa: E402
from src.internal.pipeline.llm.run import run_search  # noqa: E402

# ── Configuration ─────────────────────────────────────────────────────────────
OUT_DIR = Path(__file__).parent / "results"

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

SCENARIOS_REAL_CONTEXT = [
    "fake_polarized_real_context",
    "fake_moderate_real_context",
    "fake_neutral_real_context",
]

DATASETS: dict[str, list[str]] = {
    "fictitious": SCENARIOS_FICTITIOUS,
    "general": SCENARIOS_GENERAL,
    "real_context": SCENARIOS_REAL_CONTEXT,
}

DEFAULT_DATASET = "general"

EXPECTED = {
    "fake_polarized_fictitious": "~100",
    "fake_moderate_fictitious": "~35-70",
    "fake_neutral_fictitious": "~0",
    "fake_polarized_general": "~100",
    "fake_moderate_general": "~35-70",
    "fake_neutral_general": "~0",
    "fake_polarized_real_context": "~100",
    "fake_moderate_real_context": "~35-70",
    "fake_neutral_real_context": "~0",
}

def _compute_stance_averages(evidence: list[EvidenceItem]) -> dict[str, dict[str, float]]:
    label_map = {1: "for", -1: "against", 0: "neutral"}
    grouped: dict[str, list[EvidenceItem]] = {"for": [], "against": [], "neutral": []}
    for ev in evidence:
        label = label_map.get(ev.stance)
        if label is not None:
            grouped[label].append(ev)
    averages: dict[str, dict[str, float]] = {}
    for label, items in grouped.items():
        if not items:
            averages[label] = {"sentiment": 0.0, "animosity": 0.0}
        else:
            averages[label] = {
                "sentiment": sum(it.sentiment for it in items) / len(items),
                "animosity": sum(it.animosity for it in items) / len(items),
            }
    return averages


def format_scenario_section(mode: str, result, elapsed: float, note: str | None, model: str | None = None) -> str:
    stance_map = {1: "FOR", 0: "NEUTRAL", -1: "AGAINST"}
    lines: list[str] = [
        "=" * 60,
        f"FAKE SCENARIO — {mode}",
        "=" * 60,
        f"Scenario       : {mode}",
        f"Expected       : {EXPECTED[mode]}",
        f"Assessed at    : {result.collected_at}",
        f"Model          : {model or 'default'}",
        f"Note           : {note}" if note else "Note           : —",
        "",
        "--- Score ---",
    ]

    if result.polarization_score is not None:
        lines.append(f"Polarization   : {result.polarization_score:.2f} / 100")
    else:
        lines.append("Polarization   : N/A")
    lines.append(f"Sample size    : {result.sample_size}")
    if result.rationale:
        lines.append(f"Rationale      : {result.rationale}")
    lines.append(f"Elapsed        : {elapsed:.1f}s")
    lines.append(f"Status         : {result.status}")

    lines += ["", "--- Stance Distribution ---"]
    if result.stance_distribution:
        for key, count in result.stance_distribution.items():
            lines.append(f"  {key.capitalize():<10}: {count}")

    if result.evidence:
        avgs = _compute_stance_averages(result.evidence)
        lines += [
            "",
            "--- Item Averages By Stance ---",
            f"  For      | Sentiment: {avgs['for']['sentiment']:.2f} | Animosity: {avgs['for']['animosity']:.2f}",
            f"  Against  | Sentiment: {avgs['against']['sentiment']:.2f} | Animosity: {avgs['against']['animosity']:.2f}",
            f"  Neutral  | Sentiment: {avgs['neutral']['sentiment']:.2f} | Animosity: {avgs['neutral']['animosity']:.2f}",
        ]

    lines += ["", "--- Source Breakdown ---"]
    if result.source_breakdown:
        for platform, count in sorted(result.source_breakdown.items()):
            lines.append(f"  {platform:<12}: {count}")

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
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--note", default=None, help="Optional note to include in the summary")
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help=(
            "Override POLARIZATION_MODEL for this run. "
            "Provider is detected from the model name prefix: "
            "gpt-* (OpenAI), qwen-* (Qwen), mistral-* (Mistral), "
            "deepseek-* (DeepSeek), gemini-* (Gemini), "
            "anything else (Together AI / OSS)."
        ),
    )
    parser.add_argument(
        "--dataset",
        choices=list(DATASETS.keys()),
        default=DEFAULT_DATASET,
        help=(
            "Which dataset variant to run: "
            "'general' (universal language on fictional topics, default), "
            "'fictitious' (FlobberFlopper-specific insults), or "
            "'real_context' (structurally identical content on real-world topics)."
        ),
    )
    args = parser.parse_args()

    if args.model:
        os.environ["POLARIZATION_MODEL"] = args.model

    active_scenarios = DATASETS[args.dataset]

    out_dir = OUT_DIR if OUT_DIR.is_absolute() else _PROJECT_ROOT / OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    out_path = out_dir / f"summary_one_{ts}.txt"

    all_sections: list[str] = []

    for i, mode in enumerate(active_scenarios, 1):
        print(f"\n[{i}/{len(active_scenarios)}] Running {mode}...", flush=True)
        t0 = time.perf_counter()
        request = SearchRequest(query="benchmark", mode=mode)
        result = run_search(request)
        elapsed = time.perf_counter() - t0

        print(
            f"  score={result.polarization_score:.2f}  status={result.status}  ({elapsed:.1f}s)",
            flush=True,
        )

        section = format_scenario_section(mode, result, elapsed, args.note, model=args.model)
        all_sections.append(section)

    combined = "\n\n".join(all_sections)
    out_path.write_text(combined, encoding="utf-8")
    print(f"\nSummary written → {out_path}")


if __name__ == "__main__":
    main()
