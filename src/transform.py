"""
Transformation logic (A): raw sources + reference tables -> consolidated
analytical dataset + data-quality log.

Ground truth (validation/ground_truth_consolidated.csv) is NEVER read here.
See src/validate.py for the separate, independent validation step (B).
"""

import argparse
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
REF = ROOT / "data" / "reference"
OUT = ROOT / "data" / "processed"
CONFIG_PATH = ROOT / "config.json"

# Reference years below this threshold are treated as outdated when the PCF
# data-quality tier is derived. Overridable in config.json; see docs/BYOD.md.
DEFAULT_RECENT_PCF_YEAR_THRESHOLD = 2022

# Outputs are written with fixed LF line endings so the same inputs produce
# byte-identical files on Windows, macOS and Linux.
LF = chr(10)


def load_config(path=CONFIG_PATH):
    """Read the optional config file. A missing file means documented defaults."""
    config = {"recent_pcf_year_threshold": DEFAULT_RECENT_PCF_YEAR_THRESHOLD}
    if Path(path).exists():
        with open(path, encoding="utf-8") as handle:
            config.update(json.load(handle))
    return config


RECENT_PCF_YEAR_THRESHOLD = load_config()["recent_pcf_year_threshold"]

# The synthetic demonstration uses the source_* names; the published templates
# use the input_* names. Either is accepted, so a third party can point the
# pipeline at their own folder without renaming anything.
RAW_FILENAMES = {
    "procurement": ("source_procurement.csv", "input_procurement.csv"),
    "technical": ("source_technical_material.csv", "input_technical.csv"),
    "pcf": ("source_pcf_sustainability.csv", "input_pcf.csv"),
}
REFERENCE_FILENAMES = {
    "supplier": "ref_supplier_mapping.csv",
    "material": "ref_material_mapping.csv",
    "country": "ref_country_mapping.csv",
    "pcf_unit": "ref_pcf_unit_conversion.csv",
}


def resolve_input(directory, candidates, label):
    for name in candidates:
        candidate = Path(directory) / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f"{label}: none of {list(candidates)} found in {directory}. "
        "See docs/DATA_DICTIONARY.md for the required input files."
    )


def load_raw(raw_dir=RAW):
    procurement = pd.read_csv(
        resolve_input(raw_dir, RAW_FILENAMES["procurement"], "procurement input"),
        dtype={"annual_volume_kg": "Int64"})
    technical = pd.read_csv(
        resolve_input(raw_dir, RAW_FILENAMES["technical"], "technical input"))
    pcf = pd.read_csv(
        resolve_input(raw_dir, RAW_FILENAMES["pcf"], "PCF input"))
    return procurement, technical, pcf


def load_reference(ref_dir=REF):
    tables = {}
    for key, name in REFERENCE_FILENAMES.items():
        path = Path(ref_dir) / name
        if not path.exists():
            raise FileNotFoundError(
                f"Reference table '{name}' not found in {ref_dir}. "
                "See docs/DATA_DICTIONARY.md for the four required mapping tables."
            )
        tables[key] = pd.read_csv(path)
    return tables


def new_log():
    return []


def log_issue(log, issue_type, source, material_id, supplier_id, original_value,
              harmonized_value_or_action, severity, explanation):
    log.append({
        "issue_type": issue_type,
        "source": source,
        "material_id": material_id,
        "supplier_id": supplier_id,
        "original_value": original_value,
        "harmonized_value_or_action": harmonized_value_or_action,
        "severity": severity,
        "explanation": explanation,
    })


def resolve_duplicate_procurement_records(procurement, technical, log,
                                          source_label="procurement input",
                                          technical_label="the technical input"):
    """Detect procurement rows sharing a material_id (duplicate vendor-code
    entries) and keep only the row whose supplier_id matches the
    authoritative supplier_id on record in the technical source."""
    authoritative_supplier = technical.set_index("material_id")["supplier_id"]
    counts = procurement["material_id"].value_counts()
    duplicated_material_ids = counts[counts > 1].index.tolist()

    keep_mask = pd.Series(True, index=procurement.index)
    for material_id in duplicated_material_ids:
        cluster = procurement[procurement["material_id"] == material_id]
        keep_supplier_id = authoritative_supplier.get(material_id)
        drop_rows = cluster[cluster["supplier_id"] != keep_supplier_id]
        keep_rows = cluster[cluster["supplier_id"] == keep_supplier_id]

        # Confirm the dropped row(s) carry identical commercial figures, so
        # dropping them (rather than summing) cannot double- or under-count
        # volume/spend.
        identical = True
        if not keep_rows.empty:
            reference_row = keep_rows.iloc[0]
            compare_cols = ["material_name_procurement", "supplier_name", "supplier_country",
                             "sourcing_status", "annual_volume_kg", "price_per_kg", "currency"]
            identical = bool((drop_rows[compare_cols] == reference_row[compare_cols]).all(axis=1).all())

        for _, row in drop_rows.iterrows():
            keep_mask.loc[row.name] = False
            log_issue(
                log, "duplicate_procurement_record", source_label,
                material_id, row["supplier_id"],
                original_value=f"supplier_id={row['supplier_id']} (duplicate of {keep_supplier_id})",
                harmonized_value_or_action=(
                    f"dropped; kept supplier_id={keep_supplier_id} "
                    f"(matches {technical_label}); figures identical={identical}, "
                    "no volume/spend adjustment needed"
                ),
                severity="resolved",
                explanation="Vendor-code migration produced a second procurement row for the "
                            "same material/supplier relationship; deduplicated using the "
                            "technical source's supplier_id as the authoritative reference.",
            )

    return procurement[keep_mask].reset_index(drop=True)


