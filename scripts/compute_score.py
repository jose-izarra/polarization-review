#!/usr/bin/env python3
"""Manual polarization score calculator.

Edit scripts/score_config.json with your values, then run:
    python scripts/compute_score.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from src.internal.pipeline.llm.score import compute_polarization
from src.internal.pipeline.llm.types import ItemScore

CONFIG_PATH = Path(__file__).parent / "score_config.json"


def build_item_scores(cfg: dict) -> list[ItemScore]:
    items = []
    for i in range(cfg["n_for"]):
        items.append(ItemScore(id=f"for_{i}", sentiment=cfg["sentiment_for"], stance=1, animosity=cfg["animosity_for"], r=0.0))
    for i in range(cfg["n_against"]):
        items.append(ItemScore(id=f"against_{i}", sentiment=cfg["sentiment_against"], stance=-1, animosity=cfg["animosity_against"], r=0.0))
    for i in range(cfg["n_neutral"]):
        items.append(ItemScore(id=f"neutral_{i}", sentiment=cfg["sentiment_neutral"], stance=0, animosity=cfg["animosity_neutral"], r=0.0))
    return items


def main():
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)

    items = build_item_scores(cfg)
    score = compute_polarization(items)

    n_for, n_against, n_neutral = cfg["n_for"], cfg["n_against"], cfg["n_neutral"]
    total = n_for + n_against + n_neutral

    print(f"\n--- Polarization Score ---")
    print(f"  Score:               {score} / 100")
    print(f"  Breakdown:           {n_for} for / {n_against} against / {n_neutral} neutral  (total {total})")
    print(f"  Sentiment (for/against/neutral): {cfg['sentiment_for']} / {cfg['sentiment_against']} / {cfg['sentiment_neutral']}")
    print(f"  Animosity (for/against/neutral): {cfg['animosity_for']} / {cfg['animosity_against']} / {cfg['animosity_neutral']}")
    print()


if __name__ == "__main__":
    main()
