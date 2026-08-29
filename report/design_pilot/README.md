# Design Pilot — Visual Design System

**Status: APPROVED AND FROZEN — 2026-08-28.** The cover and main pages 1–3 are
the design reference for the whole report and are not to be redesigned; pages
4–7 (Act II) and 8–12 (Act III) were approved and frozen on the same day. The
deck now contains **all sixteen main pages**; pages 13–16 (Acts IV and V) are
described in §14. Nothing in §§1–13 was changed to accommodate them.

Architecture, action titles, act structure, claim architecture and analytical
logic are taken **verbatim** from the approved report storyline, section
*FINAL APPROVED REPORT ARCHITECTURE* (frozen). Nothing in this folder changes
them.

## Files

| File | What it is |
|---|---|
| `Sustainable_Raw_Material_Benchmarking_Design_Pilot.pptx` | Editable PowerPoint master — cover + all 16 main pages, 17 slides |
| `build_design_pilot.py` | Deterministic generator that produces the `.pptx` |
| `render_heatmap.py` | Re-renders the page 9 flagship exhibit from the Power BI Python visual |
| `assets/page09_portfolio_heatmap.png` | That exhibit, 3531 × 1500 px at 300 dpi |
| `preview/*.png` | Rendered pages for visual review, 2000 × 1125 px — `00`–`03` are the frozen reference renders, `04`–`07` are Act II |

The deck is generated, not hand-drawn. Every geometric value below exists as a
named constant in the generator, so a change to the system is one edit, not
sixteen. Re-run with `python build_design_pilot.py` (requires `python-pptx`).

---

## 1. Page size

**13.333 × 7.5 in — 16:9 landscape**, the PowerPoint widescreen standard.

Chosen over A4 landscape because the flagship exhibit on page 9 is a
13.6 × 9.8 in Matplotlib heatmap to be re-rendered at print DPI, and because the
deck will be read on screen at least as often as on paper. **Consequence to
accept:** printing to A4 landscape leaves a small margin band; it does not clip.

## 2. Grid and margins

| Element | Value |
|---|---|
| Left / right margin | 0.78 in |
| Content width | 11.773 in |
| Act eyebrow, baseline | y = 0.46 |
| Act progress marker | top right, 5 segments of 0.30 × 0.075 in, 0.07 gap |
| Action title | y = 0.74, up to 2 lines |
| Lead paragraph | y = 1.82, width 9.47 in (content width − 2.3) |
| Horizontal rule | y = 2.42, 0.75 pt |
| **Exhibit field** | **y = 2.66 → 6.60, full content width** |
| Source note | y = 6.84, width 10.77 in |
| Page number | y = 6.84, right-aligned at the right margin |

The lead paragraph is deliberately **narrower than the exhibit**. It stops at
9.47 in so the eye returns to the left edge quickly and the exhibit reads as the
wider, more important object.

Every page carries exactly these five zones: **act marker · action title · lead ·
exhibit · source note + page number.** No page adds a sixth zone.

## 3. Fonts

**Segoe UI**, the full family — Light, Semilight, Regular, Semibold.

Chosen because it is present on every Windows machine in the intended audience
(no font substitution when the file is forwarded), it is a humanist sans that
reads as engineering-neutral rather than corporate-marketing, and its four
weights give a hierarchy deep enough that **no italics and no colour are needed
to signal rank**. If the deck must move to a non-Windows environment, substitute
Source Sans 3 or Inter and re-check the line breaks in the action titles.

## 4. Typography hierarchy

| Role | Font | Size | Colour | Notes |
|---|---|---|---|---|
| Cover title | Segoe UI Light | 40 pt | INK | All caps, 3 lines |
| Cover subtitle | Segoe UI Semilight | 15.5 pt | BLUE | Sentence case |
| **Action title** | **Segoe UI Semibold** | **22 pt** | **INK** | **Max 2 lines, spacing 1.06** |
| Act / section marker | Segoe UI Semibold | 8.5 pt | INK3 | All caps |
| Lead paragraph | Segoe UI Regular | 11 pt | INK2 | Max 2 lines, spacing 1.24 |
| Exhibit title | Segoe UI Semibold | 10.5–12 pt | INK | Inside the exhibit field |
| Pull quote | Segoe UI Semilight | 13 pt | INK | Spacing 1.30 |
| Body / label inside exhibit | Segoe UI Regular | 9–10 pt | INK / INK2 | |
| Annotation | Segoe UI Regular | 8.5 pt | INK3 | Legends, cross-references |
| Source note | Segoe UI Regular | 7.5 pt | INK3 | Spacing 1.22 |
| Page number | Segoe UI Semibold | 9 pt | INK3 | |

