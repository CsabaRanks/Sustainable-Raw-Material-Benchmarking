"""
Paper figures — built natively so the paper does not carry slide bitmaps.

Palette, semantics and restraint follow the frozen design system used by the
presentation report (report/design_pilot/README.md):
  green  = performance improvement      red   = deterioration / blocker
  amber  = evidence weakness            blue  = structure, never a judgement
  grey   = baseline / normal state      blank = missing, never zero

Outputs, numbered by order of appearance in the paper:
  fig01  multidimensional benchmark profile   (make_radar.py)
  fig02  the decision sequence
  fig03  the evidence chain
  fig04  data lineage
  fig05  portfolio screening heatmap          (copied from the prototype re-render)
  fig06  CASE-D cost / carbon quadrant
"""
from __future__ import annotations

import os
import shutil
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrow

matplotlib.rcParams["font.family"] = ["Segoe UI", "Segoe UI Symbol", "DejaVu Sans"]

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DPI = 300

INK, INK2, INK3 = "#14181B", "#3D474D", "#6E7B82"
RULE, RULE_LT = "#D4DADE", "#E8ECEF"
OFFWHITE = "#F7F9FA"
BLUE, BLUE_LT, BLUE_XLT = "#2E5A87", "#BFD2E4", "#E4EDF5"
GREEN, GREEN_LT = "#3E8F63", "#D9EAE0"
RED, RED_LT = "#B3372C", "#F4DFDC"
AMBER, AMBER_LT = "#D99A2B", "#FAECD4"


def _blank(figsize):
    fig = plt.figure(figsize=figsize, dpi=DPI)
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    return fig, ax


def _box(ax, x, y, w, h, fc="white", ec=None, lw=0.8, z=1):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=fc,
                           edgecolor=ec or "none", linewidth=lw, zorder=z))


# ───────────────────────────────── fig02 ─────────────────────────────────
def fig_decision_sequence(out="fig02_decision_sequence.png"):
    """Eligibility -> comparability -> trade-off, each with failure and control."""
    fig, ax = _blank((7.1, 2.62))
    stages = [
        ("01", "ELIGIBILITY", "Can this alternative be considered at all?",
         "An option is compared that cannot legally or technically be bought.",
         "Screen on true constraints first, and keep what was screened out visible."),
        ("02", "COMPARABILITY", "Were these numbers ever comparable?",
         "Two figures are compared that were never calculated on the same basis.",
         "Prove equivalent function, boundary, allocation, period and assurance."),
        ("03", "TRADE-OFF", "What are we giving up, and who owns that call?",
         "One dimension improves while another quietly moves the wrong way.",
         "Hold the dimensions on separate axes and name the decision owner."),
    ]
    w, gap = 0.315, 0.0275
    for i, (num, name, q, fail, ctrl) in enumerate(stages):
        x = i * (w + gap)
        _box(ax, x, 0.02, w, 0.96, fc=OFFWHITE)
        _box(ax, x, 0.955, w, 0.025, fc=BLUE, z=2)
        ax.text(x + 0.026, 0.875, num, fontsize=13, color=BLUE_LT, va="center")
        ax.text(x + 0.026, 0.775, name, fontsize=9.5, color=INK, va="center",
                fontweight="semibold")
        ax.text(x + 0.026, 0.700, _wrap(q, 30), fontsize=7.8, color=INK2,
                va="top", linespacing=1.42)
        ax.plot([x + 0.026, x + w - 0.026], [0.560, 0.560], color=RULE, lw=0.8)
        for lab, txt, col, y_lab, y_txt in [("Failure", fail, RED, 0.500, 0.455),
                                            ("Control", ctrl, GREEN, 0.268, 0.223)]:
            _box(ax, x + 0.026, y_lab - 0.011, 0.012, 0.022, fc=col, z=3)
            ax.text(x + 0.048, y_lab, lab, fontsize=6.6, color=col,
                    fontweight="semibold", va="center")
            ax.text(x + 0.026, y_txt, _wrap(txt, 34), fontsize=7.2,
                    color=INK2, va="top", linespacing=1.42)
        if i < 2:
            ax.text(x + w + gap / 2, 0.50, "›", fontsize=15, color="#A3AFB6",
                    ha="center", va="center")
    return _save(fig, out)