def harmonize_material_name(df, name_col, source_label, material_ref, log, id_col):
    mapping = material_ref.set_index("raw_material_name")["material_name_canonical"]
    harmonized = df[name_col].map(mapping)
    unmapped = harmonized.isna()
    if unmapped.any():
        raise ValueError(f"{source_label}: unmapped material name(s): "
                          f"{df.loc[unmapped, name_col].unique().tolist()}")
    df = df.copy()
    df["material_name_canonical"] = harmonized
    drift = df[name_col] != df["material_name_canonical"]
    for _, row in df[drift].iterrows():
        log_issue(
            log, "material_naming_inconsistency", source_label,
            row.get(id_col, ""), row.get("supplier_id", ""),
            original_value=row[name_col],
            harmonized_value_or_action=row["material_name_canonical"],
            severity="resolved",
            explanation="Free-text material description differed from the canonical name; "
                        "resolved via ref_material_mapping.csv (exact deterministic lookup).",
        )
    return df


def harmonize_supplier_name(df, name_col, source_label, supplier_ref, log, id_col):
    mapping_id = supplier_ref.set_index("raw_supplier_name")["supplier_id_canonical"]
    mapping_name = supplier_ref.set_index("raw_supplier_name")["supplier_name_canonical"]
    supplier_id_canonical = df[name_col].map(mapping_id)
    supplier_name_canonical = df[name_col].map(mapping_name)
    unmapped = supplier_id_canonical.isna()
    if unmapped.any():
        raise ValueError(f"{source_label}: unmapped supplier name(s): "
                          f"{df.loc[unmapped, name_col].unique().tolist()}")
    df = df.copy()
    df["supplier_id_canonical"] = supplier_id_canonical
    df["supplier_name_canonical"] = supplier_name_canonical
    drift = df[name_col] != df["supplier_name_canonical"]
    for _, row in df[drift].iterrows():
        log_issue(
            log, "supplier_naming_inconsistency", source_label,
            row.get(id_col, ""), row["supplier_id_canonical"],
            original_value=row[name_col],
            harmonized_value_or_action=row["supplier_name_canonical"],
            severity="resolved",
            explanation="Supplier name spelling/legal-suffix differed from the canonical name; "
                        "resolved via ref_supplier_mapping.csv (exact deterministic lookup).",
        )
    return df


def harmonize_country(df, country_col, source_label, country_ref, log, id_col):
    mapping_name = country_ref.set_index("raw_country_value")["country_name_canonical"]
    mapping_iso2 = country_ref.set_index("raw_country_value")["country_iso2_canonical"]
    canonical_name = df[country_col].map(mapping_name)
    canonical_iso2 = df[country_col].map(mapping_iso2)
    unmapped = canonical_name.isna()
    if unmapped.any():
        raise ValueError(f"{source_label}: unmapped country value(s): "
                          f"{df.loc[unmapped, country_col].unique().tolist()}")
    df = df.copy()
    df["country_name_canonical"] = canonical_name
    df["country_iso2_canonical"] = canonical_iso2
    drift = df[country_col] != df["country_name_canonical"]
    for _, row in df[drift].iterrows():
        log_issue(
            log, "country_representation_inconsistency", source_label,
            row.get(id_col, ""), row.get("supplier_id_canonical", row.get("supplier_id", "")),
            original_value=row[country_col],
            harmonized_value_or_action=row["country_name_canonical"],
            severity="resolved",
            explanation="Country was given as an ISO code instead of the full name used "
                        "elsewhere; resolved via ref_country_mapping.csv.",
        )
    return df


