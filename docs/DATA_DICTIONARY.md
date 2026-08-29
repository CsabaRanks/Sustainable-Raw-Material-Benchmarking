# Data dictionary — the input contract

Everything the pipeline needs, and nothing it does not. Three input files and
four reference tables. If your data satisfies this contract, the pipeline runs
without any code change.

Ready-to-edit copies of all seven files are in [`data/templates/`](../data/templates/).

**Conventions used below.** Text comparisons are **case-sensitive and exact** —
`approved` is not `Approved`. Decimal separator is a full stop. Empty cells mean
*not known*; they are never read as zero. Column order does not matter, column
names do.

---

## 1. `input_procurement.csv`

What is bought today and what could be bought instead: volume, price, supplier.

| Field | Description | Required | Type | Allowed values | Example | Validation | Missing values |
|---|---|---|---|---|---|---|---|
| `material_id` | Your identifier for the material | yes | text | — | `MAT-001` | unique together with `supplier_id` | not allowed |
| `material_name_procurement` | The name as it appears in the purchasing system, however messy | yes | text | — | `Example Solvent Grade A Bio` | must appear in `ref_material_mapping.csv` | not allowed |
| `supplier_id` | Your identifier for the supplier | yes | text | — | `SUP-A` | — | not allowed |
| `supplier_name` | Supplier name as it appears in the purchasing system | yes | text | — | `Example Chemicals AG` | must appear in `ref_supplier_mapping.csv` | not allowed |
| `supplier_country` | Country of supply | yes | text | — | `Germany` | must appear in `ref_country_mapping.csv` | not allowed |
| `sourcing_status` | Marks the incumbent | yes | text | **`Current`**, **`Alternative`** | `Current` | exactly one `Current` per comparison case | not allowed |
| `annual_volume_kg` | Annual quantity | yes | integer | — | `100000` | must be > 0 | not allowed |
| `price_per_kg` | Price per kilogram | yes | decimal | — | `2.00` | must be > 0 | not allowed |
| `currency` | Currency of `price_per_kg` | yes | text | — | `EUR` | one currency across the dataset; the pipeline does **not** convert | not allowed |

**Duplicate vendor codes are tolerated.** If the same `material_id` appears twice
with different `supplier_id` values, the row whose `supplier_id` matches the
technical input is kept and the other is logged as resolved. If the commercial
figures on the dropped row differ, that is recorded in the log.

---

## 2. `input_technical.csv`

What the material is, which comparison it belongs to, and whether it is approved.

| Field | Description | Required | Type | Allowed values | Example | Validation | Missing values |
|---|---|---|---|---|---|---|---|
| `material_id` | Joins to procurement | yes | text | — | `MAT-001` | 1:1 with procurement | not allowed |
| `supplier_id` | Joins to procurement | yes | text | — | `SUP-A` | 1:1 with procurement | not allowed |
| `material_group` | Category label | yes | text | — | `Example Solvents` | — | not allowed |
| `comparison_case_id` | **Which materials compete with each other** | yes | text | — | `CASE-X` | ≥ 2 materials per case, exactly one `Current` | not allowed |
| `material_name_technical` | Name as used in the technical system | yes | text | — | `Example Solvent Grade A` | must appear in `ref_material_mapping.csv` | not allowed |
| `technical_approval_status` | **The gate** | yes | text | see below | `Approved` | must be populated | not allowed |
| `physical_form` | Property | no | text | — | `Liquid` | — | leave empty |
| `purity_pct` | Property | no | decimal | — | `99.5` | — | leave empty |
| `boiling_point_c` | Property | no | decimal | — | `145.0` | — | leave empty |
| `viscosity_cst` | Property | no | decimal | — | `1.2` | — | leave empty |
| `density_g_cm3` | Property | no | decimal | — | `0.870` | — | leave empty |
| `active_content_pct` | Property | no | decimal | — | `90.0` | — | leave empty |
| `ph_value` | Property | no | decimal | — | `7.4` | — | leave empty |

The seven property columns must **exist** even when every cell is empty; they are
carried through to the output as decision context.

---

## 3. `input_pcf.csv`

Supplier carbon declarations. **This file may be incomplete — that is the point.**
A material with no row here keeps an empty carbon figure all the way through.

| Field | Description | Required | Type | Allowed values | Example | Validation | Missing values |
|---|---|---|---|---|---|---|---|
| `pcf_record_id` | Identifier for the declaration | yes | text | — | `PCF-E01` | — | not allowed |
| `supplier_name_pcf` | Supplier as named on the declaration | yes | text | — | `Example Chemicals AG` | must appear in `ref_supplier_mapping.csv` | not allowed |
| `supplier_country_pcf` | Country as named on the declaration | yes | text | — | `NL` | must appear in `ref_country_mapping.csv` | not allowed |
| `material_name_pcf` | Material as named on the declaration | yes | text | — | `Example Solvent Grade A` | must appear in `ref_material_mapping.csv` | not allowed |
| `material_id_linked` | Optional internal cross-reference | no | text | — | | not used by the pipeline | leave empty |
| `supplier_id_linked` | Optional internal cross-reference | no | text | — | | not used by the pipeline | leave empty |
| `pcf_value` | The declared footprint | yes | decimal | — | `1.50` | must be ≥ 0 | omit the whole row instead |
| `pcf_unit_basis` | Unit the value is stated in | yes | text | must appear in `ref_pcf_unit_conversion.csv` | `kg CO2e/kg` | converted before any comparison | not allowed |
| `pcf_data_type` | **Provenance** | yes | text | see below | `Supplier-specific (primary)` | drives the confidence tier | not allowed |
| `pcf_reference_year` | Year the figure refers to | yes | integer | — | `2023` | plausible year; drives the confidence tier | not allowed |
| `pcf_data_quality_note` | Free-text remark | no | text | — | `Sector average` | — | leave empty |

