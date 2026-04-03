#!/usr/bin/env python3
"""Manual polarization score calculator.

Edit scripts/score_config.json with your values, then run:
    python scripts/compute_score.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from src.internal.pipeline.domain import ItemScore
from src.internal.pipeline.llm.assess import ALPHA_DEFAULT
from src.internal.pipeline.llm.score import compute_polarization

CONFIG_PATH = Path(__file__).parent / "score_config.json"


def build_item_scores(cfg: dict) -> list[ItemScore]:
    items = []
    for i in range(cfg["n_for"]):
        s, a, st = cfg["sentiment_for"], cfg["animosity_for"], 1
        items.append(
            ItemScore(
                id=f"for_{i}",
                sentiment=s,
                stance=st,
                animosity=a,
                r=st * (s + ALPHA_DEFAULT * a),
            )
        )
    for i in range(cfg["n_against"]):
        s, a, st = cfg["sentiment_against"], cfg["animosity_against"], -1
        items.append(
            ItemScore(
                id=f"against_{i}",
                sentiment=s,
                stance=st,
                animosity=a,
                r=st * (s + ALPHA_DEFAULT * a),
            )
        )
    for i in range(cfg["n_neutral"]):
        s, a, st = cfg["sentiment_neutral"], cfg["animosity_neutral"], 0
        items.append(
            ItemScore(
                id=f"neutral_{i}",
                sentiment=s,
                stance=st,
                animosity=a,
                r=st * (s + ALPHA_DEFAULT * a),
            )
        )
    return items


def main():
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)

    items = build_item_scores(cfg)
    score = compute_polarization(items)

    n_for, n_against, n_neutral = cfg["n_for"], cfg["n_against"], cfg["n_neutral"]
    total = n_for + n_against + n_neutral

    print("\n--- Polarization Score ---")
    print(f"  Score: {score} / 100")
    print(
        f"  Breakdown: {n_for} for / {n_against} against / {n_neutral} neutral"
        f"(total {total})"
    )
    print(
        f"  Sentiment (for/against/neutral): {cfg['sentiment_for']} /"
        f" {cfg['sentiment_against']} / {cfg['sentiment_neutral']}"
    )
    print(
        f"  Animosity (for/against/neutral): {cfg['animosity_for']} /"
        f" {cfg['animosity_against']} / {cfg['animosity_neutral']}"
    )
    print()


if __name__ == "__main__":
    main()
