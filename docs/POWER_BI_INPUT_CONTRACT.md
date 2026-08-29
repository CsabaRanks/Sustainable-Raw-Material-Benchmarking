# Power BI input contract

The report reads **exactly one file**: the processed output of `src/transform.py`.
It never reads your raw procurement, technical or PCF extracts, and it performs
no harmonisation of its own. Everything the report shows was already decided by
the Python pipeline.

```
your raw CSVs → src/validate.py → src/transform.py → consolidated_material_benchmark.csv → Power BI
```

## The file

| | |
|---|---|
| **Filename** | `consolidated_material_benchmark.csv` — the name is not enforced, the parameter points at whatever path you give it, but keeping the name avoids confusion |
| **Produced by** | `src/transform.py`, in the folder given by its `--out` argument (default `data/processed/`) |
| **Delimiter** | comma |
| **Encoding** | UTF-8 |
| **Decimal separator** | full stop; the query parses numbers with the `en-US` locale regardless of your Windows regional settings |
| **Header row** | required, first row |
| **Grain** | one row per material within a comparison case |

## How the report finds it

A single Power Query parameter:

| Parameter | Type | Default | Meaning |
|---|---|---|---|
| **`DataFilePath`** | Text, required | *(empty)* | Full absolute path to the processed CSV |

Set it once. **No M code has to be edited**, and the parameter is the only
machine-specific value in the whole project — nothing else in the published
Power BI source refers to any particular folder.

Example values:

```
C:\Users\you\repos\sustainable-raw-material-benchmarking\data\processed\consolidated_material_benchmark.csv
C:\Users\you\benchmark\mycompany\processed\consolidated_material_benchmark.csv
```

Power Query requires an absolute path — `File.Contents` cannot resolve a path
relative to the project.

## Required fields

All 31 columns below must be present. Column **order does not matter**, and
extra columns are ignored rather than rejected, so a later pipeline version that
adds a column will not break the report.

| Group | Columns |
|---|---|
| Identity | `comparison_case_id`, `material_group`, `material_id`, `material_name` |
| Supplier | `supplier_id`, `supplier_name`, `supplier_country`, `sourcing_status` |
| Commercial | `annual_volume_kg`, `price_eur_per_kg`, `currency`, `annual_spend_eur` |
| Eligibility | `technical_approval_status`, `technically_eligible` |
| Carbon | `pcf_kgco2e_per_kg`, `pcf_data_type`, `pcf_reference_year`, `pcf_data_quality_tier`, `has_pcf_data`, `annual_co2e_kg` |
| Deltas vs. the incumbent | `cost_delta_vs_baseline_eur`, `cost_delta_pct_vs_baseline`, `co2e_delta_vs_baseline_kg`, `co2e_delta_pct_vs_baseline` |
| Technical properties | `physical_form`, `purity_pct`, `boiling_point_c`, `viscosity_cst`, `density_g_cm3`, `active_content_pct`, `ph_value` |

What each field means, which values are allowed, and how it is derived is in
[`DATA_DICTIONARY.md`](DATA_DICTIONARY.md) — that document is the authority on
meaning; this one only states what the report needs in order to load.

Two conventions matter more than the rest, because the report's semantics depend
on them:

- **An empty carbon cell means *no declaration*, not zero.** The query loads it
  as null, and the measures leave it out of averages rather than counting it as
  a zero-carbon material.
- **`technically_eligible` is a gate, not a filter.** Ineligible materials are
  loaded and displayed, with their status visible. The report never silently
  drops them.

## Refreshing

**Power BI Desktop** — *Home → Refresh*, or *Transform data → Refresh preview*.
Re-run `src/transform.py` first if your inputs changed; the report reads the file
as it is on disk at refresh time and holds no cache of its own beyond the
imported model.

To point the report at a different dataset: *Home → Transform data → Manage
parameters*, change `DataFilePath`, close and apply, refresh.

**Power BI Service** — a local file path only refreshes through an on-premises
data gateway. For scheduled cloud refresh, move the processed file to a location
the Service can reach and set `DataFilePath` accordingly. The repository does not
configure or require this.

## What happens when something is wrong

The query fails loudly and specifically. It never loads a partial or silently
substituted table.

| Situation | What you see |
|---|---|
| `DataFilePath` is empty | *"The DataFilePath parameter is empty. Set it to the full path of consolidated_material_benchmark.csv produced by src/transform.py…"* |
| Path is set but the file is not there | Power Query's own `DataSource.Error` naming the path it tried to open. Check the path, and check that `src/transform.py` has actually run |
| File is there but a required column is missing | *"The file at "…" does not match the documented Power BI input contract. Missing required column(s): x, y."* — regenerate the file with `src/transform.py` rather than editing the CSV by hand |
| File has extra columns | Loads normally; the extra columns are ignored |
| Numbers are formatted for another locale | The query parses with `en-US` explicitly, so a German or French Windows locale does not affect it. A CSV that itself uses comma decimals is not a valid pipeline output — regenerate it |

---

Method and implementation: Csaba Bakay. All data shipped with this repository is
synthetic.
