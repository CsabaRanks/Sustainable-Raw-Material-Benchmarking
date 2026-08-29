# Input templates

Seven files: three inputs and four reference tables. Copy the folder, replace the
example rows, run the pipeline. Nothing here is real — every supplier, material,
volume and price is fictional and exists only to show the shape.

```
cp data/templates/*.csv data/mycompany/
python src/validate.py  --raw data/mycompany --ref data/mycompany
python src/transform.py --raw data/mycompany --ref data/mycompany --out data/mycompany/processed
```

The full field-by-field contract is in [`../../docs/DATA_DICTIONARY.md`](../../docs/DATA_DICTIONARY.md);
the step-by-step walkthrough is in [`../../docs/BYOD.md`](../../docs/BYOD.md).

## What the example is built to show

Six materials in two comparison cases, chosen so that one run exercises every
mechanism you are likely to meet in real data.

| | |
|---|---|
| **CASE-X**, three solvents | one incumbent, one approved alternative, one **not approved** |
| **CASE-Y**, three additives | one incumbent, one approved alternative **with no PCF declaration**, one **under qualification** |
| `SUP-A` | supplies a material in **both** cases — proving a PCF declaration is matched on supplier *and* material, never on supplier alone |
| `MAT-005` | has **no row** in `input_pcf.csv` — its carbon figure stays empty everywhere, and it stays in the cost comparison |
| `MAT-002` | procurement calls it `…Grade A Bio`, the technical system calls it `…Grade A Bio-based` — reconciled by `ref_material_mapping.csv` |
| `PCF-E02` | declared in `kg CO2e/t` — converted by `ref_pcf_unit_conversion.csv` before any comparison |
| `PCF-E02` | reference year 2019 and industry-average — lands in the **Low confidence** tier |
| `PCF-E03` | supplier written as `Demo Specialities B.V.` — reconciled by `ref_supplier_mapping.csv` |
| `PCF-E02` | country written as `NL` — reconciled by `ref_country_mapping.csv` |

Running the pipeline on this folder produces six rows and six data-quality
findings: four resolved automatically, two left open by design.

`processed/` holds that output so you can see the result before running
anything. It is generated and can be deleted at any time.

## Things that will stop the run

Deliberately, and with a message naming the value and the file:

- a name in any input that has no row in the matching `ref_*` table;
- two PCF declarations for the same supplier and material;
- a comparison case without exactly one `Current` row.

`python src/validate.py` reports all of these before you transform anything.