# ───────────────────────────────── fig03 ─────────────────────────────────
def fig_evidence_chain(out="fig03_evidence_chain.png"):
    """One value, three states: bare, qualified, absent."""
    fig, ax = _blank((7.1, 2.55))
    w, gap = 0.315, 0.0275
    heads = [("BARE", AMBER, INK), ("QUALIFIED", GREEN, "white"),
             ("ABSENT", RULE, INK)]
    for i, (state, fc, tc) in enumerate(heads):
        x = i * (w + gap)
        _box(ax, x, 0.02, w, 0.96, fc=OFFWHITE)
        _box(ax, x, 0.90, w, 0.08, fc=fc, z=2)
        ax.text(x + 0.026, 0.94, state, fontsize=8.4, color=tc,
                fontweight="semibold", va="center", zorder=3)

        if i < 2:
            ax.text(x + 0.026, 0.775, "2.4 kg CO$_2$e / kg", fontsize=14,
                    color=INK, va="center")
        else:
            _box(ax, x + 0.026, 0.715, 0.135, 0.115, fc="white", ec=RULE, lw=0.8)
            ax.text(x + 0.0935, 0.7725, "—", fontsize=11, color=INK3,
                    ha="center", va="center")
            ax.text(x + 0.172, 0.7725, "no figure reported", fontsize=7.4,
                    color=INK3, va="center")
        ax.plot([x + 0.026, x + w - 0.026], [0.655, 0.655], color=RULE, lw=0.8)

        if i == 0:
            for j, a in enumerate(["Provenance", "Data quality", "Verification",
                                   "Uncertainty"]):
                yy = 0.565 - j * 0.088
                ax.text(x + 0.026, yy, a, fontsize=7.8, color=INK2, va="center")
                ax.text(x + 0.185, yy, "?", fontsize=8.4, color=AMBER,
                        fontweight="semibold", va="center")
            cap = "A number. Not a measurement."
        elif i == 1:
            for j, (a, v) in enumerate([
                    ("Provenance", "supplier-specific; primary-data share"),
                    ("Data quality", "temporal, geographical, technological"),
                    ("Verification", "third-party assurance performed"),
                    ("Uncertainty", "assessed and reported with the value")]):
                yy = 0.575 - j * 0.092
                ax.text(x + 0.026, yy, a, fontsize=7.2, color=INK,
                        fontweight="semibold", va="center")
                ax.text(x + 0.026, yy - 0.040, v, fontsize=6.8, color=INK2,
                        va="center")
            cap = "The same number, now usable."
        else:
            ax.text(x + 0.040, 0.565, "0", fontsize=14, color=RED,
                    ha="center", va="center")
            ax.plot([x + 0.020, x + 0.060], [0.565, 0.565], color=RED, lw=1.6)
            ax.text(x + 0.078, 0.565, "never", fontsize=8, color=RED,
                    fontweight="semibold", va="center")
            ax.text(x + 0.026, 0.42,
                    _wrap("If absence defaults to zero, the least transparent "
                          "supplier becomes the best performer.", 44),
                    fontsize=7.2, color=INK2, va="top", linespacing=1.45)
            cap = "Missing stays missing."
        ax.text(x + 0.026, 0.075, cap, fontsize=8, color=INK,
                fontweight="semibold", va="center")
    return _save(fig, out)


# ───────────────────────────────── fig04 ─────────────────────────────────
def fig_data_lineage(out="fig04_data_lineage.png"):
    """Three heterogeneous sources through validation to the report."""
    fig, ax = _blank((7.1, 2.5))
    ax.text(0.0, 0.955, "SOURCE SYSTEMS", fontsize=7, color=INK3,
            fontweight="semibold", va="center")
    srcs = [("Procurement", "volume, price, spend, supplier"),
            ("Technical / material", "approval status, properties"),
            ("PCF / sustainability", "kg CO₂e per kg, data type, year")]
    for i, (t, sub) in enumerate(srcs):
        y = 0.79 - i * 0.175
        _box(ax, 0.0, y - 0.058, 0.235, 0.125, fc=OFFWHITE)
        _box(ax, 0.0, y - 0.058, 0.006, 0.125, fc=BLUE, z=2)
        ax.text(0.016, y + 0.021, t, fontsize=7.6, color=INK,
                fontweight="semibold", va="center")
        ax.text(0.016, y - 0.026, sub, fontsize=6.6, color=INK3, va="center")
    _box(ax, 0.0, 0.115, 0.235, 0.115, fc="white", ec=RULE, lw=0.8)
    ax.text(0.016, 0.196, "5 reference tables", fontsize=7.4, color=INK,
            fontweight="semibold", va="center")
    ax.text(0.016, 0.152, "material, supplier, country, case, units",
            fontsize=6.6, color=INK3, va="center")

    steps = [("VALIDATE", "schema, keys,\nranges, duplicates", 0.275),
             ("HARMONISE", "canonical names,\nunit basis, dedup", 0.445),
             ("CONSOLIDATE", "25 rows, one grain,\ndata-quality log", 0.615)]
    for t, sub, x in steps:
        _box(ax, x, 0.35, 0.145, 0.30, fc=BLUE_XLT)
        ax.text(x + 0.0725, 0.575, t, fontsize=7.4, color=BLUE, ha="center",
                fontweight="semibold", va="center")
        ax.text(x + 0.0725, 0.455, sub, fontsize=6.6, color=INK2, ha="center",
                va="center", linespacing=1.5)
    for x0, x1 in [(0.240, 0.272), (0.422, 0.442), (0.592, 0.612), (0.762, 0.772)]:
        ax.annotate("", xy=(x1, 0.50), xytext=(x0, 0.50),
                    arrowprops=dict(arrowstyle="-|>", color=INK3, lw=0.9))
    ax.annotate("", xy=(0.272, 0.50), xytext=(0.240, 0.72),
                arrowprops=dict(arrowstyle="-|>", color=INK3, lw=0.9))
    ax.annotate("", xy=(0.272, 0.50), xytext=(0.240, 0.28),
                arrowprops=dict(arrowstyle="-|>", color=INK3, lw=0.9))

    _box(ax, 0.775, 0.35, 0.135, 0.30, fc=OFFWHITE)
    _box(ax, 0.775, 0.635, 0.135, 0.015, fc=BLUE, z=2)
    ax.text(0.8425, 0.575, "SEMANTIC MODEL", fontsize=7.2, color=INK,
            ha="center", fontweight="semibold", va="center")
    ax.text(0.8425, 0.455, "21 audited measures,\nbaseline and guards",
            fontsize=6.6, color=INK2, ha="center", va="center", linespacing=1.5)
    ax.annotate("", xy=(0.935, 0.50), xytext=(0.915, 0.50),
                arrowprops=dict(arrowstyle="-|>", color=INK3, lw=0.9))
    ax.text(0.942, 0.50, "report", fontsize=7.0, color=INK, va="center")

    ax.plot([0.0, 1.0], [0.075, 0.075], color=RULE, lw=0.8)
    ax.text(0.0, 0.028,
            "Ground truth is held out of the transform and used only by an "
            "independent validation step. Eight data-quality findings are logged; "
            "two are left open by design.",
            fontsize=6.8, color=INK3, va="center")
    return _save(fig, out)


