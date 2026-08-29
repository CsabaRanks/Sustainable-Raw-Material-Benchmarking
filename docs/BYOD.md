# Bring your own data

How to run this benchmark on your own raw-material data instead of the synthetic
demonstration. No code changes are required.

The synthetic demonstration stays where it is. Nothing below overwrites it.

---

## 1. Install

Python 3.10 or later. One dependency.

```
pip install -r requirements.txt
```

## 2. Check that the demonstration runs

```
python src/transform.py
python src/validate.py
python src/validate_demo.py
```

The first rebuilds `data/processed/` from `data/raw/`. The second checks the
inputs and the output against the rules. The third is the regression test for the
synthetic demonstration only — it compares against a known ground truth and is
**not** meaningful for your data.

## 3. Copy the templates

```
mkdir -p data/mycompany
cp data/templates/*.csv data/mycompany/
```

Seven files: three inputs and four reference tables. They contain a small
fictional example so you can see the shape before you replace it.

Put your folder anywhere. `data/mycompany/` is a suggestion, not a requirement.
Keep it out of the repository if your data is confidential.

## 4. Fill in your data

Replace the example rows. The full contract is in
[`DATA_DICTIONARY.md`](DATA_DICTIONARY.md). The short version:

**`input_procurement.csv`** — one row per material you buy or could buy.
Volume, price, supplier, and `sourcing_status` set to `Current` for the material
you buy today and `Alternative` for each candidate.

**`input_technical.csv`** — the same materials, plus `comparison_case_id`
grouping the ones that actually compete with each other, plus
`technical_approval_status`. Only the exact value `Approved` makes an alternative
eligible.

**`input_pcf.csv`** — one row per supplier carbon declaration you hold. **Leave
out materials you have no declaration for.** Do not enter a zero and do not
estimate; a missing figure is reported as missing and stays missing everywhere
downstream.

**The four `ref_*.csv` tables** — one row for every spelling that appears in your
inputs. This is where messy real-world naming is reconciled. If you miss one, the
run stops and names the value and the table.

### Deciding what a comparison case is

A comparison case is one purchased material need. Everything inside it must be a
genuine substitute for everything else inside it, because every figure is
measured against the incumbent of that case. Two different needs are two cases,
and the benchmark makes no statement across them.

## 5. Validate before you transform

```
python src/validate.py --raw data/mycompany --ref data/mycompany
```

This checks your files against the contract: required columns, controlled
vocabularies, one incumbent per case, unmapped names, implausible values,
ambiguous PCF declarations. Fix what it reports before going further — every
message names the file and the value.

## 6. Transform

```
python src/transform.py --raw data/mycompany --ref data/mycompany --out data/mycompany/processed
```

Produces `consolidated_material_benchmark.csv` and `data_quality_log.csv`.

Read the log. Findings marked `resolved` were reconciled deterministically.
Findings marked `open` are real gaps in your data that the method deliberately
carries rather than filling — a missing PCF, an outdated reference year. Findings
marked `unresolved` need you.

## 7. Validate the result

```
python src/validate.py --raw data/mycompany --ref data/mycompany --out data/mycompany/processed
```

Now the output rules are checked too: missing PCF stayed missing, ineligible
alternatives are still visible, each case has exactly one incumbent sitting at
zero, and no score, rank or weight column has appeared.

Do **not** run `validate_demo.py` against your data. It compares against the
synthetic ground truth and will fail by design.

## 8. Open it in Power BI

```
powerbi/Sustainable_Raw_Material_Benchmarking.pbip
```

Set the `DataFilePath` parameter to the full path of the file you just produced,
and refresh. That is the only change the report needs.

[`POWER_BI_SETUP.md`](POWER_BI_SETUP.md) has the walkthrough;
[`POWER_BI_INPUT_CONTRACT.md`](POWER_BI_INPUT_CONTRACT.md) documents exactly what
the report expects and how it fails when something is wrong.

---

## Configuration

`config.json` in the repository root:

```json
{
  "recent_pcf_year_threshold": 2022
}
```

`recent_pcf_year_threshold` is the reference year from which a supplier-specific
PCF is treated as recent enough for the **High confidence** tier. Set it to your
own currency requirement. Delete the file to fall back to the documented default.

This is the only configurable value. Everything else that could change a result
lives in your input data, where you can see it.

---

## The rules the pipeline will not let you break

These are methodological commitments, not preferences. They are enforced in code
and checked by `validate.py`.

- **Exactly one incumbent per comparison case.** Every delta is measured against
  it, so two incumbents or none makes the case meaningless.
- **Alternatives stay inside their case.** A material is compared only with the
  materials it can actually replace.
- **Cases are independent.** No statement is made across cases, and nothing is
  aggregated across them.
- **Technical eligibility is a gate, not a score.** A non-approved alternative
  stays visible with its reason. It is never deleted, and no carbon or cost
  advantage can compensate for a failed gate.
- **Missing PCF stays missing.** It is never converted to zero, never imputed and
  never estimated. If absence became zero, the supplier who discloses least would
  look like the best performer.
- **A missing carbon delta is undefined, not zero.** The material stays in the
  cost comparison and drops out of the carbon comparison only.
- **Evidence stays beside the number.** Provenance, reference year and confidence
  tier travel with the PCF in their own columns and are never blended into it.
- **No composite score. No weighting. No cross-case ranking.** Cost and carbon are
  reported side by side, and the trade-off is left visible for a person to decide.

---

## Known limitations

**Currency.** The pipeline does not convert currencies. Use one currency per
dataset; `validate.py` warns if it finds more than one.

**One declaration per supplier and material.** If you hold two competing PCF
declarations for the same supplier and material, the run stops. Decide which one
applies rather than letting the tool pick.

**Functional equivalence is assumed, not proven.** All comparisons are per
kilogram. If the materials in a case are not functionally equivalent per
kilogram — different active content, different dosage — the per-kilogram delta
is a declared-unit comparison, not a functional one. Record the functional basis
in `ref_comparison_case.csv` and read the deltas with that in mind.

**Comparability of supplier PCFs is not verified.** The pipeline reports what
your suppliers declared and how well it is evidenced. It does not establish that
two declarations were produced on a comparable basis. That question, and the
fields that would answer it, are discussed in the paper.
