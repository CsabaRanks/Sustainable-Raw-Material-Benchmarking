"""
Multidimensional benchmark profile — modular, reusable exhibit generator.

Draws the ten success dimensions of this project as a classic engineering
radar: circular web, radial axes, visible concentric assessment levels, thin
unfilled profile lines, dimension labels outside the web.

Reusable by design: `draw_radar()` takes its dimensions and profiles as
arguments, so the paper and the presentation report can call it with different
profiles and get an identical visual language. Nothing in this module is
specific to one document.

Integrity rules enforced here and stated on the figure itself:
  · the ten dimensions are separate and are never aggregated;
  · no weighting, no total, no ranking is computed or implied;
  · profile values are illustrative example values, labelled as such on the
    figure, and are not empirical assessments of any material or supplier.
"""
from __future__ import annotations

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

matplotlib.rcParams["font.family"] = ["Segoe UI", "Segoe UI Symbol", "DejaVu Sans"]

# ── palette ───────────────────────────────────────────────────────────────
INK      = "#14181B"
INK2     = "#3D474D"
INK3     = "#6E7B82"
RULE     = "#C9D1D5"
RULE_LT  = "#E3E8EA"
GREEN    = "#3E8F63"     # benchmark / target profile
RED      = "#B3372C"     # observed profile under assessment
BLACK    = "#14181B"     # second comparison profile

# ── the ten success dimensions of this project ────────────────────────────
DIMENSIONS = [
    "Climate / GHG",
    "Technical performance\nand qualification",
    "Specific legal\ncompliance",
    "Commercial performance\nprice, TCO",
    "Circularity /\nresource loops",
    "Pollution / toxicity",
    "Water",
    "Resource use",
    "Supply-chain\nresilience",
    "Land use /\nbiodiversity",
]

# Illustrative example profiles on a coarse five-level scale. These are NOT
# measurements. They exist to show the shape of the representation only.
PROFILES_DEFAULT = [
    ("Benchmark / target level", [4, 5, 5, 4, 3, 4, 3, 3, 4, 3], GREEN, "-",  "o"),
    ("Observed profile",         [4, 2, 5, 3, 2, 3, 2, 2, 2, 2], RED,   "-",  "s"),
    ("Second comparison",        [3, 5, 5, 2, 4, 3, 3, 3, 3, 2], BLACK, "--", "^"),
]

LEVELS = [1, 2, 3, 4, 5]
LEVEL_LABELS = ["1", "2", "3", "4", "5"]


def draw_radar(dimensions=None, profiles=None, out=None,
               levels=LEVELS, level_labels=None,
               note=("Illustrative example profiles on a five-level scale — "
                     "not empirical assessments.\nThe ten dimensions are separate: "
                     "no weighting, no total score and no ranking is derived."),
               figsize=(8.8, 7.5), dpi=300, title=None, chrome=True):
    """Render the radar and return the output path.

    dimensions : list[str]   axis labels, outside the web
    profiles   : list of (label, values, colour, linestyle, marker)
    chrome     : bool  draw legend and disclaimer inside the figure. Set False
                 for a paper, where both belong in the caption.
    """
    dimensions = dimensions or DIMENSIONS
    profiles = profiles or PROFILES_DEFAULT
    level_labels = level_labels or LEVEL_LABELS
    n = len(dimensions)
    lo, hi = min(levels), max(levels)

    ang = np.linspace(0, 2 * np.pi, n, endpoint=False)
    closed = np.concatenate([ang, ang[:1]])

    fig = plt.figure(figsize=figsize, dpi=dpi)
    fig.patch.set_facecolor("white")
    ax = fig.add_subplot(111, polar=True)
    ax.set_facecolor("white")
    ax.set_theta_direction(-1)
    ax.set_theta_zero_location("N")
    ax.set_ylim(0, hi + 0.35)

    # circular web: concentric assessment levels, deliberately visible
    ax.set_xticks([])
    ax.set_yticks(levels)
    ax.set_yticklabels([])
    ax.spines["polar"].set_visible(False)
    ax.grid(False)
    theta_fine = np.linspace(0, 2 * np.pi, 361)
    for lv in levels:
        ax.plot(theta_fine, np.full_like(theta_fine, lv),
                color=RULE if lv < hi else INK3,
                lw=0.7 if lv < hi else 1.0, zorder=1)
    # radial axes
    for a in ang:
        ax.plot([a, a], [0, hi], color=RULE, lw=0.7, zorder=1)

    # level numbers, once, on the vertical axis
    a_lab = (ang[0] + ang[1]) / 2 if n > 1 else 0.0
    for lv, lab in zip(levels, level_labels):
        ax.text(a_lab, lv, lab, ha="center", va="center", fontsize=7.2,
                color=INK3, zorder=4,
                bbox=dict(boxstyle="square,pad=0.14", fc="white", ec="none"))

    # profiles — thin lines, never filled
    for label, vals, colour, ls, mk in profiles:
        v = np.asarray(vals, dtype=float)
        assert len(v) == n, f"profile '{label}' has {len(v)} values, expected {n}"
        vc = np.concatenate([v, v[:1]])
        ax.plot(closed, vc, color=colour, lw=1.4, ls=ls, zorder=3,
                solid_capstyle="round")
        ax.plot(ang, v, linestyle="none", marker=mk, ms=4.2,
                mfc="white", mec=colour, mew=1.3, zorder=3)

    # dimension labels, outside the web
    for a, lab in zip(ang, dimensions):
        deg = np.degrees(a) % 360
        ha = "center"
        if 10 < deg < 170:
            ha = "left"
        elif 190 < deg < 350:
            ha = "right"
        ax.text(a, hi + 0.50, lab, ha=ha, va="center", fontsize=8.6,
                color=INK, linespacing=1.28, zorder=4, clip_on=False)

    if title:
        fig.text(0.5, 0.972, title, ha="center", va="top", fontsize=11,
                 color=INK, fontweight="semibold")

    if chrome:
        handles = [Line2D([], [], color=c, lw=1.4, ls=ls, marker=mk, ms=4.2,
                          mfc="white", mec=c, mew=1.3, label=lab)
                   for lab, _, c, ls, mk in profiles]
        fig.legend(handles=handles, loc="lower center", ncol=len(profiles),
                   frameon=False, fontsize=8.6, bbox_to_anchor=(0.5, 0.082),
                   handlelength=2.6, columnspacing=2.2)
        fig.text(0.5, 0.024, note, ha="center", va="bottom", fontsize=7.4,
                 color=INK3, linespacing=1.34)
        fig.subplots_adjust(left=0.185, right=0.815, top=0.965, bottom=0.155)
    else:
        fig.subplots_adjust(left=0.185, right=0.815, top=0.975, bottom=0.025)

    out = out or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "fig01_benchmark_profile.png")
    d = os.path.dirname(out)
    if d:
        os.makedirs(d, exist_ok=True)
    fig.savefig(out, dpi=dpi, facecolor="white")
    plt.close(fig)
    return out


if __name__ == "__main__":
    p = draw_radar()
    print("saved:", p)
    print("dimensions:", len(DIMENSIONS), "| profiles:", len(PROFILES_DEFAULT))
