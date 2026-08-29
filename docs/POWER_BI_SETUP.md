# Power BI setup

How to open this benchmark in Power BI Desktop — first with the synthetic
demonstration data, then with your own.

You do not need to know anything about how the project was built. There is one
setting to change.

**Requirements:** Power BI Desktop (a recent version, Windows), Python 3.10+,
and this repository on disk.

---

## Two paths, and they must not be mixed

| | Reads | Use it to |
|---|---|---|
| **A — Demonstration** | `data/processed/` — **synthetic data, invented for this repository** | See what the method produces, before committing any of your own data |
| **B — Your own data** | a processed file you generate from your own inputs | Actually benchmark your materials |

Everything shipped in `data/raw/`, `data/processed/` and `data/templates/` is
**synthetic**: the suppliers, materials, prices, volumes and carbon figures were
invented. No number in the demonstration is a real market figure, and none of it
should ever be quoted as one. Keep your own processed output in a separate folder
so the two can never be confused — the paths are how you tell them apart.

---

## Path A — the synthetic demonstration

**1. Install the one dependency**

```
pip install -r requirements.txt
```

**2. Generate the processed file**

```
python src/transform.py
```

This writes `data/processed/consolidated_material_benchmark.csv`. It is
deterministic — running it again produces the identical file.

**3. Open the project**

Open `powerbi/Sustainable_Raw_Material_Benchmarking.pbip` in Power BI Desktop.

**4. Set the file path** *(once — see below)*

Point `DataFilePath` at the file step 2 produced. On your machine that is
`<this repository>\data\processed\consolidated_material_benchmark.csv`.

**5. Refresh**

*Home → Refresh.* You should get 25 materials across 5 comparison cases, on
three pages: **Executive / Portfolio Overview**, **Material Benchmark & Decision
Analysis** and **Opportunity & Risk Heatmap**.

---

## Path B — your own data

**1–2.** As above: install the dependency, and read
[`BYOD.md`](BYOD.md) — it is the guide to preparing your inputs.

**3. Copy the templates and fill them in**

```
mkdir mycompany
cp data/templates/*.csv mycompany/
```

Replace the example rows with your own. The field-by-field contract is
[`DATA_DICTIONARY.md`](DATA_DICTIONARY.md).

**4. Validate**

```
python src/validate.py --raw mycompany --ref mycompany
```

Fix everything it reports. Each message names the file and the value.

**5. Transform**

```
python src/transform.py --raw mycompany --ref mycompany --out mycompany/processed
```

**6. Validate the result**

```
python src/validate.py --raw mycompany --ref mycompany --out mycompany/processed
```

**7. Open the project and point it at your file**

Open the `.pbip`, set `DataFilePath` to
`<full path>\mycompany\processed\consolidated_material_benchmark.csv`, refresh.

Your own benchmark, in the same three pages.

> If your data is confidential, keep your folder outside the repository so it
> can never be committed by accident.

---

## Setting `DataFilePath`

*Home → Transform data → Manage parameters*, set **DataFilePath**, then
*Close & Apply*.

It takes the **full absolute path to the CSV file**, including the filename:

```
C:\Users\you\repos\sustainable-raw-material-benchmarking\data\processed\consolidated_material_benchmark.csv
```

Power Query cannot resolve a path relative to the project, which is why this is
a parameter rather than something the project can work out for itself. It is the
only machine-specific value in the project, and changing it is the only edit a
new user has to make.

---

## If the refresh fails

| Message | Cause | Fix |
|---|---|---|
| *"The DataFilePath parameter is empty…"* | The parameter was never set | Set it, as above |
| `DataSource.Error … Could not find file` | Wrong path, or `transform.py` has not run | Check the path character for character; confirm the CSV exists |
| *"…does not match the documented Power BI input contract. Missing required column(s): …"* | The file is not a pipeline output, or is from an incompatible version | Regenerate it with `src/transform.py`. Do not hand-edit the CSV |
| Access denied | The file is open in Excel, or is in a protected folder | Close it; move it somewhere writable |

The full contract, including every required column and every failure mode, is in
[`POWER_BI_INPUT_CONTRACT.md`](POWER_BI_INPUT_CONTRACT.md).

---

## What is in the project, and what counts as source

The **PBIP project** — the `.pbip` file with the `.Report/` and
`.SemanticModel/` folders — is the source. It is entirely text: pages, visuals,
measures and the query are all reviewable and diffable, which is why the
repository publishes it in this form.

A `.pbix` is a **build output**, never the source. If you find one, treat it as
disposable.

### Making a `.pbit` template *(optional, manual)*

A `.pbit` is convenient for handing the report to someone who only wants to
apply it: opening one prompts for `DataFilePath` immediately, before any data is
loaded, and it carries no data inside it.

**This repository does not ship a `.pbit`.** It cannot be generated reliably
without Power BI Desktop, and a hand-fabricated one would be untrustworthy. To
produce one yourself:

1. Open `powerbi/Sustainable_Raw_Material_Benchmarking.pbip` in Power BI Desktop.
2. Set `DataFilePath` and refresh once, to confirm the report loads.
3. **Clear `DataFilePath` back to an empty value** — a template carries its
   parameter defaults, and you do not want to ship your own folder path inside it.
4. *File → Export → Power BI template*.
5. Give it a description, e.g. *"Set DataFilePath to your processed
   consolidated_material_benchmark.csv."*
6. Save as `Sustainable_Raw_Material_Benchmarking.pbit`.

Step 3 is the one that matters. A `.pbit` exported with a populated parameter
leaks the exporter's folder structure to everyone who opens it.

---

## Maintainer note — before releasing

*Only relevant if you edit the project in Power BI Desktop and publish the
result. Users of the report can ignore this.*

Power BI Desktop rewrites the PBIP source when it saves, and two of those
rewrites have to be undone before a release:

- **It persists the current `DataFilePath` value** into
  `SemanticModel/definition/expressions.tmdl`. Whatever path you last used is
  written into the source. Reset the default to `""` before committing, or you
  publish your own folder structure and hand every new user a default that
  points nowhere on their machine.
- **It strips the `$schema` properties** from `Report/definition.pbir` and
  `SemanticModel/definition.pbism`. The repository's validation requires them,
  and Fabric rejects PBIR definition files without them.

So run the validation **after the last Desktop save**, not before, and restore
both entries if they are gone:

```
powerbi-report-author validate powerbi/Sustainable_Raw_Material_Benchmarking.Report
```

Expected: 0 errors.

Desktop also moves the parameter between `model.tmdl` and `expressions.tmdl`.
That relocation is normal — `expressions.tmdl` is Desktop's own canonical
location for it, and the release requirement is only that its default is empty.

---

Method, pipeline and report: **Csaba Bakay**. All data shipped with this
repository is synthetic.
