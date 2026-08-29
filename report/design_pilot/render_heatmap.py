# Page 9 flagship exhibit — report-native re-render of the Power BI Python visual.
#
# The plotting body below is the script embedded in the PBIR visual
#   powerbi/.../pages/5c6d7e8f9012a3b4c5d6/visuals/99aabbccddeeff001122/visual.json
# reproduced verbatim. Only the I/O around it differs:
#   · `dataset` is rebuilt here from the governed CSV using the same measure
#     definitions the visual binds to (deltas recomputed from absolute values,
#     never from the rounded *_pct_vs_baseline columns);
#   · figsize matches the slide's exhibit field;
#   · the figure's own title, subtitle, legend and footnote are omitted — the
#     report page supplies them in the approved design language;
#   · plt.show() becomes savefig at print DPI.
# No colour, threshold, norm, padding, glyph or semantic rule is changed.
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm, to_rgb

# a LIST on font.family enables per-glyph fallback; Segoe UI lacks U+2713/2717/25B8
matplotlib.rcParams["font.family"] = ["Segoe UI", "Segoe UI Symbol", "DejaVu Sans"]

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "..", "..", "data", "processed",
                   "consolidated_material_benchmark.csv")
OUTDIR = os.path.join(HERE, "assets")
OUT = os.path.join(OUTDIR, "page09_portfolio_heatmap.png")

FIG_W, FIG_H, DPI = 11.773, 5.00, 300     # slide exhibit field, print resolution


def build_dataset():
    """Reproduce the frame the Power BI visual receives from the semantic model."""
    d = pd.read_csv(CSV)
    base = d[d.sourcing_status == "Current"].set_index("comparison_case_id")
    b_spend = d.comparison_case_id.map(base.annual_spend_eur)
    b_co2 = d.comparison_case_id.map(base.annual_co2e_kg)
    out = pd.DataFrame({
        "comparison_case_id": d.comparison_case_id,
        "material_id": d.material_id,
        "material_group": d.material_group,
        "sourcing_status": d.sourcing_status,
        # [Cost Delta %] / [CO2e Delta %] — recomputed from absolutes, as audited
        "Cost Delta %": (d.annual_spend_eur - b_spend) / b_spend,
        "CO2e Delta %": (d.annual_co2e_kg - b_co2) / b_co2,
        # count measures: 1 or BLANK
        "Technically Eligible Materials": np.where(d.technically_eligible, 1.0, np.nan),
        "Materials with PCF": np.where(d.has_pcf_data, 1.0, np.nan),
        "High Confidence PCF Materials": np.where(
            d.pcf_data_quality_tier == "High confidence", 1.0, np.nan),
        "Oldest PCF Reference Year": d.pcf_reference_year,
    })
    return out


dataset = build_dataset()

# ══════════════════ verbatim from the PBIR python visual ══════════════════
df = dataset.copy()

C_CASE, C_MAT, C_GRP, C_SRC = "comparison_case_id", "material_id", "material_group", "sourcing_status"
C_COST, C_CO2 = "Cost Delta %", "CO2e Delta %"
C_ELIG, C_PCF = "Technically Eligible Materials", "Materials with PCF"
C_CONF, C_YEAR = "High Confidence PCF Materials", "Oldest PCF Reference Year"

for c in (C_COST, C_CO2, C_ELIG, C_PCF, C_CONF, C_YEAR):
    df[c] = pd.to_numeric(df[c], errors="coerce")

df = df.sort_values([C_CASE, C_MAT]).reset_index(drop=True)
n = len(df)

flag = lambda s: s.fillna(0).astype(float)
elig, pcf, conf = flag(df[C_ELIG]), flag(df[C_PCF]), flag(df[C_CONF])

