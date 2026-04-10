"""
Grouped bar chart: effect of data source on polarization score.
Reads all source_effects JSON result files and saves the chart to results/.
"""

import json
import os
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

RESULTS_DIR = Path(__file__).parent / "results"
OUT_PATH = RESULTS_DIR / "source_effects_grouped_bar.png"

# ── Data extracted from result JSONs ─────────────────────────────────────────
SOURCE_CONFIGS = [
    "reddit_only",
    "gnews_only",
    "youtube_only",
    "reddit + gnews",
    "reddit + youtube",
    "gnews + youtube",
    "all sources",
]

# Keys match JSON label field; display names defined above
JSON_KEYS = [
    "reddit_only",
    "gnews_only",
    "youtube_only",
    "reddit_gnews",
    "reddit_youtube",
    "gnews_youtube",
    "all",
]

TOPICS = {
    "abortion":       [24.15, 0.00, 39.96, 22.19, 33.83, 36.92, 33.15],
    "climate change": [26.79, 0.00, 26.57, 25.37, 30.43, 42.20, 31.38],
    "gun control":    [25.38, 0.00, 44.86, 22.27, 42.69, 43.77, 43.27],
    "inflation":      [15.96, 0.00, 20.08, 15.70, 31.50, 22.33, 24.69],
}

SAMPLE_SIZES = {
    # (topic, config_key) -> sample_size for annotation reference
    "abortion":       [53,  1,  30,  54, 113,  61, 114],
    "climate change": [80,  2,  24,  82, 104,  41, 136],
    "gun control":    [14,  3,  66,  17,  80,  54,  83],
    "inflation":      [35,  3,  25,  38,  60,  28,  78],
}

# ── Colors ────────────────────────────────────────────────────────────────────
COLORS = ["#4C72B0", "#DD8452", "#55A868", "#C44E52"]

# ── Plot ──────────────────────────────────────────────────────────────────────
def main():
    n_configs = len(SOURCE_CONFIGS)
    n_topics = len(TOPICS)
    bar_width = 0.18
    group_gap = 0.08
    group_width = n_topics * bar_width + group_gap
    x = np.arange(n_configs) * group_width

    fig, ax = plt.subplots(figsize=(14, 6))

    topic_names = list(TOPICS.keys())
    for i, (topic, scores) in enumerate(TOPICS.items()):
        offsets = x + (i - n_topics / 2 + 0.5) * bar_width
        bars = ax.bar(
            offsets,
            scores,
            width=bar_width,
            color=COLORS[i],
            label=topic.title(),
            zorder=3,
        )
        # annotate sample size (n=) above each bar, only when n > 1
        sizes = SAMPLE_SIZES[topic]
        for bar, score, n in zip(bars, scores, sizes):
            if score > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    score + 0.5,
                    f"n={n}",
                    ha="center",
                    va="bottom",
                    fontsize=6,
                    color="#444444",
                    rotation=90,
                )
            else:
                # gnews_only always 0 — label above the zero line
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    1.5,
                    f"n={n}",
                    ha="center",
                    va="bottom",
                    fontsize=6,
                    color="#888888",
                )

    # ── Axes formatting ───────────────────────────────────────────────────────
    ax.set_xticks(x)
    ax.set_xticklabels(SOURCE_CONFIGS, fontsize=10)
    ax.set_ylabel("Polarization Score (0–100)", fontsize=11)
    ax.set_title(
        "Effect of Data Source on Polarization Score",
        fontsize=13,
        fontweight="bold",
        pad=14,
    )
    ax.set_ylim(0, 58)
    ax.yaxis.grid(True, linestyle="--", alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Shade the "all sources" group to highlight the baseline
    last_x = x[-1]
    ax.axvspan(
        last_x - group_width / 2,
        last_x + group_width / 2,
        alpha=0.07,
        color="black",
        zorder=0,
    )
    ax.text(
        last_x,
        55,
        "baseline\n(production)",
        ha="center",
        va="top",
        fontsize=8,
        color="#555555",
        style="italic",
    )

    ax.legend(
        title="Topic",
        title_fontsize=9,
        fontsize=9,
        loc="upper left",
        framealpha=0.9,
    )

    fig.tight_layout()
    fig.savefig(OUT_PATH, dpi=180, bbox_inches="tight")
    print(f"Saved → {OUT_PATH}")


if __name__ == "__main__":
    main()