**7.5 pt is the floor.** Only source notes may use it. Nothing else on any page
goes below 8.5 pt.

**Action titles must dominate.** 22 pt Semibold against an 11 pt Regular lead is
a 2× size step plus a weight step. The title was set at 22 pt rather than larger
so that every one of the 16 approved titles fits on **two lines** at the full
content width — the size is derived from the longest frozen title, not chosen
for looks.

## 5. Colour palette

| Token | Hex | Use |
|---|---|---|
| `INK` | `#14181B` | Primary type, gates, cover spine |
| `INK2` | `#3D474D` | Secondary type, exhibit body |
| `INK3` | `#6E7B82` | Annotations, source notes, page numbers |
| `RULE` | `#D4DADE` | Hairlines |
| `RULE_LT` | `#E8ECEF` | Inactive markers, empty-state dots |
| `PAPER` | `#FFFFFF` | Page ground |
| `OFFWHITE` | `#F7F9FA` | Panel and row-band fill |
| `BLUE` | `#2E5A87` | **Structure and navigation only** |
| `BLUE_LT` | `#BFD2E4` | Class B fill |
| `BLUE_XLT` | `#E4EDF5` | Chip fill |
| `GREEN` | `#3E8F63` | **Performance improvement** |
| `RED` | `#B3372C` | **Deterioration / blocker** |
| `AMBER` | `#D99A2B` | **Evidence weakness / uncertainty** |

The neutrals carry a slight blue bias so they sit with `BLUE` rather than fight
it.

## 6. Semantic colour rules — binding

Inherited from the Power BI prototype so that the report and the live dashboard
read as one system:

- **green = performance improvement**
- **red = deterioration or a hard blocker**
- **amber = evidence weakness or uncertainty**
- **neutral grey = baseline / normal state**
- **blue = structure and navigation, never a performance judgement**

Four consequences, enforced in the generator:

1. Green, red and amber are **never** used decoratively. On page 1 they mark
   *Failure* and *Control*; on the cover they encode the sign of the synthetic
   cost delta, and the caption says so in words.
2. The A–E dimension classes on page 3 are keyed in the **blue and ink family**,
   never green/red/amber — a classification is not a performance verdict, and
   green for "core" would collide with green for "improvement".
3. A missing value is rendered **blank**. It is never zero-filled and never given
   a colour. This is the same rule the prototype enforces in DAX, in conditional
   formatting and in the Python heatmap.
4. Amber appears only where evidence quality is actually at issue. It was removed
   from the cover during the pilot because nothing on the cover explains it.

## 7. Component styles

**Action title.** Segoe UI Semibold 22 pt, INK, left-aligned at the left margin,
line spacing 1.06, no terminal punctuation. Line breaks are set manually so both
lines are near-balanced — never left to auto-wrap.

**Exhibit title.** Segoe UI Semibold 10.5 pt, INK, with a 1.0 pt INK rule beneath
it spanning the column. Used for column and section heads inside the exhibit
field. An exhibit never repeats the action title.

**Source note.** Segoe UI Regular 7.5 pt, INK3, bottom left, wrapping to at most
three lines. Format: `Author, Title (year), locator`, items separated by ` · `.
It names the standard and the section, not just a URL. Where a claim is not a
plain fact it says so — `project synthesis`, `source-supported interpretation`,
`emphasis added`.

**Annotation.** Segoe UI Regular 8.5 pt, INK3, with the operative words in
Semibold INK2. Used for legends and forward references.

