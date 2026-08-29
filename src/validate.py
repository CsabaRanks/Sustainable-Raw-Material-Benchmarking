"""
General input validation — works with any dataset, including your own.

Checks the three input files and the four reference tables against the
contract documented in docs/DATA_DICTIONARY.md, and then checks the
consolidated output (if it exists) against the methodological rules the
benchmark depends on.

This module deliberately knows nothing about the synthetic demonstration
dataset and never reads validation/ground_truth_consolidated.csv. To run the
regression test for the shipped demonstration data, use
`python src/validate_demo.py` instead.

    python src/validate.py
    python src/validate.py --raw data/templates --ref data/templates --out data/templates/processed

Exit code 0 = every check passed, 1 = at least one check failed.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from transform import (  # noqa: E402
    RAW, REF, OUT, RAW_FILENAMES, REFERENCE_FILENAMES, resolve_input,
)

SOURCING_STATUS_VALUES = {"Current", "Alternative"}

REQUIRED_COLUMNS = {
    "procurement": ["material_id", "material_name_procurement", "supplier_id",
                    "supplier_name", "supplier_country", "sourcing_status",
                    "annual_volume_kg", "price_per_kg", "currency"],
    "technical": ["material_id", "supplier_id", "material_group", "comparison_case_id",
                  "material_name_technical", "technical_approval_status"],
    "pcf": ["pcf_record_id", "supplier_name_pcf", "supplier_country_pcf",
            "material_name_pcf", "pcf_value", "pcf_unit_basis", "pcf_data_type",
            "pcf_reference_year"],
}

FAILURES = []


def check(label, condition, detail=""):
    ok = bool(condition)
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f"\n       {detail}" if detail and not ok else ""))
    if not ok:
        FAILURES.append(label)
    return ok


# ── input contract ───────────────────────────────────────────────────────
def check_columns(frames):
    for key, frame in frames.items():
        missing = [c for c in REQUIRED_COLUMNS[key] if c not in frame.columns]
        check(f"{key}: all required columns present", not missing,
              f"missing: {missing}")


def check_vocabularies(procurement, technical, pcf, reference):
    bad = sorted(set(procurement["sourcing_status"].dropna()) - SOURCING_STATUS_VALUES)
    check("procurement: sourcing_status uses only 'Current' or 'Alternative'", not bad,
          f"unexpected value(s): {bad}. Values are case-sensitive.")

    blank = technical["technical_approval_status"].isna().sum()
    check("technical: technical_approval_status is populated on every row", blank == 0,
          f"{blank} row(s) have no approval status. Only the exact value 'Approved' "
          "makes an alternative technically eligible.")

    known_units = set(reference["pcf_unit"]["pcf_unit_basis"])
    unmapped = sorted(set(pcf["pcf_unit_basis"].dropna()) - known_units)
    check("PCF: every pcf_unit_basis is present in ref_pcf_unit_conversion.csv", not unmapped,
          f"unmapped unit(s): {unmapped}. Add a conversion row for each.")


def check_reference_coverage(procurement, technical, pcf, reference):
    materials = set(reference["material"]["raw_material_name"])
    suppliers = set(reference["supplier"]["raw_supplier_name"])
    countries = set(reference["country"]["raw_country_value"])

    for label, values, known, table in [
        ("procurement material names", procurement["material_name_procurement"], materials, "ref_material_mapping.csv"),
        ("technical material names", technical["material_name_technical"], materials, "ref_material_mapping.csv"),
        ("PCF material names", pcf["material_name_pcf"], materials, "ref_material_mapping.csv"),
        ("procurement supplier names", procurement["supplier_name"], suppliers, "ref_supplier_mapping.csv"),
        ("PCF supplier names", pcf["supplier_name_pcf"], suppliers, "ref_supplier_mapping.csv"),
        ("procurement countries", procurement["supplier_country"], countries, "ref_country_mapping.csv"),
        ("PCF countries", pcf["supplier_country_pcf"], countries, "ref_country_mapping.csv"),
    ]:
        unmapped = sorted(set(values.dropna()) - known)
        check(f"{label}: every value is mapped", not unmapped,
              f"add these to {table}: {unmapped}")


def check_keys_and_cases(procurement, technical):
    dupes = procurement.duplicated(subset=["material_id", "supplier_id"]).sum()
    check("procurement: (material_id, supplier_id) is unique", dupes == 0,
          f"{dupes} duplicate key(s). Duplicate vendor codes for the same material "
          "are resolved by the pipeline only when the technical input names the "
          "authoritative supplier_id.")

    dupes = technical.duplicated(subset=["material_id", "supplier_id"]).sum()
    check("technical: (material_id, supplier_id) is unique", dupes == 0,
          f"{dupes} duplicate key(s)")

    merged = procurement.merge(technical, on=["material_id", "supplier_id"], how="outer",
                               indicator=True)
    matched_materials = set(merged[merged["_merge"] == "both"]["material_id"])

    # A procurement row that does not match the technical supplier_id is only a
    # problem if its material has no matching row at all. Where the material does
    # match on another row, the unmatched row is a duplicate vendor code, which
    # the pipeline resolves against the technical source.
    unmatched = merged[merged["_merge"] == "left_only"]
    orphans = sorted(set(unmatched["material_id"]) - matched_materials)
    resolvable = sorted(set(unmatched["material_id"]) & matched_materials)
    check("every procurement material has a technical record", not orphans,
          f"no technical record for: {orphans}")
    if resolvable:
        print(f"       note: duplicate vendor code(s) for {resolvable} will be "
              "resolved against the technical source")

    only_tech = merged[merged["_merge"] == "right_only"]["material_id"].tolist()
    check("every technical row has a procurement row", not only_tech,
          f"no procurement record for: {only_tech}")

    both = merged[merged["_merge"] == "both"]
    for case_id, group in both.groupby("comparison_case_id"):
        n_current = (group["sourcing_status"] == "Current").sum()
        check(f"case {case_id}: exactly one 'Current' incumbent", n_current == 1,
              f"found {n_current}. Each comparison case needs exactly one incumbent "
              "because every delta is measured against it.")
        check(f"case {case_id}: at least one alternative to compare", len(group) >= 2,
              f"only {len(group)} material(s) in this case")


def check_measures(procurement, pcf):
    bad = procurement[procurement["annual_volume_kg"].fillna(0) <= 0]
    check("procurement: annual_volume_kg is positive on every row", bad.empty,
          f"non-positive volume for: {bad['material_id'].tolist()}")

    bad = procurement[procurement["price_per_kg"].fillna(0) <= 0]
    check("procurement: price_per_kg is positive on every row", bad.empty,
          f"non-positive price for: {bad['material_id'].tolist()}")

    currencies = sorted(procurement["currency"].dropna().unique())
    check("procurement: a single currency is used", len(currencies) <= 1,
          f"found {currencies}. The pipeline does not convert currencies; "
          "spend figures from different currencies are not comparable.")

    bad = pcf[pcf["pcf_value"].fillna(0) < 0]
    check("PCF: no negative pcf_value", bad.empty,
          f"negative value for: {bad['pcf_record_id'].tolist()}")

    years = pcf["pcf_reference_year"].dropna()
    implausible = years[(years < 1990) | (years > 2100)]
    check("PCF: reference years are plausible", implausible.empty,
          f"implausible year(s): {sorted(implausible.unique().tolist())}")

    dupes = pcf.duplicated(subset=["supplier_name_pcf", "material_name_pcf"]).sum()
    check("PCF: at most one declaration per supplier/material pair", dupes == 0,
          f"{dupes} ambiguous pair(s). The pipeline refuses to choose between "
          "competing declarations for the same supplier and material.")


# ── output rules ─────────────────────────────────────────────────────────
def check_output_rules(result):
    missing = result[~result["has_pcf_data"].astype(bool)]
    check("output: missing PCF stays missing, never zero",
          missing["pcf_kgco2e_per_kg"].isna().all() and missing["annual_co2e_kg"].isna().all(),
          "a row without PCF data carries a numeric carbon value; it must stay empty")
    check("output: a missing carbon delta is undefined, not zero",
          missing["co2e_delta_vs_baseline_kg"].isna().all(),
          "a row without PCF data carries a carbon delta")
    check("output: rows without PCF remain in the cost comparison",
          missing.empty or missing["annual_spend_eur"].notna().all(),
          "a row without PCF data lost its spend figure")

    ineligible = result[~result["technically_eligible"].astype(bool)]
    check("output: technically ineligible alternatives remain visible",
          ineligible.empty or ineligible["annual_spend_eur"].notna().all(),
          "an ineligible alternative was dropped instead of being flagged")

    for case_id, group in result.groupby("comparison_case_id"):
        base = group[group["sourcing_status"] == "Current"]
        check(f"output: case {case_id} has exactly one incumbent", len(base) == 1,
              f"found {len(base)}")
        if len(base) == 1:
            check(f"output: case {case_id} incumbent has a zero cost delta",
                  abs(float(base.iloc[0]["cost_delta_vs_baseline_eur"])) < 1e-6,
                  "the incumbent is the reference and must sit at zero")

    dupes = result.duplicated(subset=["material_id", "supplier_id"]).sum()
    check("output: no double-counted (material_id, supplier_id) rows", dupes == 0,
          f"{dupes} duplicate key(s)")

    forbidden = [c for c in result.columns
                 if any(t in c.lower() for t in ("score", "rank", "weight", "index"))]
    check("output: no score, rank or weight column has been introduced", not forbidden,
          f"unexpected column(s): {forbidden}")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate input files, reference tables and the consolidated output.")
    parser.add_argument("--raw", default=RAW, type=Path)
    parser.add_argument("--ref", default=REF, type=Path)
    parser.add_argument("--out", default=OUT, type=Path)
    args = parser.parse_args(argv)

    print("=== Input files ===")
    frames = {}
    for key in ("procurement", "technical", "pcf"):
        path = resolve_input(args.raw, RAW_FILENAMES[key], f"{key} input")
        frames[key] = pd.read_csv(path)
        print(f"[PASS] {key}: {path.name} ({len(frames[key])} rows)")

    reference = {}
    for key, name in REFERENCE_FILENAMES.items():
        reference[key] = pd.read_csv(Path(args.ref) / name)
        print(f"[PASS] reference: {name} ({len(reference[key])} rows)")

    print("\n=== Required columns ===")
    check_columns(frames)

    print("\n=== Controlled vocabularies ===")
    check_vocabularies(frames["procurement"], frames["technical"], frames["pcf"], reference)

    print("\n=== Reference-table coverage ===")
    check_reference_coverage(frames["procurement"], frames["technical"], frames["pcf"], reference)

    print("\n=== Keys and comparison cases ===")
    check_keys_and_cases(frames["procurement"], frames["technical"])

    print("\n=== Measures ===")
    check_measures(frames["procurement"], frames["pcf"])

    output_path = Path(args.out) / "consolidated_material_benchmark.csv"
    if output_path.exists():
        print("\n=== Consolidated output ===")
        check_output_rules(pd.read_csv(output_path))
    else:
        print(f"\n=== Consolidated output ===\n[SKIP] {output_path} not found. "
              "Run src/transform.py first to check the output rules as well.")

    print()
    if FAILURES:
        print(f"VALIDATION FAILED — {len(FAILURES)} check(s) did not pass:")
        for f in FAILURES:
            print(f"  - {f}")
        sys.exit(1)
    print("ALL VALIDATION CHECKS PASSED")
    sys.exit(0)


if __name__ == "__main__":
    main()
