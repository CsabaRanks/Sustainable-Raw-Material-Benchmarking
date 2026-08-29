"""
Synthetic-demonstration regression test.

Compares the independently produced consolidated dataset against the approved
ground truth for the SYNTHETIC DEMONSTRATION DATASET ONLY, and reconstructs the
five decision stories that dataset was authored to carry.

This test is meaningful only for the demonstration data shipped with the
repository. If you have replaced the inputs with your own data, run
`python src/validate.py` instead -- your data is not expected to reproduce the
demonstration ground truth.

This is the ONLY module allowed to read validation/ground_truth_consolidated.csv.
It must never be imported by src/transform.py, and the ground truth must never
be consulted while transform.py is building the consolidated dataset.
"""

from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed" / "consolidated_material_benchmark.csv"
GROUND_TRUTH = ROOT / "validation" / "ground_truth_consolidated.csv"

NUMERIC_TOLERANCES = {
    "annual_volume_kg": 0.5,
    "price_eur_per_kg": 0.01,
    "annual_spend_eur": 1,
    "pcf_kgco2e_per_kg": 0.01,
    "annual_co2e_kg": 1,
    "cost_delta_vs_baseline_eur": 1,
    "cost_delta_pct_vs_baseline": 0.1,
    "co2e_delta_vs_baseline_kg": 1,
    "co2e_delta_pct_vs_baseline": 0.1,
}
CATEGORICAL_COLUMNS = [
    "comparison_case_id", "material_group", "material_name", "supplier_name",
    "supplier_country", "sourcing_status", "currency", "technical_approval_status",
    "technically_eligible", "pcf_data_type", "pcf_reference_year",
    "pcf_data_quality_tier", "has_pcf_data",
]


def load():
    result = pd.read_csv(PROCESSED)
    truth = pd.read_csv(GROUND_TRUTH)
    return result, truth


def check(label, condition, details=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}" + (f" -- {details}" if details and not condition else ""))
    return condition


def compare_values(result, truth):
    merged = result.merge(truth, on=["material_id", "supplier_id"], how="outer",
                           suffixes=("_result", "_truth"), indicator=True)
    all_ok = True

    only_result = merged[merged["_merge"] == "left_only"]
    only_truth = merged[merged["_merge"] == "right_only"]
    all_ok &= check("Every ground-truth alternative is present in the result",
                     only_truth.empty, f"missing: {only_truth['material_id'].tolist()}")
    all_ok &= check("No unexpected extra alternatives in the result",
                     only_result.empty, f"unexpected: {only_result['material_id'].tolist()}")

    both = merged[merged["_merge"] == "both"]
    mismatches = []

    def resolve_cols(col):
        r, t = f"{col}_result", f"{col}_truth"
        return (r, t) if r in both.columns else (col, col)

    def both_nan(r, t):
        return both[r].isna() & both[t].isna()

    for col in CATEGORICAL_COLUMNS:
        r, t = resolve_cols(col)
        equal = (both[r] == both[t]) | both_nan(r, t)
        diff = both[~equal]
        if not diff.empty:
            mismatches.append((col, diff[["material_id", r, t]]))

    for col, tol in NUMERIC_TOLERANCES.items():
        r, t = resolve_cols(col)
        within_tol = ((both[r] - both[t]).abs() <= tol) | both_nan(r, t)
        diff = both[~within_tol]
        if not diff.empty:
            mismatches.append((col, diff[["material_id", r, t]]))

    all_ok &= check("All field values match ground truth within tolerance", not mismatches)
    for col, diff in mismatches:
        print(f"    discrepancy in '{col}':")
        print(diff.to_string(index=False, max_rows=10).replace("\n", "\n    "))

    return all_ok


def check_no_double_counting(result):
    dupes = result.duplicated(subset=["material_id", "supplier_id"]).sum()
    return check("No double-counted (material_id, supplier_id) rows", dupes == 0,
                 f"{dupes} duplicate key(s) found")


