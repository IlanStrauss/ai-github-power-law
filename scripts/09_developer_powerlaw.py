#!/usr/bin/env python3
"""
Power Law Analysis for Strict Developer Filter

Runs power law estimation on accounts that are likely human developers:
- ≥10 commits/year (excludes casual contributors)
- ≥3 repos (excludes single-project automation)
- ≤10,000 commits/year (excludes extreme automation)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import powerlaw

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
INTERMEDIATE_DIR = OUTPUT_DIR / "intermediate"


def load_developer_data():
    """Load per-developer data with repo counts."""
    parquet_files = list(INTERMEDIATE_DIR.glob("year_*_developers.parquet"))

    if not parquet_files:
        raise FileNotFoundError("No developer parquet files found")

    dfs = []
    for f in parquet_files:
        df = pd.read_parquet(f)
        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)


def fit_power_law(commits: np.ndarray) -> dict:
    """Fit power law and compare to log-normal."""
    if len(commits) < 100:
        return None

    fit = powerlaw.Fit(commits, discrete=True, verbose=False)

    # Compare to log-normal
    R, p = fit.distribution_compare('power_law', 'lognormal', normalized_ratio=True)

    return {
        "alpha": fit.power_law.alpha,
        "xmin": fit.power_law.xmin,
        "R_vs_lognormal": R,
        "p_value": p
    }


def compute_concentration(commits: np.ndarray) -> dict:
    """Compute concentration metrics."""
    n = len(commits)
    total = commits.sum()

    sorted_commits = np.sort(commits)[::-1]

    # Top 1% share
    top_1pct_n = max(1, int(n * 0.01))
    top_1pct_share = sorted_commits[:top_1pct_n].sum() / total * 100

    # Top 10% share
    top_10pct_n = max(1, int(n * 0.10))
    top_10pct_share = sorted_commits[:top_10pct_n].sum() / total * 100

    # Gini
    cumsum = np.cumsum(sorted_commits[::-1])
    gini = 1 - 2 * cumsum.sum() / (n * total)

    return {
        "n_accounts": n,
        "total_commits": int(total),
        "mean_commits": commits.mean(),
        "median_commits": np.median(commits),
        "p90_commits": np.percentile(commits, 90),
        "p99_commits": np.percentile(commits, 99),
        "top_1pct_share": top_1pct_share,
        "top_10pct_share": top_10pct_share,
        "gini": gini,
        "p99_p50_ratio": np.percentile(commits, 99) / np.median(commits)
    }


def main():
    print("=" * 70)
    print("POWER LAW ANALYSIS: STRICT DEVELOPER FILTER")
    print("=" * 70)

    df = load_developer_data()
    print(f"\nLoaded {len(df):,} developer-year records")

    # Define filters
    filters = {
        "multi_repo": {"min_repos": 2, "min_commits": 3, "max_commits": 10000},
        "strict_developer": {"min_repos": 3, "min_commits": 10, "max_commits": 10000},
        "very_strict": {"min_repos": 4, "min_commits": 20, "max_commits": 10000},
    }

    all_results = []

    for filter_name, criteria in filters.items():
        print(f"\n{'='*70}")
        print(f"FILTER: {filter_name}")
        print(f"  min_repos >= {criteria['min_repos']}")
        print(f"  min_commits >= {criteria['min_commits']}")
        print(f"  max_commits <= {criteria['max_commits']}")
        print("=" * 70)

        for year in sorted(df["year"].unique()):
            year_data = df[df["year"] == year].copy()

            # Apply filter
            filtered = year_data[
                (year_data["n_repos"] >= criteria["min_repos"]) &
                (year_data["total_commits"] >= criteria["min_commits"]) &
                (year_data["total_commits"] <= criteria["max_commits"])
            ]

            if len(filtered) < 100:
                print(f"  {year}: Only {len(filtered)} accounts, skipping")
                continue

            commits = filtered["total_commits"].values

            # Concentration metrics
            conc = compute_concentration(commits)

            # Power law
            pl = fit_power_law(commits)

            result = {
                "year": year,
                "filter": filter_name,
                **conc
            }

            if pl:
                result["powerlaw_alpha"] = pl["alpha"]
                result["powerlaw_xmin"] = pl["xmin"]
                result["powerlaw_vs_lognormal_R"] = pl["R_vs_lognormal"]
                result["powerlaw_vs_lognormal_p"] = pl["p_value"]

            all_results.append(result)

            print(f"  {year}: n={conc['n_accounts']:,}, α={pl['alpha']:.2f}, "
                  f"Top 1%={conc['top_1pct_share']:.1f}%, Gini={conc['gini']:.3f}")

    # Save results
    results_df = pd.DataFrame(all_results)
    output_file = OUTPUT_DIR / "developer_powerlaw_analysis.csv"
    results_df.to_csv(output_file, index=False)
    print(f"\n\nSaved to: {output_file}")

    # Summary comparison
    print("\n" + "=" * 70)
    print("COMPARISON: Power Law α by Filter")
    print("=" * 70)

    pivot = results_df.pivot_table(
        index="year",
        columns="filter",
        values="powerlaw_alpha"
    )
    print(pivot.round(2).to_string())

    print("\n" + "=" * 70)
    print("COMPARISON: Top 1% Share by Filter")
    print("=" * 70)

    pivot2 = results_df.pivot_table(
        index="year",
        columns="filter",
        values="top_1pct_share"
    )
    print(pivot2.round(1).to_string())


if __name__ == "__main__":
    main()