def normalize_pcf_units(pcf, unit_ref, log, source_label="PCF input"):
    mapping = unit_ref.set_index("pcf_unit_basis")["multiplier_to_kgco2e_per_kg"]
    multiplier = pcf["pcf_unit_basis"].map(mapping)
    unmapped = multiplier.isna() & pcf["pcf_unit_basis"].notna()
    if unmapped.any():
        raise ValueError(f"Unmapped pcf_unit_basis value(s): "
                          f"{pcf.loc[unmapped, 'pcf_unit_basis'].unique().tolist()}")
    pcf = pcf.copy()
    pcf["pcf_kgco2e_per_kg"] = pcf["pcf_value"] * multiplier
    non_standard = pcf["pcf_unit_basis"] != "kg CO2e/kg"
    for _, row in pcf[non_standard].iterrows():
        log_issue(
            log, "pcf_unit_basis_inconsistency", source_label,
            "", row["supplier_id_canonical"],
            original_value=f"{row['pcf_value']} {row['pcf_unit_basis']}",
            harmonized_value_or_action=f"{row['pcf_kgco2e_per_kg']:.2f} kg CO2e/kg "
                                        f"(x{multiplier[row.name]})",
            severity="resolved",
            explanation="PCF was reported on a non-standard unit basis; converted via "
                        "ref_pcf_unit_conversion.csv before any comparison.",
        )
    return pcf


def classify_pcf_quality(row):
    if not row["has_pcf_data"]:
        return "No data"
    is_primary = row["pcf_data_type"] == "Supplier-specific (primary)"
    is_recent = pd.notna(row["pcf_reference_year"]) and row["pcf_reference_year"] >= RECENT_PCF_YEAR_THRESHOLD
    return "High confidence" if (is_primary and is_recent) else "Low confidence"