**Page number.** Segoe UI Semibold 9 pt, INK3, right-aligned, baseline shared
with the source note. **The cover is not numbered.** Main pages run 1–16;
appendices are lettered separately. Cover and contents are not counted.

**Table style.** No vertical rules and no outer box. A 1.0 pt INK rule under the
column headers, a 0.75 pt RULE line under the last row, OFFWHITE banding on
alternate rows. Row height 0.27 in, row text 9.5 pt. Column heads are 8 pt
Semibold INK3, all caps. Numbers right-aligned, labels left-aligned.

**Chart / exhibit style.** Direct labels, never a legend, wherever the label fits
next to the mark. No gridlines unless a value must be read off an axis. No 3-D,
no shadows, no gradients, no rounded corners — every shape in the pilot has its
shadow explicitly disabled. Panels are OFFWHITE fills with a 0.035 in BLUE top
edge and no border. A category legend is used only where marks repeat across many
rows (page 3), and it sits below the exhibit, never beside it.

**Icon policy: no icons.** No pictograms, no leaf marks, no stock photography, no
illustration. The only non-typographic elements permitted are filled squares and
circles used as data marks, hairlines, filled panels, and the `›` chevron used to
show sequence. If a concept needs an icon to be understood, the wording is wrong.

**Whitespace rules.** The exhibit field is 3.94 in tall and **is not required to
be filled** — page 1 uses 3.16 in of it, and page 2 leaves a deliberate gap above
the methods strip. Minimum 0.55 in between the last exhibit element and the
source note. Minimum 0.24 in gutter between exhibit columns; 0.57 in between the
three panels on page 1. Nothing is centred on the page except text inside a cell
that is itself a mark.

---

## 8. Design concept

**The screening line.** The report argues that a defensible decision is a
*sequence* — screen, then compare, then trade off. The visual system says the
same thing structurally rather than decoratively:

- A **five-segment act marker** sits top right on every page. The current act is
  filled in BLUE, the rest in RULE_LT. The reader always knows how far through
  the argument they are, and the marker costs 0.075 in of vertical space.
- A **single hairline** under the lead separates *what we claim* from *what
  proves it*. Above the line is language; below it is evidence.
- The **cover mark** is a 5 × 5 field — five benchmark cases by five material
  alternatives — tinted by the sign of the synthetic cost delta. It is the
  dataset's actual shape rather than an abstract pattern, and it foreshadows the
  page 9 portfolio heatmap. The caption states what the colours mean.

The palette is restrained on purpose: an analytical near-black on white, one
structural blue, and three semantic colours spent only where they carry meaning.
There is no hero image, no gradient, no card shadow and no illustration anywhere
in the deck.

## 9. Exhibits in this pilot

| Page | Action title (frozen) | Dominant exhibit |
|---|---|---|
| Cover | — | 5 × 5 material-screening mark + synthetic-data disclosure |
| 1 | *No raw material is universally sustainable — a defensible decision proves eligibility, then comparability, then shows the trade-off* | Three-stage decision flow: **ELIGIBILITY › COMPARABILITY › TRADE-OFF**, each with its question, its failure mode (red) and its control (green) |
| 2 | *Carbon is the dimension we measure best — and the carbon standard itself says it is not the whole answer* | The GHG Protocol §1.7 limitation clause as a full-width pull quote, split below into *what the number covers* / *what it is silent on*, closed by a methods strip |
| 3 | *Which dimensions matter depends on the material, its feedstock and its origin — not on a universal checklist* | Materiality matrix: ten decision dimensions × four context drivers, each row carrying its frozen A–D class |

**Note on the page 3 exhibit form.** The blueprint describes this page's exhibit
as a matrix carrying the frozen A–E classification. The frozen research
classifies at *topic* level, not topic × material-category, so a matrix with the
five synthetic categories as columns could only have been filled by inventing
per-category judgements. The columns are therefore the **four context drivers the
action title itself names** — material, feedstock, origin, application — which is
what the research does support and what the title actually claims. The
classification column is unchanged. **This is a design decision inside
production, not an architecture change, and it is flagged here for review.**

---

## 10. Decisions to freeze if the pilot is approved

