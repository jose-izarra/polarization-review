"""Generate a grouped bar chart comparing actual polarization scores
against analytically estimated values across three language variants:
fictitious (FlobberFloppers), general (strong universal language), and
real_context (real-world references: Trump, Carbon Tax, Mardi Gras).

Run from repo root:
    uv run python studies/fake_scenarios/plot_scores.py

Output: studies/fake_scenarios/results/score_comparison.png
"""

from __future__ import annotations

import os
import matplotlib.pyplot as plt
import numpy as np

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

SCENARIOS = ["Polarized\n(King Flavio)", "Moderate\n(Snorf Tax)", "Neutral\n(Wumble Festival)"]

ACTUAL = {
    "fictitious":    [65.46, 41.90, 0.00],
    "general":       [68.72, 36.88, 0.00],
    "real_context":  [68.94, 43.64, 0.00],
}

# Shared analytical estimate across all variants (formula derivation)
ESTIMATED = [70, 40, 0]

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

N = len(SCENARIOS)
x = np.arange(N)

BAR_W   = 0.22
OFFSETS = [-1.0, 0.0, 1.0]   # fictitious, general, real_context

COLORS = {
    "fictitious_act":   "#1A4F72",
    "general_act":      "#B04A0F",
    "real_context_act": "#2E7D4F",
}

LABELS = {
    "fictitious":   "Fictitious",
    "general":      "General",
    "real_context": "Real context",
}

# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor("white")
ax.set_facecolor("white")
for spine in ax.spines.values():
    spine.set_edgecolor("#CCCCCC")

def draw_bars(offset_idx: int, variant: str) -> None:
    positions = x + OFFSETS[offset_idx] * BAR_W
    color = COLORS[f"{variant}_act"]
    label = f"{LABELS[variant]} — actual"
    bars = ax.bar(positions, ACTUAL[variant], BAR_W, color=color, label=label,
                  alpha=0.92, zorder=3, edgecolor="white", linewidth=0.5)
    for b, val in zip(bars, ACTUAL[variant]):
        if val > 0:
            ax.text(
                b.get_x() + b.get_width() / 2,
                b.get_height() + 0.8,
                f"{val:.0f}",
                ha="center", va="bottom",
                fontsize=7.5, color="#333333", fontweight="bold",
            )

for i, variant in enumerate(("fictitious", "general", "real_context")):
    draw_bars(i, variant)

# ---------------------------------------------------------------------------
# Estimated value lines (single shared line per scenario spanning all bars)
# ---------------------------------------------------------------------------

for j, est in enumerate(ESTIMATED):
    if est == 0:
        continue
    left  = x[j] + OFFSETS[0] * BAR_W - BAR_W / 2
    right = x[j] + OFFSETS[-1] * BAR_W + BAR_W / 2
    ax.hlines(est, left, right,
              colors="#555555", linewidths=2.0, linestyles="--",
              zorder=5, alpha=0.85,
              label="Estimated" if j == 0 else "_nolegend_")
    ax.text(right + 0.04, est, f"{est}",
            va="center", fontsize=8, color="#555555", fontweight="bold")

# ---------------------------------------------------------------------------
# Axes styling
# ---------------------------------------------------------------------------

ax.set_xticks(x)
ax.set_xticklabels(SCENARIOS, color="#222222", fontsize=10)
ax.set_yticks(range(0, 101, 10))
ax.set_yticklabels(range(0, 101, 10), color="#444444", fontsize=9)
ax.set_ylim(0, 115)
ax.set_xlim(-0.7, N - 0.25)
ax.set_ylabel("Polarization Score (0–100)", color="#444444", fontsize=10)
ax.tick_params(colors="#CCCCCC", length=0)
ax.yaxis.grid(True, color="#E0E0E0", linewidth=0.5, linestyle="--", zorder=0)
ax.set_axisbelow(True)

ax.set_title(
    "Polarization Score: Actual vs Estimated — Three Language Variants",
    color="#111111", fontsize=12, fontweight="bold", pad=14,
)

ax.text(
    0.5, 1.01,
    "Dashed lines = analytically estimated score from formula derivation",
    transform=ax.transAxes, ha="center", va="bottom",
    fontsize=7.5, color="#777777",
)

ax.legend(
    loc="upper right",
    framealpha=0.9, edgecolor="#CCCCCC",
    labelcolor="#222222", fontsize=8,
    facecolor="white",
)

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

out_dir = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "score_comparison.png")
plt.tight_layout()
plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
print(f"Saved → {out_path}")
plt.close()