**A declaration is matched on supplier *and* material.** At most one declaration
per supplier/material pair; two competing declarations stop the pipeline with an
explicit error rather than one being chosen silently.

---

## 4. Controlled vocabularies

### `sourcing_status`

| Value | Meaning |
|---|---|
| `Current` | The incumbent. **Every delta in the benchmark is measured against this row.** Exactly one per comparison case. |
| `Alternative` | A candidate competing with the incumbent inside the same case. |

### `technical_approval_status`

| Value | Technically eligible? | Meaning |
|---|---|---|
| **`Approved`** | **yes** | Released for use. **This is the only value that makes an alternative technically eligible.** |
| `Not Approved` | no | Assessed and rejected. Stays visible with its reason; it is never deleted from the comparison. |
| `Under Qualification` | no | In the qualification pipeline. Not buyable today, may become eligible later. |

Any other value you introduce is treated as **not eligible**, because eligibility
is derived as `technical_approval_status == "Approved"`. If your organisation uses
different labels, either map them to these three or accept that anything other
than the exact string `Approved` blocks the alternative.

### `pcf_data_type`

| Value | Interpretation |
|---|---|
| `Supplier-specific (primary)` | The supplier calculated this figure for this product. The only provenance that can reach the **High confidence** tier. |
| `Industry-average (secondary)` | A sector or database average. Cannot by construction distinguish two suppliers inside the same industry, so it always yields **Low confidence**. |

### `pcf_unit_basis`

Whatever you list in `ref_pcf_unit_conversion.csv`. The demonstration and the
templates ship with `kg CO2e/kg` (multiplier 1) and `kg CO2e/t` (multiplier
0.001).

### `pcf_data_quality_tier` — derived, not an input

| Tier | Condition |
|---|---|
| `High confidence` | `pcf_data_type` is `Supplier-specific (primary)` **and** `pcf_reference_year` ≥ the threshold in `config.json` (default 2022) |
| `Low confidence` | A PCF exists but fails either condition |
| `No data` | No PCF declaration for this supplier/material pair |

This tier is a **prototype design heuristic derived from provenance and recency**.
It is not a standards-conformant data-quality assessment.

---

## 5. Reference tables

Four tables, all required, all read from the folder given by `--ref`. Each one
maps a messy real-world value to a canonical one. Lookups are **exact and
deterministic — never fuzzy.** An unmapped value stops the run with a message
naming the value and the table to add it to.

| Table | Maps | Columns | Add a row when… |
|---|---|---|---|
| `ref_material_mapping.csv` | `material_name_procurement`, `material_name_technical`, `material_name_pcf` | `raw_material_name`, `material_name_canonical`, `material_group_hint` | a material appears under a new spelling in any of the three inputs |
| `ref_supplier_mapping.csv` | `supplier_name`, `supplier_name_pcf` | `raw_supplier_name`, `supplier_id_canonical`, `supplier_name_canonical` | a supplier appears under a new spelling or legal form |
| `ref_country_mapping.csv` | `supplier_country`, `supplier_country_pcf` | `raw_country_value`, `country_name_canonical`, `country_iso2_canonical` | a country appears as a code or an alternative name |
| `ref_pcf_unit_conversion.csv` | `pcf_unit_basis` | `pcf_unit_basis`, `multiplier_to_kgco2e_per_kg` | a declaration arrives on a new unit basis |

**Every spelling needs its own row, including the canonical one.** If procurement
writes `Example Solvent Grade A Bio` and the technical system writes
`Example Solvent Grade A Bio-based`, both strings need a row pointing at the same
canonical name.

### `ref_comparison_case.csv` — informational only

The demonstration dataset also ships `data/reference/ref_comparison_case.csv`,
which describes each comparison case in words: its name, its functional
requirement and its specification window. **It is not read by the pipeline.**
`comparison_case_id` and `material_group` are taken from the technical input.

Keep it as documentation of what each case is for — it is the natural place to
record the functional equivalence a comparison assumes — or leave it out. Nothing
in the code depends on it.

---

## 6. Output

`consolidated_material_benchmark.csv`, one row per material, 31 columns: the
inputs after harmonisation, plus `technically_eligible`, `has_pcf_data`,
`pcf_data_quality_tier`, `annual_spend_eur`, `annual_co2e_kg` and four
delta columns measured against the incumbent of the same case.

`data_quality_log.csv`, one row per finding: `issue_type`, `source`,
`material_id`, `supplier_id`, `original_value`, `harmonized_value_or_action`,
`severity` (`resolved` / `open` / `unresolved`) and an explanation.

**Nothing in the output is a score, a rank or a weight.** Cost and carbon stay in
separate columns, and a material with no PCF keeps an empty carbon figure rather
than a zero.
