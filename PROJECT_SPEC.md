# Project Specification — Sustainable Raw Material Benchmarking (v0.1)

## Purpose

This is a public, portfolio-oriented demonstration project. It shows how a
company could compare technically suitable supplier/material alternatives for
a purchased raw material, looking jointly at **cost** and **Product Carbon
Footprint (PCF)**.

All data in this repository is **synthetic**. No real company, supplier,
tender, or proprietary information is contained here or should ever be added.

### Portfolio context

Alongside the technical use case, this repository is a public portfolio
piece. It demonstrates — generically, through the quality of the use case,
data model, validation logic, analytics, and documentation, not by naming
anyone — capabilities relevant to industrial digitalization and
chemical raw-material data work: consolidating and harmonizing heterogeneous
data sources, spotting and handling data inconsistencies, master-data
transparency, and deriving robust decision support from imperfect data
across functions like Procurement, R&D, Master Data, and Sustainability.

This repository must **not** name or target any specific employer (past,
present, or prospective), must not use any company's name, logo, proprietary
process, or confidential information, and must not attempt to reproduce any
specific company's internal raw-material approval process. It stays a
generic, credible industrial demonstrator.

## Use Case

A company currently purchases a chemical raw material from one supplier and
wants to compare technically suitable alternatives (other suppliers and/or
other materials that fulfill the same technical function).

### Key decision question

> Which technically suitable material/supplier alternative improves the
> current sourcing situation, and what trade-off between cost and carbon
> footprint must be accepted?

### Core data fields (v0.1)

- material / supplier
- annual volume
- price per kg
- annual spend
- Product Carbon Footprint (PCF), kg CO2e/kg
- annual CO2e
- technical approval status
- PCF data quality

### Technical qualification as a gate, not a ranking factor