INK, INK_2, INK_3 = "#121A19", "#3A4846", "#7B8B88"
RULE_SOFT, RULE_FIRM = "#DCE4E2", "#9FB0AC"
OK_PALE, OK_TICK = "#EFF6EA", "#8FB39C"
EXC_RED, WARN_AMB = "#D9534F", "#F0A830"
NA_GREY, YR_QUIET = "#F2F4F3", "#FAFBFA"
DIV = LinearSegmentedColormap.from_list("cc", ["#176B44", "#FFFFFF", "#A32E22"])


def mix(c1, c2, t):
    a, b = np.array(to_rgb(c1)), np.array(to_rgb(c2))
    return tuple(a + (b - a) * float(np.clip(t, 0, 1)))


def ink_on(rgb):
    r, g, b = rgb[:3]
    return "#FFFFFF" if (0.299 * r + 0.587 * g + 0.114 * b) < 0.58 else INK


HEADS = ["Cost\nDelta %", "CO₂e\nDelta %",
         "Technical\neligibility", "PCF\navailable", "PCF\nconfidence", "PCF\nreference year"]
WIDTH = [1.60, 1.60, 1.18, 0.86, 0.92, 0.94]
PRIMARY = 2
GAP_X = 0.22
BLOCK_GAP = 0.48

xs, x = [], 0.0
for j, w in enumerate(WIDTH):
    if j == PRIMARY:
        x += GAP_X
    xs.append(x)
    x += w
XTOT = x

norm_cost = TwoSlopeNorm(vmin=-0.16, vcenter=0.0, vmax=0.26)
norm_co2 = TwoSlopeNorm(vmin=-0.56, vcenter=0.0, vmax=0.26)


def delta_cell(v, norm):
    if pd.isna(v):
        return NA_GREY, "n / a", INK_3, "italic", 8.4, "normal"
    rgb = DIV(norm(v))[:3]
    txt = "{:+.2f}%".format(v * 100).replace("+0.00%", "0.00%")
    return rgb, txt, ink_on(rgb), "normal", 9.4, "semibold"


ys, y = [], 0.0
for i in range(n):
    if i and df[C_CASE][i] != df[C_CASE][i - 1]:
        y += BLOCK_GAP
    ys.append(y)
    y += 1.0
YTOT = y

fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), dpi=DPI)
fig.patch.set_facecolor("white")
ax.set_facecolor("white")
ax.set_xlim(0, XTOT)
ax.set_ylim(YTOT, 0)
ax.set_xticks([])
ax.set_yticks([])
for s in ax.spines.values():
    s.set_visible(False)

PAD_P, PAD_S = 0.030, 0.105

for i in range(n):
    row = df.iloc[i]
    yy = ys[i]
    cells = [delta_cell(row[C_COST], norm_cost), delta_cell(row[C_CO2], norm_co2)]

    if elig[i] >= 1:
        cells.append((to_rgb(OK_PALE), "✓", OK_TICK, "normal", 8.6, "normal"))
    else:
        cells.append((to_rgb(EXC_RED), "✗  not approved", "#FFFFFF", "normal", 7.9, "semibold"))

    if pcf[i] >= 1:
        cells.append((to_rgb(OK_PALE), "✓", OK_TICK, "normal", 8.6, "normal"))
    else:
        cells.append((to_rgb(WARN_AMB), "missing", INK, "normal", 7.9, "semibold"))

    if conf[i] >= 1:
        cells.append((to_rgb(OK_PALE), "✓", OK_TICK, "normal", 8.6, "normal"))
    elif pcf[i] >= 1:
        cells.append((to_rgb(WARN_AMB), "low", INK, "normal", 7.9, "semibold"))
    else:
        cells.append((to_rgb(WARN_AMB), "no data", INK, "normal", 7.9, "semibold"))

    yr = row[C_YEAR]
    if pd.isna(yr):
        cells.append((to_rgb(NA_GREY), "n / a", INK_3, "italic", 8.0, "normal"))
    else:
        age = (2023.0 - float(yr)) / 4.0
        old = age > 0.01
        cells.append((mix(YR_QUIET, WARN_AMB, age), "{:d}".format(int(yr)),
                      INK if old else INK_2, "normal", 8.2, "semibold" if old else "normal"))

    for j, (fc, txt, tc, st, fs, fw) in enumerate(cells):
        pad = PAD_P if j < PRIMARY else PAD_S
        ax.add_patch(Rectangle((xs[j] + pad, yy + pad), WIDTH[j] - 2 * pad, 1 - 2 * pad,
                               facecolor=fc, edgecolor="white",
                               linewidth=1.3 if j < PRIMARY else 0.9, zorder=2))
        ax.text(xs[j] + WIDTH[j] / 2, yy + 0.5, txt, ha="center", va="center",
                fontsize=fs, color=tc, style=st, fontweight=fw, zorder=3)

