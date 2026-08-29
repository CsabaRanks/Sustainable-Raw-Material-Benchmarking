# Sustainable Raw Material Benchmarking

Comparing technically suitable supplier/material alternatives for a purchased
raw material on **cost** and **Product Carbon Footprint (PCF)** — deliberately
without collapsing them into a single sustainability score.

The decision this supports is narrow and practical: *for this material need,
which approved alternatives are worth a closer look, and what would switching
cost in euros and in kilograms of CO2e?* Cost and carbon are reported side by
side and the trade-off is left visible for a person to decide.

**All data in this repository is synthetic.** No real company, supplier,
material, price, PCF figure or tender appears anywhere in it. See
[`PROJECT_SPEC.md`](PROJECT_SPEC.md) for the full scope and the explicit
exclusions.

This is a **demonstration and reference implementation**, not a product. Run
it on the synthetic data shipped here, or connect your own data through the
documented BYOD workflow — [`docs/BYOD.md`](docs/BYOD.md).

**Status:** v1.0 — dataset, pipeline, Power BI report, written paper and
report deck are all in place.

---

## What is in here

| | |
|---|---|
| **A method** | eligibility → comparability → evidence → trade-off → decision, written up in [`Paper/`](Paper/) |
| **A synthetic dataset** | 25 supplier/material combinations across five comparison cases, carrying realistic naming drift, mixed units and a missing PCF |
| **A pipeline** | ~600 lines of pandas in [`src/`](src/) — validate, harmonise, consolidate, log every data-quality finding |
| **A Power BI report** | authored as text through the PBIP/PBIR project format in [`powerbi/`](powerbi/) |
| **An input contract** | [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md) and ready-to-edit templates in [`data/templates/`](data/templates/) |
| **A portable report** | one Power Query parameter points the report at the demonstration output or at yours — [`docs/POWER_BI_SETUP.md`](docs/POWER_BI_SETUP.md) |

## Quick start

Python 3.10 or later, one dependency.

```
pip install -r requirements.txt

python src/validate.py        # check the inputs against the contract
python src/transform.py       # build data/processed/ from data/raw/
python src/validate_demo.py   # regression test — synthetic demonstration only
```

`transform.py` is deterministic: run it twice and you get byte-identical
output. It writes `consolidated_material_benchmark.csv` (one row per material,
31 columns) and `data_quality_log.csv` (one row per finding).

### Running it on your own data

No code changes are required. Copy [`data/templates/`](data/templates/), replace
the example rows, and point the scripts at your folder:

```
python src/validate.py  --raw data/mycompany --ref data/mycompany
python src/transform.py --raw data/mycompany --ref data/mycompany --out data/mycompany/processed
```

Then open the Power BI project and point its `DataFilePath` parameter at your
processed file — [`docs/POWER_BI_SETUP.md`](docs/POWER_BI_SETUP.md).

[`docs/BYOD.md`](docs/BYOD.md) walks through it step by step and lists the known
limitations. `validate_demo.py` is the regression test for the shipped synthetic
data only and will fail on yours by design.

## Repository structure

```
data/raw/           three synthetic source extracts, deliberately inconsistent
data/reference/     mapping tables that reconcile the inconsistencies
data/processed/     the consolidated output, committed so it can be inspected
data/templates/     the same seven files, empty of demo content, for your data
src/                validate.py, transform.py, validate_demo.py
docs/               input contract, BYOD guide and Power BI setup
powerbi/            PBIP/PBIR project — the authoritative report source
Paper/              the written paper (LaTeX source and PDF)
report/             the management report deck and its generator
validation/         the ground truth the demonstration regression test uses
```

## The rules the pipeline enforces

These are methodological commitments, not preferences, and `validate.py` checks
every one of them:

- **Exactly one incumbent per comparison case** — every delta is measured
  against it, so two incumbents or none makes the case meaningless.
- **Cases are independent** — nothing is compared or aggregated across them.
- **Technical eligibility is a gate, not a score** — a non-approved alternative
  stays visible with its reason, and no cost or carbon advantage overrides it.
- **Missing PCF stays missing** — never zero, never imputed. If absence became
  zero, the supplier who discloses least would look like the best performer.
- **Evidence travels beside the number** — provenance, reference year and
  confidence tier live in their own columns and are never blended in.
- **No composite score, no weighting, no cross-case ranking.**

## The Power BI report

Three pages — **Executive / Portfolio Overview**, **Material Benchmark &
Decision Analysis**, **Opportunity & Risk Heatmap** — over 21 measures.

The report is developed **programmatically through the PBIP/PBIR project
format**, which keeps every page, visual, measure and query reviewable as text
and diffable in Git. `powerbi/*.pbip` together with the `.Report/` and
`.SemanticModel/` folders is the authoritative source; a `.pbix` is a build
output, never the source.

It reads one file — the processed CSV — located by a single Power Query
parameter, `DataFilePath`. Setting that parameter is the only change a new user
makes; no M code needs editing. See
[`docs/POWER_BI_SETUP.md`](docs/POWER_BI_SETUP.md) for the walkthrough and
[`docs/POWER_BI_INPUT_CONTRACT.md`](docs/POWER_BI_INPUT_CONTRACT.md) for the
contract and the failure modes.

## Author

Csaba Bakay.

## License

The software, Power BI source files, technical utilities and synthetic
demonstration data are licensed under the **MIT License** — see
[`LICENSE`](LICENSE).

The written paper ([`Paper/`](Paper/)) and the presentation deck
([`report/`](report/)) are **© 2026 Csaba Bakay, all rights reserved**. Those
two documents are **not** covered by the MIT License; the scripts that generate
them are.

To cite this work, see [`CITATION.cff`](CITATION.cff).