`technical_approval_status` is a binary precondition, not a factor combined
with cost or carbon. Only alternatives with status `Approved` (plus the
`Current` baseline itself) are ever treated as valid sourcing options in
cost/CO2e comparisons — this is enforced by a calculated
`technically_eligible` flag applied *before* any cost/carbon comparison
logic runs. Alternatives that are `Under Qualification` or `Not Approved`
remain visible in the dataset for transparency (e.g. "a cheaper option
exists but isn't approved yet") but are excluded from being presented as a
valid current choice. This is a hard filter, never a weight or score.

### Questions the dashboard should help answer

1. Which alternative has the lowest annual material cost?
2. Which alternative has the lowest annual carbon footprint?
3. How do cost and CO2 change versus the current solution?
4. Are there alternatives that improve both cost and PCF?
5. How reliable is the underlying PCF data?

## Methodological Principle

- **PCF is not equivalent to sustainability.** It is only one observable
  sustainability indicator.
- **Price is not equivalent to total cost competitiveness.**
- Version 0.1 must **not** create an overall sustainability score or a
  weighted supplier ranking. Cost and carbon are shown side by side, not
  combined into a single index.
- Technical properties (e.g. viscosity, purity, active content) are
  **material-group-specific and never compared across groups.** No generic
  numerical technical property is ever interpreted as "better" — these
  fields describe fitness-for-use within a group, not a cross-group ranking
  dimension.

## Data Capability Chain

Beyond the Cost-vs-Carbon analysis itself, v0.1 is meant to eventually
demonstrate a small, realistic data-quality / harmonization step, since that
is as central to the portfolio purpose as the analysis:

```
heterogeneous source data
  → validation
  → harmonization
  → consolidated raw-material dataset
  → data-quality transparency
  → analytical KPIs
  → Power BI visualization
  → fact-based material / supplier decision
```

Reference/mapping tables (see Data Model below) belong to this
harmonization step, not to any raw source:

```
Procurement ─┐
Technical ───┼─> validation/harmonization -> consolidated analytical dataset
PCF ─────────┘                 ↑
                         reference/mapping
```

- `data/` is expected to later distinguish **raw source data** (deliberately
  imperfect, synthetic) from a **consolidated dataset** (validated/
  harmonized) — the exact subfolder split will be decided at implementation
  time.
- Harmonization/validation logic, when it exists, stays simple and explicit
  (e.g. a small script or notebook cleaning known issues, using the small
  reference tables below) — not a generic rules engine or framework.
- PCF data quality is already a core field and doubles as the visible output
  of this pipeline in the dashboard.

## Data Model (v0.1 — approved)

Three raw sources, one shared canonical business key
(`material_id`, `supplier_id`), one small reference/mapping layer, one
consolidated analytical table. No fourth raw source.

### Material groups (approved)

1. Base Oils
2. Solvents
3. Surfactants
4. Polymer Additives
5. Resins / Binders

Generic synthetic categories — no reference to any specific company's
formulations, products, or internal material portfolio. Exactly 5 supplier/
material alternatives per group (25 records total), one `Current` +
4 `Alternative` per group, deliberately varied decision patterns
(cost winner, carbon winner, win-win, genuine trade-off, questionable PCF
data quality).

### Comparison case (functional/specification fit)

**Logical decision sequence:** candidate material/grade → functional/
specification fit → technical qualification → technically eligible sourcing
alternatives → Cost/PCF/data-quality comparison → decision support.
Technical suitability must never be implicitly compensated by an attractive
cost or PCF value — this is why *functional/specification fit* is modeled
as its own explicit step, upstream of qualification and cost/PCF comparison.

A **comparison case** is one functional raw-material requirement for which
several supplier grades are evaluated as direct substitutes. Alternatives
are only ever compared *within* the same comparison case — never across
functionally different materials (e.g. a base oil viscosity grade must
never be casually compared against a different viscosity grade, and an
antioxidant package must never be compared against a UV stabilizer). For
v0.1 there are exactly 5 comparison cases, one per material group (1:1 for
this version; the model does not assume that will always hold):

| Case ID | Material group | Functional requirement | Specification window |
|---|---|---|---|
| `CASE-A` | Base Oils | Group II base oil for lubricant/metalworking-fluid blending | 150N viscosity grade (≈32 cSt @ 40°C), Group II |
| `CASE-B` | Solvents | Isopropanol (IPA) as an industrial cleaning/process solvent | Technical/industrial grade, ≥99.5% purity |
| `CASE-C` | Surfactants | Nonionic surfactant for detergent/cleaning formulation | Fatty alcohol ethoxylate, C12–14, 6–9 mol EO |
| `CASE-D` | Polymer Additives | Primary antioxidant package for polyolefin compound stabilization | Phenolic/phosphite-type antioxidant blend |
| `CASE-E` | Resins / Binders | Water-based binder for coating/adhesive formulation | Acrylic resin dispersion, 48–52% solids |

Each supplier grade still has its own `material_id`/`supplier_id` — the
comparison case does not replace that key, it scopes which alternatives are
allowed to be compared against each other.

### Source 1 — `source_procurement.csv`

Grain: one row per sourcing alternative, i.e. per `(material_id,
supplier_id)`. Primary key: `(material_id, supplier_id)`.

| Field | Type | Meaning | Required |
|---|---|---|---|
| `material_id` | string | ERP material master number | required |
| `material_name_procurement` | string | Free-text description (purchasing view) | required |
| `supplier_id` | string | ERP vendor number | required |
| `supplier_name` | string | Supplier name as entered in procurement | required |
| `supplier_country` | string | Supplier country as recorded by procurement | required |
| `sourcing_status` | `Current`/`Alternative` | Baseline vs. alternative under evaluation | required |
| `annual_volume_kg` | float | Annual purchased/planned volume | required |
| `price_per_kg` | float | Price per kg | required |
| `currency` | string | Always `EUR` in v0.1 (no FX logic) | optional (constant) |

### Source 2 — `source_technical_material.csv`

Grain: one row per `(material_id, supplier_id)` — qualification is
supplier-specific, not material-only. Primary key: `(material_id,
supplier_id)`, 1:1 with Procurement.

| Field | Type | Meaning | Required |
|---|---|---|---|
| `material_id` | string | Same key as Procurement | required |
| `supplier_id` | string | Same key as Procurement | required |
| `material_group` | string | One of the 5 approved groups | required |
| `comparison_case_id` | string | FK to `ref_comparison_case` — scopes which alternatives are directly comparable | required |
| `material_name_technical` | string | Free-text description (technical/R&D view) | required |
| `technical_approval_status` | `Approved`/`Under Qualification`/`Not Approved` | Qualification gate (see above) | required |
| `physical_form` | categorical | e.g. Liquid, Solid, Paste | optional |
| *group-specific technical properties* | float, optional | See table below — populated only for the relevant group(s); never compared across groups | optional |

Group-specific properties (small, explicit, no spec-management system):

| Material group | Properties populated |
|---|---|
| Base Oils | `viscosity_cst`, `density_g_cm3` |
| Solvents | `purity_pct`, `boiling_point_c` |
| Surfactants | `active_content_pct`, `ph_value` |
| Polymer Additives | `viscosity_cst`, `density_g_cm3` |
| Resins / Binders | `viscosity_cst`, `density_g_cm3` |

### Source 3 — `source_pcf_sustainability.csv`

Grain: one row per PCF declaration, i.e. per `(supplier_name_pcf,
material_name_pcf, pcf_reference_year)`. **Not** natively keyed to
`material_id`/`supplier_id` — this is the deliberate harmonization gap.
Relationship to Procurement/Technical: 0..1 per alternative (an alternative
may have no PCF record yet).

| Field | Type | Meaning | Required |
|---|---|---|---|
| `pcf_record_id` | string | Row ID of this source (not a business key) | required |
| `supplier_name_pcf` | string | Supplier name as stated on the PCF declaration | required |
| `supplier_country_pcf` | string | Country as stated on the declaration | optional |
| `material_name_pcf` | string | Material name as stated on the declaration | required |
| `material_id_linked` | string, nullable | Pre-linked material ID, where a data steward already resolved it | optional |
| `supplier_id_linked` | string, nullable | Pre-linked supplier ID, where already resolved | optional |
| `pcf_value` | float, nullable | Reported PCF value (may be missing) | required |
| `pcf_unit_basis` | categorical | `kg CO2e/kg` (occasionally `kg CO2e/t`) | required |
| `pcf_data_type` | `Supplier-specific (primary)`/`Industry-average (secondary)` | Data provenance | required |
| `pcf_reference_year` | integer | Reporting year of the value | required |
| `pcf_data_quality_note` | string | Free-text quality/limitation note | optional |

### The 7 approved synthetic data-quality issues

1. Inconsistent material naming across the three sources (free-text drift).
2. Inconsistent supplier naming across sources (e.g. legal-suffix variants).
3. Inconsistent country representation (full name vs. ISO code) between
   Procurement and PCF sources.
4. Missing `pcf_value` for a small number of alternatives.
5. Inconsistent PCF unit/basis (`kg CO2e/t` instead of `kg CO2e/kg`) on 1–2
   records.
6. One duplicate/near-duplicate procurement record (e.g. from a vendor-code
   migration) needing de-duplication.
7. Inconsistent `pcf_reference_year` across records (e.g. 2021–2023),
   affecting comparability.

### Reference/mapping layer (transformation step, not a raw source)

Small, explicit lookup tables — not a rules engine:

- `ref_supplier_mapping` — raw supplier name variant → canonical
  `supplier_id` + `supplier_name_canonical`.
- `ref_material_mapping` — raw material name variant → canonical
  `material_id` + `material_name_canonical`.
- `ref_country_mapping` — raw country value → canonical country name +
  ISO alpha-2 code.
- `ref_pcf_unit_conversion` — tiny (2-row) multiplier table, e.g.
  `kg CO2e/kg` → ×1, `kg CO2e/t` → ×0.001; may be implemented as a small
  constant instead of a full table.
- `ref_comparison_case` — the 5 comparison-case definitions (see above):
  `comparison_case_id`, `comparison_case_name`,
  `functional_requirement_description`, `specification_window`,
  `material_group`.

### Calculated fields (transformation/analytics layer only — never in raw sources)

- `annual_spend` = `annual_volume_kg` × `price_per_kg`
- `pcf_value_kg_co2e_per_kg` = `pcf_value` normalized via
  `ref_pcf_unit_conversion`
- `annual_co2e` = `annual_volume_kg` × `pcf_value_kg_co2e_per_kg`
- `technically_eligible` (boolean) = `technical_approval_status == Approved`
  — the qualification gate (see above); `Current` baseline is eligible by
  definition
- `cost_delta_vs_baseline`, `co2e_delta_vs_baseline` — vs. the `Current`
  record within the same `material_group`
- `pcf_data_quality_tier` — derived confidence label from `pcf_data_type` +
  presence of `pcf_value` + recency of `pcf_reference_year`; a data-quality
  confidence indicator only, never combined with cost into a score
- `harmonized_material_name`, `harmonized_supplier_name`,
  `harmonized_country` — canonical values from the reference/mapping layer
- `has_pcf_data` (boolean) — whether a PCF record was linked at all

### Consolidated analytical table (target for Power BI)

Grain: one row per sourcing alternative, ~25–30 rows total.

`comparison_case_id`, `material_group`, `material_id`, `material_name`,
`supplier_id`, `supplier_name`, `supplier_country`, `sourcing_status`,
`annual_volume_kg`, `price_per_kg`, `currency`, `annual_spend`,
`technical_approval_status`, `technically_eligible`, *[group-specific
technical properties, carried through as-is]*, `pcf_value_kg_co2e_per_kg`,
`pcf_data_type`, `pcf_reference_year`, `pcf_data_quality_tier`,
`has_pcf_data`, `annual_co2e`, `cost_delta_vs_baseline`,
`co2e_delta_vs_baseline`. Cost/CO2e deltas and any "which alternative wins"
logic are always computed **within one `comparison_case_id`**, never across
cases.

### Resolved design decisions

- **Alternative count:** exactly 5 supplier/material alternatives per
  material group, one of which is `Current`/baseline → 5 groups × 5 = **25
  consolidated rows total** (fixed, not a range).
- **Non-approved alternatives:** kept fully populated (procurement,
  technical, PCF data) — never deleted from the consolidated dataset.
  `Not Approved`/`Under Qualification` alternatives must remain visible so
  the dashboard can show an economically/environmentally attractive option
  that is nonetheless excluded from the valid sourcing-option set by the
  technical gate.
- **Data-quality issue distribution:** the 7 issues are spread across the 5
  material groups (no group carries more than 2). Default is one issue per
  affected raw record — avoid unnecessarily compounding multiple issues on
  the same record. Combine issues on one record only where there's a clear,
  realistic reason (e.g. a newly onboarded, less-integrated supplier
  plausibly carrying more than one master-data gap at once).
- **Rounding (presentation/output only — internal calculations stay at full
  precision):**

  | Field | Convention |
  |---|---|
  | `price_eur_per_kg` | 2 decimal places |
  | `pcf_kgco2e_per_kg` | 2 decimal places |
  | `annual_volume_kg` | whole kg |
  | `annual_spend_eur` | nearest EUR |
  | `annual_co2e_kg` | nearest kg CO2e |
  | percentage deltas | 1 decimal place |

### Decision stories (ground truth pattern per material group)

Each group is deliberately constructed around one analytical pattern —
**stories, not a scoring system or a "best supplier" algorithm.** The exact
25-row ground truth (specific IDs, names, and figures) is a separate design
artifact under owner/architect review before raw-source generation.

| Group | Pattern |
|---|---|
| Base Oils | Win-win: one technically eligible alternative is both cheaper and lower-PCF than baseline. |
| Solvents | Genuine trade-off: the cheapest eligible alternative has a worse PCF than baseline; the lowest-PCF eligible alternative costs more than baseline. |
| Surfactants | Data-quality case: one alternative looks like a strong carbon performer, but its PCF evidence is missing, secondary, and/or outdated — exposed transparently, not treated as equally reliable. |
| Polymer Additives | Technical-gate case: one alternative is attractive on cost and/or PCF but is `Not Approved` — stays visible, never treated as a valid recommendation. |
| Resins / Binders | Ambiguous field: several eligible alternatives cluster close to baseline on both cost and carbon — no obvious universal winner. |

## Power BI Concept

- Management KPI cards
- Cost vs. Carbon scatter plot
- Comparison against the current/baseline solution
- Alternative comparison table
- Filters by material group / material
- Indication of PCF data quality

### How the report is built

The Power BI report is developed **programmatically with Claude Code through
the PBIP/PBIR project format**. This is a deliberate part of the project
concept, not an implementation detail: it keeps the report reviewable as
text, diffable in Git, and reproducible from what is committed.

- **Claude Code may create and modify** the semantic model, measures, report
  pages, visuals, slicers, visual interactions and drill-through
  configuration.
- **The project owner owns** strategic design, domain judgement, approval,
  and final visual review.
- **`powerbi/*.pbip` plus the `.Report/` and `.SemanticModel/` folders are
  the authoritative source.** The legacy `powerbi/*.pbix` is a backup only
  and must never be treated as the current source or edited as one.
- **No changes to source data or domain logic** without the project owner's
  explicit approval.
- **Report pages are built sequentially and approved one at a time.** Stop
  after each page and wait for approval before starting the next.
- Changes must stay reproducible, traceable and Git-compatible: relative
  paths, no machine-local dependencies, no user-local settings in commits.

## Working Principles

1. Work strictly bottom-up ("Euler mode") — build the smallest working piece
   first, verify it, then extend.
2. Do not overengineer.
3. Do not introduce frameworks, scoring systems, optimization algorithms, or
   complex architectures unless explicitly requested.
4. Do not invent requirements beyond this specification.

## Explicit Exclusions

- **No confidential data.** Never include company data, supplier data,
  previous employer data, tender data, internal documents, or proprietary
  information of any kind. All demonstration data must be fully synthetic.
- **Publication scope.** Do not introduce conceptual or mathematical
  extensions beyond the publication scope defined for this repository.
- **No binary Power BI authoring.** The report is authored programmatically,
  but only through the text-based PBIP/PBIR project files (see *How the
  report is built*). Never generate or hand-edit a `.pbix`; it is a build
  output and a legacy backup, never the source.
- **No overall sustainability score or weighted ranking** (see Methodological
  Principle above).
- **No specific employer.** Never name or target a specific employer (past,
  present, or prospective), use a company's name/logo/proprietary process, or
  attempt to reproduce any specific company's internal raw-material approval
  process.

## Data Locations

- `data/raw/source_procurement.csv`, `data/raw/source_technical_material.csv`,
  `data/raw/source_pcf_sustainability.csv` — the three synthetic raw
  sources, deliberately heterogeneous, embedding the 7 approved
  data-quality issues (see Data Model above).
- `validation/ground_truth_consolidated.csv` — the approved 25-row
  consolidated ground truth (canonical/harmonized values, including
  calculated fields), kept outside `data/raw/` so later transformation
  output can be tested against it. **Test data only** — `src/transform.py`
  must never read this file; only `src/validate.py` may.
- `data/reference/` — the small, explicit, deterministic mapping tables used
  by the transformation (`ref_supplier_mapping.csv`,
  `ref_material_mapping.csv`, `ref_country_mapping.csv`,
  `ref_pcf_unit_conversion.csv`, `ref_comparison_case.csv`). No fuzzy
  matching or entity resolution — every mapping is an exact, inspectable
  lookup.
- `src/transform.py` — the transformation/harmonization pipeline (raw
  sources + reference tables → `data/processed/`). Produces
  `consolidated_material_benchmark.csv` (25-row analytical table) and
  `data_quality_log.csv` (one row per detected/resolved data-quality issue
  instance).
- `src/validate.py` — independent validation only; compares
  `data/processed/consolidated_material_benchmark.csv` against
  `validation/ground_truth_consolidated.csv` after the fact. Kept separate
  from `transform.py` so the transformation can never "see" the answer key.

## Status

**v0.1 data pipeline complete and validated.**

- 3 heterogeneous raw sources (procurement, technical/qualification, PCF/
  sustainability), deliberately non-harmonized by design.
- 7 intentional data-quality issue types successfully detected: material
  naming inconsistency, supplier naming inconsistency, country
  representation inconsistency, missing PCF value, PCF unit-basis
  inconsistency, duplicate procurement record, inconsistent/outdated PCF
  reference year.
- 25-row consolidated analytical dataset generated
  (`data/processed/consolidated_material_benchmark.csv`).
- `data_quality_log.csv` generated, documenting each detected issue with
  source, affected record, original value, harmonized value/action,
  severity, and explanation.
- Transformation logic (`src/transform.py`) kept strictly separated from
  ground-truth validation (`src/validate.py`) — the transformation never
  reads `validation/ground_truth_consolidated.csv`.
- Validation against ground truth **PASSED**: correct row count, no
  double-counting, all field values within tolerance, correct qualification
  gating, correct PCF missingness/quality classification.
- All 5 decision stories (Base Oils win-win, Solvents trade-off, Surfactants
  data-quality case, Polymer Additives technical-gate case, Resins/Binders
  ambiguous field) reconstructed successfully from the independently
  produced consolidated dataset.
- No scoring/ranking logic implemented anywhere in the pipeline.

**Next phase:** Power BI analysis and dashboard development in the PBIP/PBIR
project, authored with Claude Code and approved page by page by the project
owner, using `data/processed/consolidated_material_benchmark.csv` and
`data/processed/data_quality_log.csv` as inputs.