def check_decision_stories(result):
    all_ok = True

    a = result[result["comparison_case_id"] == "CASE-A"]
    a_alt = a[(a["sourcing_status"] == "Alternative") & a["technically_eligible"]]
    win_win = a_alt[(a_alt["cost_delta_vs_baseline_eur"] < 0) & (a_alt["co2e_delta_vs_baseline_kg"] < 0)]
    all_ok &= check("Base Oils (CASE-A): a technically eligible win-win alternative exists",
                     len(win_win) >= 1)

    b = result[result["comparison_case_id"] == "CASE-B"]
    b_alt = b[(b["sourcing_status"] == "Alternative") & b["technically_eligible"]]
    b_no_win_win = b_alt[(b_alt["cost_delta_vs_baseline_eur"] < 0) & (b_alt["co2e_delta_vs_baseline_kg"] < 0)]
    cheapest = b_alt.loc[b_alt["annual_spend_eur"].idxmin()]
    lowest_co2e = b_alt.loc[b_alt["annual_co2e_kg"].idxmin()]
    all_ok &= check("Solvents (CASE-B): no alternative beats baseline on both cost and carbon",
                     b_no_win_win.empty)
    all_ok &= check("Solvents (CASE-B): cheapest alternative has a worse PCF than baseline",
                     cheapest["co2e_delta_vs_baseline_kg"] > 0)
    all_ok &= check("Solvents (CASE-B): lowest-carbon alternative costs more than baseline",
                     lowest_co2e["cost_delta_vs_baseline_eur"] > 0)

    c = result[result["comparison_case_id"] == "CASE-C"]
    low_conf_carbon_winner = c[(c["co2e_delta_vs_baseline_kg"] < -30000) &
                                (c["pcf_data_quality_tier"] != "High confidence")]
    no_data_row = c[~c["has_pcf_data"]]
    all_ok &= check("Surfactants (CASE-C): the apparent carbon winner is flagged low-confidence",
                     len(low_conf_carbon_winner) >= 1)
    all_ok &= check("Surfactants (CASE-C): at least one alternative has no PCF data",
                     len(no_data_row) >= 1)

    d = result[result["comparison_case_id"] == "CASE-D"]
    best_numbers = d.loc[d["annual_spend_eur"].idxmin()]
    best_eligible = d[(d["sourcing_status"] == "Alternative") & d["technically_eligible"]]
    best_eligible_row = best_eligible.loc[best_eligible["annual_spend_eur"].idxmin()]
    all_ok &= check("Polymer Additives (CASE-D): the cheapest overall alternative is NOT technically eligible",
                     not bool(best_numbers["technically_eligible"]))
    all_ok &= check("Polymer Additives (CASE-D): best technically eligible alternative is a distinct, "
                     "more modest improvement",
                     best_eligible_row["cost_delta_vs_baseline_eur"] > best_numbers["cost_delta_vs_baseline_eur"])

    e = result[result["comparison_case_id"] == "CASE-E"]
    e_alt = e[e["sourcing_status"] == "Alternative"]
    ambiguous = (e_alt["cost_delta_pct_vs_baseline"].abs() < 5) & (e_alt["co2e_delta_pct_vs_baseline"].abs() < 10)
    all_ok &= check("Resins/Binders (CASE-E): all alternatives stay within a narrow band of baseline "
                     "(no dominant winner)", ambiguous.all())

    return all_ok


def main():
    result, truth = load()
    print("=== Structural checks ===")
    ok = check("Consolidated result has exactly 25 rows", len(result) == 25, f"got {len(result)}")
    ok &= check_no_double_counting(result)

    print("\n=== Ground-truth comparison ===")
    ok &= compare_values(result, truth)

    print("\n=== Decision-story reconstruction ===")
    ok &= check_decision_stories(result)

    print("\n" + ("ALL VALIDATION CHECKS PASSED" if ok else "VALIDATION FAILED — see discrepancies above"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
