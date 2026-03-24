#!/usr/bin/env python3
"""
Counterfactual α Analysis: Sensitivity to Tail Exclusion

Re-estimate power law α after dropping the top 0.1%, 1%, and 5% of accounts.
This quantifies how much findings depend on extreme accounts vs broad distributional shift.
"""

import pandas as pd
import numpy as np
import powerlaw
from pathlib import Path

# Config
OUTPUT_DIR = Path("output")
YEARS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]
TAIL_CUTS = [0, 0.1, 1, 5]  # Percentages to drop from top

def load_data():
    """Load developer data for all years."""
    # 2019-2024 from parquet
    df_main = pd.read_parquet(OUTPUT_DIR / "all_developers_filtered.parquet")

    # 2025 from CSV
    df_2025 = pd.read_csv(OUTPUT_DIR / "filtered_developers_2025.csv")
    df_2025 = df_2025.rename(columns={"actor": "actor_login"})

    # Combine
    df = pd.concat([
        df_main[["actor_login", "total_commits", "n_repos", "year"]],
        df_2025[["actor_login", "total_commits", "n_repos", "year"]]
    ], ignore_index=True)

    return df

def estimate_alpha(commits, xmin=None):
    """Estimate power law α using Clauset-Shalizi-Newman method."""
    if len(commits) < 50:
        return np.nan, np.nan

    try:
        fit = powerlaw.Fit(commits, discrete=True, verbose=False)
        return fit.alpha, fit.xmin
    except Exception:
        return np.nan, np.nan

def run_counterfactual_analysis(df):
    """Run counterfactual α estimation dropping top percentiles."""
    results = []

    for year in YEARS:
        year_data = df[df["year"] == year].copy()

        # Apply multi-repo filter (n_repos >= 2)
        year_data = year_data[year_data["n_repos"] >= 2]

        # Apply commit filters (3 <= commits <= 10000)
        year_data = year_data[
            (year_data["total_commits"] >= 3) &
            (year_data["total_commits"] <= 10000)
        ]

        commits_full = year_data["total_commits"].values
        n_full = len(commits_full)

        if n_full < 100:
            print(f"Skipping {year}: insufficient data ({n_full})")
            continue

        for pct in TAIL_CUTS:
            if pct == 0:
                # Baseline - no trimming
                commits = commits_full
                n_dropped = 0
            else:
                # Drop top pct%
                threshold = np.percentile(commits_full, 100 - pct)
                commits = commits_full[commits_full <= threshold]
                n_dropped = n_full - len(commits)

            alpha, xmin = estimate_alpha(commits)

            results.append({
                "year": year,
                "tail_cut_pct": pct,
                "n_original": n_full,
                "n_dropped": n_dropped,
                "n_remaining": len(commits),
                "threshold": np.percentile(commits_full, 100 - pct) if pct > 0 else np.nan,
                "alpha": alpha,
                "xmin": xmin
            })

            print(f"{year} | Drop top {pct:>4.1f}% | n={len(commits):>6,} | α={alpha:.3f}")

    return pd.DataFrame(results)

def create_summary_table(results_df):
    """Create pivot table for README."""
    # Pivot: years as rows, tail cuts as columns
    pivot = results_df.pivot(index="year", columns="tail_cut_pct", values="alpha")
    pivot.columns = [f"α (drop {c}%)" if c > 0 else "α (baseline)" for c in pivot.columns]

    # Add change columns
    baseline = results_df[results_df["tail_cut_pct"] == 0].set_index("year")["alpha"]

    for pct in [0.1, 1, 5]:
        trimmed = results_df[results_df["tail_cut_pct"] == pct].set_index("year")["alpha"]
        pivot[f"Δα ({pct}%)"] = trimmed - baseline

    return pivot

def main():
    print("=" * 60)
    print("Counterfactual α Analysis: Sensitivity to Tail Exclusion")
    print("=" * 60)

    # Load data
    print("\nLoading data...")
    df = load_data()
    print(f"Total observations: {len(df):,}")

    # Run analysis
    print("\nRunning counterfactual analysis...")
    print("-" * 60)
    results = run_counterfactual_analysis(df)

    # Save detailed results
    results.to_csv(OUTPUT_DIR / "counterfactual_alpha.csv", index=False)
    print(f"\nSaved: {OUTPUT_DIR / 'counterfactual_alpha.csv'}")

    # Create summary
    print("\n" + "=" * 60)
    print("SUMMARY: α Sensitivity to Tail Exclusion")
    print("=" * 60)

    summary = create_summary_table(results)
    print(summary.round(3).to_string())

    # Key finding
    print("\n" + "-" * 60)
    print("KEY FINDING:")

    baseline_2019 = results[(results["year"] == 2019) & (results["tail_cut_pct"] == 0)]["alpha"].values[0]
    baseline_2024 = results[(results["year"] == 2024) & (results["tail_cut_pct"] == 0)]["alpha"].values[0]
    drop5_2019 = results[(results["year"] == 2019) & (results["tail_cut_pct"] == 5)]["alpha"].values[0]
    drop5_2024 = results[(results["year"] == 2024) & (results["tail_cut_pct"] == 5)]["alpha"].values[0]

    baseline_change = baseline_2024 - baseline_2019
    drop5_change = drop5_2024 - drop5_2019

    print(f"  Baseline Δα (2019→2024): {baseline_change:+.3f}")
    print(f"  Drop 5%  Δα (2019→2024): {drop5_change:+.3f}")
    print(f"  Ratio: {drop5_change/baseline_change:.1%} of baseline change persists after dropping top 5%")

    if abs(drop5_change) > abs(baseline_change) * 0.5:
        print("\n  → Concentration is a BROAD distributional shift, not driven by outliers.")
    else:
        print("\n  → Concentration is SENSITIVE to extreme accounts.")

if __name__ == "__main__":
    main()