1. Page size 13.333 × 7.5 in, 16:9.
2. Margins 0.78 in and the five-zone grid, including the exhibit field at
   y = 2.66 → 6.60 on every one of the 16 pages.
3. Segoe UI across four weights; Source Sans 3 / Inter as the only sanctioned
   substitutes.
4. The full type scale in §4, and the 7.5 pt floor reserved for source notes.
5. The palette in §5 with its exact hex values.
6. **The semantic colour rules in §6 — the hardest of the frozen decisions.**
   Green, red and amber may not be used decoratively anywhere in the report, and
   a missing value stays blank.
7. Action title at 22 pt Semibold, two lines, manual line breaks.
8. The five-segment act marker, top right, on all 16 pages.
9. The no-icon policy.
10. Table style: no vertical rules, header rule 1.0 pt INK, OFFWHITE banding.
11. Source-note format, including the explicit `project synthesis` /
    `source-supported interpretation` / `emphasis added` markers.
12. Page numbering: cover unnumbered, main pages 1–16, appendices lettered.
13. Exhibits are generated from a script, so the system stays reproducible and a
    late change to a shared value propagates to every page.

## 11. Known limitations

- `build_design_pilot.py` contains an **absolute output path**. It should be made
  relative before the file is committed.
- Rendering to PNG uses PowerPoint COM automation on Windows. There is no
  cross-platform renderer in this environment.
- Line breaks in the action titles are hand-set for Segoe UI at 22 pt. Changing
  the font or the size requires re-checking every break.
- The pilot covers 4 of 20 surfaces. Exhibit types not yet exercised: the page 9
  Matplotlib re-render, prototype screenshots (pages 8, 10, 11), and the
  evidence-strength markers on page 5.

---

## 12. Act II — main pages 4–7 (added after approval)

Four consecutive methodology pages are the section most likely to read as a
wall of text. The frozen architecture answers that with **four different
rhetorical modes inside one visual grammar**, and a hard body-text budget per
page. Every element below is built from the components already defined in
§§4–7; **no new colour, type size, shape or rule was introduced.**

| Page | Mode | Dominant exhibit | Budget |
|---|---|---|---|
| **4** | Conceptual architecture | Four decision-role bands — role · question · behaviour — with two right-hand insets: *the role is set by the decision rule* and *what is, and is not, a gate* | ≤ 110 words |
| **5** | Best-practice sequence | Five-step sequence SCREEN › COMPARE › QUALIFY › DECIDE › RECORD with the thirteen practices attached and three-state evidence markers; closed by a dark action band | ≤ 140 words |
| **6** | Comparability test | Supplier A / struck equals / Supplier B above the six §A.1 conditions in a 2 × 3 grid, closed by the three-state verdict | ≤ 110 words |
| **7** | Evidence chain | The same value three times — bare · qualified · absent — as three equal panels | ≤ 100 words |

Read left to right the section carries one sequence: **structure the decision →
apply the practices → prove comparability → keep the evidence visible.**

### Semantic-colour decisions taken on these pages

These four are the precedents for the rest of the report:

1. **The decision-role colours on page 4 are the page-3 class colours**, reused
   exactly: Gate = `INK` (page 3 class C), Performance = `BLUE` (class A),
   Evidence = `AMBER`, Context = `RULE` (class D). A role marker is a
   classification, never a performance judgement.
2. **The evidence marker on page 5 is a shape, not a colour** — filled `INK`,
   filled `INK3`, hollow. Evidence strength must not compete with the
   green/red/amber performance semantics, and a colour ramp would read as a
   score. Three states, no numbers, no maturity model.
3. **The page-6 verdict chips are the one place amber carries comparability**
   rather than data confidence: comparable `GREEN_LT`, conditionally comparable
   `AMBER_LT`, not comparable `RED_LT`. Conditional comparability is an evidence
   condition, so amber is correct.
4. **On page 7 the ABSENT panel is deliberately neutral, not red.** Missing data
   is a state, not a failure; colouring it would contradict the rule the page
   states. Red appears only on the struck `0` — the error being warned against.
5. **The struck equals on page 6 and the struck zero on page 7 are drawn as
   shapes, not typeset glyphs.** Font metrics cannot place a strike reliably
   across renderers; both were visibly wrong when typeset and were rebuilt as
   rectangles plus a connector.

