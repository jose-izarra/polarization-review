"""Run each fake scenario once and write a combined txt summary.

Runs fake_polarized, fake_moderate, and fake_neutral through the real LLM
pipeline (Gemini API) and saves a single human-readable summary file in the
same format as data/results/ txt files.

All parameters are read from run_fake_scenario_config.json (next to this script).

Usage:
    python scripts/run_fake_scenario.py
    python scripts/run_fake_scenario.py --config path/to/other_config.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.internal.pipeline.domain import EvidenceItem, SearchRequest  # noqa: E402
from src.internal.pipeline.llm.run import run_search  # noqa: E402

_DEFAULT_CONFIG = Path(__file__).parent / "run_fake_scenario_config.json"

# ── Scenario definitions ───────────────────────────────────────────────────────

DATASETS: dict[str, list[str]] = {
    "fictitious": [
        "fake_polarized_fictitious",
        "fake_moderate_fictitious",
        "fake_neutral_fictitious",
    ],
    "general": [
        "fake_polarized_general",
        "fake_moderate_general",
        "fake_neutral_general",
    ],
    "real_context": [
        "fake_polarized_real_context",
        "fake_moderate_real_context",
        "fake_neutral_real_context",
    ],
}

EXPECTED: dict[str, str] = {
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
    required = {"dataset", "out_dir"}
    missing = required - raw.keys()
    if missing:
        raise ValueError(f"Config missing required fields: {missing}")
    if raw["dataset"] not in DATASETS:
        raise ValueError(
            f"Invalid dataset {raw['dataset']!r}. "
            f"Choose from: {list(DATASETS.keys())}"
        )
    return raw


# ── Helpers ────────────────────────────────────────────────────────────────────

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


# ── Formatting ─────────────────────────────────────────────────────────────────

def _fmt_scenario_section(mode: str, result, elapsed: float, config: dict) -> str:
    stance_map = {1: "FOR", 0: "NEUTRAL", -1: "AGAINST"}
    note = config.get("note")
    model = config.get("model")

    lines: list[str] = [
        "=" * W,
        f"  FAKE SCENARIO — {mode}",
        "=" * W,
        f"  Scenario       : {mode}",
        f"  Expected       : {EXPECTED[mode]}",
        f"  Assessed at    : {result.collected_at}",
        f"  Model          : {model or 'default'}",
        f"  Note           : {note}" if note else "  Note           : —",
        "",
        "  --- Score ---",
    ]

    if result.polarization_score is not None:
        lines.append(f"  Polarization   : {result.polarization_score:.2f} / 100")
    else:
        lines.append("  Polarization   : N/A")
    lines.append(f"  Sample size    : {result.sample_size}")
    if result.rationale:
        lines.append(f"  Rationale      : {result.rationale}")
    lines.append(f"  Elapsed        : {elapsed:.1f}s")
    lines.append(f"  Status         : {result.status}")

    lines += ["", "  --- Stance Distribution ---"]
    if result.stance_distribution:
        for key, count in result.stance_distribution.items():
            lines.append(f"    {key.capitalize():<10}: {count}")

    if result.evidence:
        avgs = _compute_stance_averages(result.evidence)
        lines += [
            "",
            "  --- Item Averages By Stance ---",
            f"    For      | Sentiment: {avgs['for']['sentiment']:.2f} | Animosity: {avgs['for']['animosity']:.2f}",
            f"    Against  | Sentiment: {avgs['against']['sentiment']:.2f} | Animosity: {avgs['against']['animosity']:.2f}",
            f"    Neutral  | Sentiment: {avgs['neutral']['sentiment']:.2f} | Animosity: {avgs['neutral']['animosity']:.2f}",
        ]

    lines += ["", "  --- Source Breakdown ---"]
    if result.source_breakdown:
        for platform, count in sorted(result.source_breakdown.items()):
            lines.append(f"    {platform:<12}: {count}")

    lines += ["", "  --- Evidence Items ---"]
    for i, ev in enumerate(result.evidence, 1):
        stance_label = stance_map.get(ev.stance, str(ev.stance))
        lines += [
            "",
            f"  [{i}] {ev.platform or 'unknown'} | {ev.source_lean or 'unknown lean'} | Stance: {stance_label} | Sentiment: {ev.sentiment} | Animosity: {ev.animosity}",
            f"       URL      : {ev.url}",
            f"       Rationale: {ev.rationale or '—'}",
            f"       Snippet  : {ev.snippet}",
        ]

    lines.append("")
    return "\n".join(lines)


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default=str(_DEFAULT_CONFIG),
        metavar="PATH",
        help=f"Path to JSON config file (default: {_DEFAULT_CONFIG.name})",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = _PROJECT_ROOT / config_path
    config = load_config(config_path)

    model = config.get("model")
    if model:
        os.environ["POLARIZATION_MODEL"] = model

    active_scenarios = DATASETS[config["dataset"]]

    out_dir = Path(config["out_dir"])
    if not out_dir.is_absolute():
        out_dir = _PROJECT_ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    out_path = out_dir / f"{config['dataset']}_results_{ts}.txt"

    print(
        f"\nFake scenario run\n"
        f"  Dataset  : {config['dataset']}\n"
        f"  Model    : {model or 'default'}\n"
        f"  Scenarios: {', '.join(active_scenarios)}",
        flush=True,
    )
    if config.get("note"):
        print(f"  Note     : {config['note']}", flush=True)
    print()

    all_sections: list[str] = []

    for i, mode in enumerate(active_scenarios, 1):
        print(f"[{i}/{len(active_scenarios)}] Running {mode}...", flush=True)
        t0 = time.perf_counter()
        request = SearchRequest(query="benchmark", mode=mode)
        result = run_search(request)
        elapsed = time.perf_counter() - t0

        print(
            f"  score={result.polarization_score:.2f}  status={result.status}  ({elapsed:.1f}s)",
            flush=True,
        )

        section = _fmt_scenario_section(mode, result, elapsed, config)
        all_sections.append(section)

    combined = "\n\n".join(all_sections)
    out_path.write_text(combined, encoding="utf-8")
    print(f"\nSummary written → {out_path}")


if __name__ == "__main__":
    main()