# ───────────────────────────────── fig06 ─────────────────────────────────
def fig_case_d_quadrant(out="fig06_case_d_quadrant.png"):
    """CASE-D on cost and carbon, with the blocked options marked."""
    d = pd.read_csv(os.path.join(ROOT, "data", "processed",
                                 "consolidated_material_benchmark.csv"))
    d = d[d.comparison_case_id == "CASE-D"].copy()
    b = d[d.sourcing_status == "Current"].iloc[0]
    d["c"] = (d.annual_spend_eur - b.annual_spend_eur) / b.annual_spend_eur * 100
    d["g"] = (d.annual_co2e_kg - b.annual_co2e_kg) / b.annual_co2e_kg * 100

    fig = plt.figure(figsize=(3.42, 2.85), dpi=DPI)
    fig.patch.set_facecolor("white")
    ax = fig.add_subplot(111)
    ax.set_facecolor(OFFWHITE)
    ax.set_xlim(-18, 7); ax.set_ylim(-46, 14)
    ax.axhline(0, color=INK3, lw=0.8); ax.axvline(0, color=INK3, lw=0.8)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(labelsize=6.6, colors=INK3, length=0)
    ax.set_xlabel("Cost delta % vs incumbent   (cheaper ←)", fontsize=7,
                  color=INK3, labelpad=3)
    ax.set_ylabel("CO$_2$e delta % vs incumbent   (lower ↓)", fontsize=7,
                  color=INK3, labelpad=3)
    ax.text(-17.2, -3.6, "better on both", fontsize=6.8, color=INK3,
            fontweight="semibold")
    for _, r in d.iterrows():
        blocked = not bool(r.technically_eligible)
        inc = r.sourcing_status == "Current"
        col = INK if inc else (RED if blocked else BLUE)
        ax.plot(r.c, r.g, "o", ms=5.2, color=col, zorder=3)
        ha = "right" if r.c > 2 else "left"
        dx = -0.9 if ha == "right" else 0.9
        ax.text(r.c + dx, r.g + 1.2, r.material_id, fontsize=6.6, color=INK,
                ha=ha, va="bottom", fontweight="semibold")
        if blocked:
            ax.text(r.c + dx, r.g - 3.4, "blocked", fontsize=6.2, color=RED,
                    ha=ha, va="top", fontweight="semibold")
    fig.subplots_adjust(left=0.155, right=0.985, top=0.975, bottom=0.145)
    return _save(fig, out)


# ───────────────────────────────── helpers ───────────────────────────────
def _wrap(t, n):
    out, line = [], ""
    for word in t.split():
        if len(line) + len(word) + 1 > n:
            out.append(line); line = word
        else:
            line = f"{line} {word}".strip()
    out.append(line)
    return "\n".join(out)


def _save(fig, out):
    p = out if os.path.isabs(out) else os.path.join(HERE, out)
    fig.savefig(p, dpi=DPI, facecolor="white")
    plt.close(fig)
    return p


def copy_heatmap(out="fig05_portfolio_heatmap.png"):
    src = os.path.join(ROOT, "report", "design_pilot", "assets",
                       "page09_portfolio_heatmap.png")
    dst = os.path.join(HERE, out)
    shutil.copyfile(src, dst)
    return dst


if __name__ == "__main__":
    for f in (fig_decision_sequence, fig_evidence_chain, fig_data_lineage,
              fig_case_d_quadrant, copy_heatmap):
        print("saved:", os.path.basename(f()))