### Consequences for pages 8–16

- The dark full-width action band introduced on page 5 is now available as a
  component for any page that must state what the reader should do. Use it
  sparingly — at most one per act.
- Amber on a *value* means evidence weakness; amber on a *verdict* means
  conditional. Both are in play from page 6 onward, so a caption must always
  say which reading applies.
- Pages 4–7 use no prototype data and carry no synthetic-data label. From
  page 8 the label is mandatory on the page and in every caption.

---

## 13. Act III — main pages 8–12 (the prototype demonstration)

Act III demonstrates the method on the existing synthetic Power BI prototype.
It introduces no new methodology, no score, no ranking and no weight, and it
keeps each benchmark case a separate decision.

| Page | Mode | Dominant exhibit |
|---|---|---|
| **8** | Prototype scope | The portfolio-total correction — 4,073,400 € struck through, 820,000 € stated — beside the case structure, the coverage KPIs, and a *shows / does not show* strip |
| **9** | **Flagship** | The full portfolio screening heatmap, all 25 materials, edge to edge |
| **10** | Worked case — eligibility | CASE-D cost/carbon quadrant with the two blocked options marked, beside the eligibility record |
| **11** | Worked case — evidence | CASE-C evidence table with SF-3002 amber-banded and SF-3003 blank, plus two callouts |
| **12** | Scope boundary | The six §A.1 conditions from page 6 scored against the prototype, with the field that would close each |

### The synthetic-data boundary

From page 8 the boundary is stated three times on every page: a bordered
`SYNTHETIC DEMONSTRATION DATA` chip beside the act marker, the same words
opening the source note, and — on pages 8 and 12 — a *what it does not show*
statement inside the exhibit. This is not optional on any Act III page.

### Page 9 — how the flagship exhibit is produced

`render_heatmap.py` reuses the plotting body of the Power BI Python visual
**verbatim**. Only the I/O around it differs:

- `dataset` is rebuilt from `data/processed/consolidated_material_benchmark.csv`
  using the same measure definitions the visual binds to. **The deltas are
  recomputed from absolute spend and CO₂e, never taken from the rounded
  `*_pct_vs_baseline` columns** — those carry one decimal (6.2 %) where the
  audited measure gives 6.25 %.
- `figsize` matches the slide's exhibit field; the figure's own title, subtitle,
  legend and footnote are dropped because the report page supplies them in the
  approved design language.
- `plt.show()` becomes `savefig` at 300 dpi.

No colour, threshold, norm, padding, glyph or semantic rule was changed. Two
technical points worth keeping:

1. **Font fallback needs a list on `font.family`, not on `font.sans-serif`.**
   Segoe UI has no U+2713 ✓, U+2717 ✗ or U+25B8 ▸; with the wrong rcParam the
   figure rendered three columns of tofu boxes.
2. The heatmap's native aspect is far squarer than a 16:9 slide, so page 9 uses
   a **compressed header** — act marker, action title, legend strip, exhibit,
   source note, and no lead paragraph. It is the only page permitted to omit the
   lead.

### Semantic decisions taken in Act III

1. **Missing stays missing, in every representation.** SF-3003 is `n / a` in the
   heatmap, a short grey rule in the page 11 table, and absent from the CO₂e
   comparison — never zero, never a worse performer, and never removed from the
   cost comparison.
2. **Blocked options stay on the page.** PA-4002 and PA-4004 are plotted, listed
   and coloured red on page 10. Screening removes an option from the comparison,
   not from the record.
3. **Page 12 has no green.** No §A.1 condition is fully satisfied, so only amber
   `partial` and neutral `not shown` appear. Inventing a green would be the
   exact failure the page is about.
4. **Blue marks eligible-but-unremarkable points on page 10**, not good
   performance. Green and red stay reserved for the delta values themselves,
   which the heatmap already carries.

---

## 14. Acts IV and V — main pages 13–16

The closing block widens the argument beyond carbon and then hands it over. It
introduces no new methodology and adds no maturity model, score, ranking,
weighting or composite index.