is_base = (df[C_SRC].astype(str).str.strip().str.lower() == "current") if C_SRC in df else pd.Series([False] * n)
for i in range(n):
    inc = bool(is_base[i])
    lab = ("▸  " + str(df[C_MAT][i])) if inc else str(df[C_MAT][i])
    ax.text(-0.08, ys[i] + 0.5, lab, ha="right", va="center", fontsize=8.9,
            color=INK if inc else INK_2, fontweight="semibold" if inc else "normal",
            clip_on=False)

starts = [i for i in range(n) if i == 0 or df[C_CASE][i] != df[C_CASE][i - 1]]
bounds = starts + [n]
LX = -1.42
for b, s in enumerate(starts):
    e = bounds[b + 1]
    top, bot = ys[s], ys[e - 1] + 1.0
    mid = (top + bot) / 2
    ax.add_patch(Rectangle((LX - 0.10, top + 0.06), 0.055, (bot - top) - 0.12,
                           facecolor=RULE_FIRM, edgecolor="none", clip_on=False, zorder=4))
    ax.text(LX, mid - 0.20, str(df[C_CASE][s]), ha="left", va="center",
            fontsize=11.4, fontweight="bold", color=INK, clip_on=False)
    if C_GRP in df:
        ax.text(LX, mid + 0.46, str(df[C_GRP][s]), ha="left", va="center",
                fontsize=8.4, color=INK_3, clip_on=False)
    if b:
        ax.plot([LX - 0.10, XTOT], [top - BLOCK_GAP / 2] * 2, color=RULE_SOFT,
                lw=1.0, clip_on=False, zorder=1)

for j, h in enumerate(HEADS):
    primary = j < PRIMARY
    ax.text(xs[j] + WIDTH[j] / 2, -0.34, h, ha="center", va="bottom",
            fontsize=10.0 if primary else 8.5,
            fontweight="bold" if primary else "semibold",
            color=INK if primary else INK_3,
            linespacing=1.45, clip_on=False)
ax.plot([LX - 0.10, xs[PRIMARY - 1] + WIDTH[PRIMARY - 1]], [0, 0], color=INK, lw=1.6, clip_on=False, zorder=4)
ax.plot([xs[PRIMARY], XTOT], [0, 0], color=RULE_FIRM, lw=1.0, clip_on=False, zorder=4)
ax.plot([LX - 0.10, XTOT], [YTOT, YTOT], color=RULE_SOFT, lw=1.0, clip_on=False, zorder=4)
# ══════════════════ end verbatim block ══════════════════

# chrome supplied by the report page instead of the figure
fig.subplots_adjust(left=0.205, right=0.995, top=0.895, bottom=0.012)

os.makedirs(OUTDIR, exist_ok=True)
fig.savefig(OUT, dpi=DPI, facecolor="white")
print("saved:", OUT)
print("rows:", n, "| cases:", df[C_CASE].nunique(),
      "| px:", int(FIG_W * DPI), "x", int(FIG_H * DPI))
print("missing kept missing —  CO2e n/a:",
      list(df.loc[df[C_CO2].isna(), C_MAT]),
      "| PCF year n/a:", list(df.loc[df[C_YEAR].isna(), C_MAT]))