def build_pipeline(raw_dir=RAW, ref_dir=REF):
    log = new_log()
    procurement, technical, pcf = load_raw(raw_dir)
    ref = load_reference(ref_dir)
    # Error messages and the data-quality log name the file the user actually
    # supplied, not a fixed filename.
    src_name = {k: resolve_input(raw_dir, v, k).name for k, v in RAW_FILENAMES.items()}

    # 1. Duplicate detection/resolution (procurement only)
    procurement = resolve_duplicate_procurement_records(
        procurement, technical, log, src_name["procurement"], src_name["technical"])

    # 2. Harmonization (deterministic lookups only, no fuzzy matching)
    procurement = harmonize_material_name(procurement, "material_name_procurement",
                                           src_name["procurement"], ref["material"], log, "material_id")
    procurement = harmonize_supplier_name(procurement, "supplier_name",
                                           src_name["procurement"], ref["supplier"], log, "material_id")
    procurement = harmonize_country(procurement, "supplier_country",
                                     src_name["procurement"], ref["country"], log, "material_id")

    technical = harmonize_material_name(technical, "material_name_technical",
                                         src_name["technical"], ref["material"], log, "material_id")

    pcf = harmonize_material_name(pcf, "material_name_pcf",
                                   src_name["pcf"], ref["material"], log, "pcf_record_id")
    pcf = harmonize_supplier_name(pcf, "supplier_name_pcf",
                                   src_name["pcf"], ref["supplier"], log, "pcf_record_id")
    pcf = harmonize_country(pcf, "supplier_country_pcf",
                             src_name["pcf"], ref["country"], log, "pcf_record_id")
    pcf = normalize_pcf_units(pcf, ref["pcf_unit"], log, src_name["pcf"])

    # 3. Consolidate base table: procurement + technical, joined on the
    # canonical (material_id, supplier_id) business key.
    base = procurement.merge(
        technical, on=["material_id", "supplier_id"], how="inner",
        suffixes=("_proc", "_tech"), validate="one_to_one",
    )
    if len(base) != len(procurement) or len(base) != len(technical):
        raise ValueError("Procurement/Technical join did not produce a clean 1:1 match.")

    base["material_name"] = base["material_name_canonical_tech"]
    base["supplier_name"] = base["supplier_name_canonical"]
    base["supplier_country"] = base["country_name_canonical"]

    # Cross-check: procurement's harmonized material name should agree with
    # technical's, now that both have gone through the same mapping table.
    disagreement = base["material_name_canonical_proc"] != base["material_name_canonical_tech"]
    for _, row in base[disagreement].iterrows():
        log_issue(
            log, "material_naming_inconsistency", "cross-source check",
            row["material_id"], row["supplier_id"],
            original_value=(row["material_name_canonical_proc"], row["material_name_canonical_tech"]),
            harmonized_value_or_action="manual review required",
            severity="unresolved",
            explanation="Procurement and Technical still disagree on material identity after "
                        "harmonization.",
        )

    # 4. Attach PCF on the full business key: canonical supplier AND canonical
    # material name. A PCF declaration belongs to one supplier and one material,
    # so joining on the supplier alone would attach the same declaration to
    # every material that supplier delivers. Columns are renamed with a pcf_
    # prefix before the merge so they cannot collide with the base table's own
    # harmonization columns of the same name.
    pcf_slim = pcf[["supplier_id_canonical", "material_name_canonical", "pcf_kgco2e_per_kg",
                    "pcf_data_type", "pcf_reference_year", "pcf_data_quality_note"]].rename(columns={
        "supplier_id_canonical": "pcf_join_supplier_id",
        "material_name_canonical": "pcf_join_material_name",
    })

    ambiguous = pcf_slim.duplicated(
        subset=["pcf_join_supplier_id", "pcf_join_material_name"], keep=False)
    if ambiguous.any():
        pairs = (pcf_slim.loc[ambiguous, ["pcf_join_supplier_id", "pcf_join_material_name"]]
                 .drop_duplicates().to_string(index=False))
        raise ValueError(
            "Ambiguous PCF records: more than one declaration exists for the same "
            "supplier/material pair, so none can be assigned without guessing. "
            "Keep exactly one declaration per supplier/material pair.\n"
            f"Affected pairs:\n{pairs}"
        )

    consolidated = base.merge(
        pcf_slim,
        left_on=["supplier_id", "material_name_canonical_tech"],
        right_on=["pcf_join_supplier_id", "pcf_join_material_name"],
        how="left", validate="one_to_one",
    )
    consolidated["has_pcf_data"] = consolidated["pcf_join_supplier_id"].notna()

    missing_pcf = ~consolidated["has_pcf_data"]
    for _, row in consolidated[missing_pcf].iterrows():
        log_issue(
            log, "missing_pcf_value", src_name["pcf"],
            row["material_id"], row["supplier_id"],
            original_value="(no PCF record found)",
            harmonized_value_or_action="preserved as missing; pcf_kgco2e_per_kg left null, "
                                        "not imputed",
            severity="open",
            explanation="No PCF declaration exists yet for this supplier/material; the gap is "
                        "carried into the analytical dataset rather than estimated.",
        )

    # Reverse check: PCF declarations that matched no supplier/material pair in
    # the base table. These are not silently dropped, they are reported.
    matched_keys = set(zip(
        consolidated.loc[consolidated["has_pcf_data"], "supplier_id"],
        consolidated.loc[consolidated["has_pcf_data"], "material_name_canonical_tech"],
    ))
    for _, row in pcf_slim.iterrows():
        if (row["pcf_join_supplier_id"], row["pcf_join_material_name"]) in matched_keys:
            continue
        log_issue(
            log, "unmatched_pcf_record", src_name["pcf"],
            "", row["pcf_join_supplier_id"],
            original_value=f"{row['pcf_join_supplier_id']} / {row['pcf_join_material_name']}",
            harmonized_value_or_action="not attached to any material; manual review required",
            severity="unresolved",
            explanation="A PCF declaration exists for a supplier/material pair that is not "
                        "present in the procurement and technical inputs.",
        )

    # 5. PCF data-quality tier + outdated-reference-year flag
    consolidated["pcf_data_quality_tier"] = consolidated.apply(classify_pcf_quality, axis=1)
    outdated = consolidated["has_pcf_data"] & (consolidated["pcf_reference_year"] < RECENT_PCF_YEAR_THRESHOLD)
    for _, row in consolidated[outdated].iterrows():
        log_issue(
            log, "inconsistent_outdated_pcf_reference_year", src_name["pcf"],
            row["material_id"], row["supplier_id"],
            original_value=f"pcf_reference_year={int(row['pcf_reference_year'])}, "
                            f"pcf_data_type={row['pcf_data_type']}",
            harmonized_value_or_action=f"pcf_data_quality_tier={row['pcf_data_quality_tier']}",
            severity="open",
            explanation=f"Reference year is older than {RECENT_PCF_YEAR_THRESHOLD} and/or the "
                        "value is secondary data; value is kept but flagged low-confidence, "
                        "never silently treated as equivalent to current primary data.",
        )

    # 6. Technical qualification gate (deterministic, not a score)
    consolidated["technically_eligible"] = consolidated["technical_approval_status"] == "Approved"

    # 7. Calculated fields
    consolidated["price_eur_per_kg"] = consolidated["price_per_kg"]
    consolidated["annual_spend_eur"] = consolidated["annual_volume_kg"] * consolidated["price_eur_per_kg"]
    consolidated["annual_co2e_kg"] = consolidated["annual_volume_kg"] * consolidated["pcf_kgco2e_per_kg"]

    baseline_rows = consolidated[consolidated["sourcing_status"] == "Current"]
    baseline_spend = baseline_rows.set_index("comparison_case_id")["annual_spend_eur"]
    baseline_co2e = baseline_rows.set_index("comparison_case_id")["annual_co2e_kg"]

    case = consolidated["comparison_case_id"]
    consolidated["cost_delta_vs_baseline_eur"] = consolidated["annual_spend_eur"] - case.map(baseline_spend)
    consolidated["cost_delta_pct_vs_baseline"] = (
        consolidated["cost_delta_vs_baseline_eur"] / case.map(baseline_spend) * 100
    )
    consolidated["co2e_delta_vs_baseline_kg"] = consolidated["annual_co2e_kg"] - case.map(baseline_co2e)
    consolidated["co2e_delta_pct_vs_baseline"] = (
        consolidated["co2e_delta_vs_baseline_kg"] / case.map(baseline_co2e) * 100
    )

    # 8. Presentation rounding (internal calculations above stay full precision)
    consolidated["price_eur_per_kg"] = consolidated["price_eur_per_kg"].round(2)
    consolidated["pcf_kgco2e_per_kg"] = consolidated["pcf_kgco2e_per_kg"].round(2)
    consolidated["annual_spend_eur"] = consolidated["annual_spend_eur"].round(0)
    consolidated["annual_co2e_kg"] = consolidated["annual_co2e_kg"].round(0)
    consolidated["cost_delta_vs_baseline_eur"] = consolidated["cost_delta_vs_baseline_eur"].round(0)
    consolidated["cost_delta_pct_vs_baseline"] = consolidated["cost_delta_pct_vs_baseline"].round(1)
    consolidated["co2e_delta_vs_baseline_kg"] = consolidated["co2e_delta_vs_baseline_kg"].round(0)
    consolidated["co2e_delta_pct_vs_baseline"] = consolidated["co2e_delta_pct_vs_baseline"].round(1)

    output_columns = [
        "comparison_case_id", "material_group", "material_id", "material_name",
        "supplier_id", "supplier_name", "supplier_country", "sourcing_status",
        "annual_volume_kg", "price_eur_per_kg", "currency", "annual_spend_eur",
        "technical_approval_status", "technically_eligible",
        "pcf_kgco2e_per_kg", "pcf_data_type", "pcf_reference_year",
        "pcf_data_quality_tier", "has_pcf_data", "annual_co2e_kg",
        "cost_delta_vs_baseline_eur", "cost_delta_pct_vs_baseline",
        "co2e_delta_vs_baseline_kg", "co2e_delta_pct_vs_baseline",
        "physical_form", "purity_pct", "boiling_point_c", "viscosity_cst",
        "density_g_cm3", "active_content_pct", "ph_value",
    ]
    consolidated = consolidated[output_columns].sort_values(
        ["comparison_case_id", "sourcing_status"], ascending=[True, False]
    ).reset_index(drop=True)

    dq_log = pd.DataFrame(log, columns=[
        "issue_type", "source", "material_id", "supplier_id",
        "original_value", "harmonized_value_or_action", "severity", "explanation",
    ])

    return consolidated, dq_log


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Build the consolidated benchmark dataset and the data-quality log.")
    parser.add_argument("--raw", default=RAW, type=Path,
                        help="folder holding the three input files (default: data/raw)")
    parser.add_argument("--ref", default=REF, type=Path,
                        help="folder holding the four reference tables (default: data/reference)")
    parser.add_argument("--out", default=OUT, type=Path,
                        help="folder to write the outputs to (default: data/processed)")
    args = parser.parse_args(argv)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    consolidated, dq_log = build_pipeline(args.raw, args.ref)
    # Fixed LF line endings keep the output byte-reproducible on every platform.
    consolidated.to_csv(out_dir / "consolidated_material_benchmark.csv",
                        index=False, lineterminator=LF)
    dq_log.to_csv(out_dir / "data_quality_log.csv", index=False, lineterminator=LF)

    print(f"Consolidated dataset: {len(consolidated)} rows, {len(consolidated.columns)} columns "
          f"-> {out_dir / 'consolidated_material_benchmark.csv'}")
    print(f"Data-quality log: {len(dq_log)} entries -> {out_dir / 'data_quality_log.csv'}")
    print()
    print("Issues by type:")
    print(dq_log["issue_type"].value_counts().to_string())


if __name__ == "__main__":
    main()