| Page | Act | Dominant exhibit |
|---|---|---|
| **13** | IV | Two registers — climate, where recycling wins in all 27 pathways, above the five impact categories where energy-intensive routes lose, with the named routes beneath |
| **14** | IV | The trade-off map: eight tensions × how it shows up · evidence marker · handling rule, closed by a dark *deliberately rejected* band |
| **15** | V | Ownership band beside the one-page decision record, with the qualification pipeline as a second output |
| **16** | V | Three columns — build now, build where material, do not build — over a footer that separates research limitations from implementation prerequisites |

### Decisions taken in this block

1. **Page 13 carries its scope limit inside the exhibit, not in a footnote.** The
   amber band at the top of the exhibit field states that JRC132067 is a
   plastics waste-treatment study and is not evidence about the five material
   groups in this report. The frozen research requires the label to be on the
   page; putting it in the source note would not satisfy that.
2. **Page 13 never maps a category to a route one-to-one.** The source names five
   impact categories and separately names five energy-intensive routes. The
   exhibit keeps them as two rows joined by a sentence, because the assessment
   does not license a cell-by-cell claim.
3. **Page 14 reuses the page 5 evidence marker unchanged** — same three shapes,
   same legend wording. A second scale would have implied a second, unsourced
   judgement. Cost ↔ carbon is the one hollow marker on the page, because its
   quantitative figures are steel-sector illustration only.
4. **The dark action band appears twice in the deck**, on pages 5 and 14 — one
   per act, as §12 provides. On page 14 it carries what the report refuses to
   build, which is a conclusion, not a call to action.
5. **Page 15 carries the project-synthesis chip** in the same position as the
   synthetic-data chip on Act III pages. ISO 20400 supports the principle; it
   does not validate this artefact, and the page says so twice.
6. **Page 16 states its limitations at the same type size as its recommendations.**
   The footer gives research limitations and implementation prerequisites equal
   width, so that the absence of an industrial case reads as a bounded scope
   rather than a defect.

---

## 15. Full-report QA pass — 2026-08-28

All 17 slides were audited structurally (against the generated `.pptx`, not the
source), numerically (against the governed dataset), and visually.

**One substantive correction.** The page 10 action title read "The two strongest
alternatives in **the portfolio**…". PA-4002 supports that reading — it has the
largest cost improvement of all 25 options and is dominated on neither axis. PA-4004
(−7.14 % / −16.67 %) does not: BO-1002 (−12.50 % / −20.00 %) is better on both axes
and is technically eligible. "In the portfolio" was also a cross-case claim, which
page 9 explicitly disclaims. Corrected on approval to **"in this case"**, with the
line break rebalanced to 43 / 36 characters. **The frozen storyline still carries
the original wording in its action-title list and its final page table** — the deck
and the storyline now differ on this one title.

**Seven further corrections, all mechanical.** Percentage setting standardised to no
space before `%` on pages 8, 10 and 11 — pages 10 and 11 each carried the same
figure twice with different spacing. Page 15's own-voice header changed from
"comparison case" to "benchmark case", matching the cover and page 8; the BP-11
citation in its source note keeps the source's wording. Page 10's y-axis caption
was moved 0.08 in right, onto the left margin it had been sitting outside of.
Three text frames on pages 3, 9, 10 and 11 were trimmed to stop at the margin —
their rendered text was already inside.

**A pixel diff against the pre-QA render confirms the cover and pages 1–7, 9,
12–14 and 16 are byte-identical.** Only the four intended regions changed.

### Standing conventions confirmed by the audit

- Act marker: five segments on every main page, exactly one filled, correct act.
- Page numbers 1–16 in order; the cover is unnumbered.
- 7.5 pt floor holds on all 17 slides; only source notes use it.
- No font outside the Segoe UI family.
- Every occurrence of *score*, *ranking*, *weighting* or *maturity* is a negation
  or a quotation — there is no accidental scoring language anywhere.
- `SYNTHETIC DEMONSTRATION DATA` appears on pages 8–12 and nowhere else, which is
  correct: pages 13–16 use no prototype data.
- Every cross-page reference resolves to the right page.
