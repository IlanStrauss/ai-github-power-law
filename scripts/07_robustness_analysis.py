#!/usr/bin/env python3
"""
Robustness Analysis: Addressing Key Critiques

This script addresses the following concerns:
1. Outlier contamination: Remove top outliers from ALL years consistently
2. Denominator growth: Use metrics that are insensitive to inactive accounts
3. Power law vs log-normal: Properly interpret 2019 R < 0
4. Sensitivity analysis: How do results change under different specifications?

Key insight: Rising concentration could be driven by:
- Numerator effect: Top developers producing more
- Denominator effect: More inactive accounts joining GitHub
We need metrics that isolate the numerator effect.

Usage:
    python 07_robustness_analysis.py
"""

import gzip
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

try:
    import powerlaw
    HAS_POWERLAW = True
except ImportError:
    HAS_POWERLAW = False
    print("Warning: 'powerlaw' package not installed.")

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Baseline sample definition: minimum commits to be considered an "active" developer
MIN_COMMITS = 3


def extract_commits_from_files() -> pd.DataFrame:
    """Extract commit data from downloaded GH Archive files."""
    records = []

    files = sorted(RAW_DIR.glob("*.json.gz"))
    if not files:
        raise FileNotFoundError(f"No files matching in {RAW_DIR}")

    print(f"Processing {len(files)} files...")

    for filepath in files:
        filename = filepath.stem.replace(".json", "")
        date_str = "-".join(filename.split("-")[:3])

        with gzip.open(filepath, "rt", encoding="utf-8") as f:
            for line in f:
                try:
                    event = json.loads(line)
                    if event.get("type") != "PushEvent":
                        continue

                    actor = event.get("actor", {}).get("login")
                    if not actor:
                        continue

                    actor_lower = actor.lower()
                    if any(bot in actor_lower for bot in ["[bot]", "-bot", "dependabot", "renovate", "github-actions"]):
                        continue

                    commits = event.get("payload", {}).get("size", 0)
                    if commits > 0:
                        records.append({
                            "date": date_str,
                            "actor_login": actor,
                            "commits": commits,
                        })
                except json.JSONDecodeError:
                    continue

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    return df


def compute_concentration_metrics(commits_series: pd.Series) -> dict:
    """Compute concentration metrics for a commit distribution."""
    commits = commits_series.values
    commits_sorted = np.sort(commits)[::-1]
    total = commits_sorted.sum()
    n = len(commits_sorted)

    if n == 0 or total == 0:
        return None

    # Top 1% share
    top1_n = max(1, int(n * 0.01))
    top1_share = commits_sorted[:top1_n].sum() / total

    # Gini coefficient
    index = np.arange(1, n + 1)
    gini = (2 * np.sum(index * np.sort(commits)) / (n * total)) - (n + 1) / n

    # Percentiles
    median = np.median(commits)
    p99 = np.percentile(commits, 99)
    p90 = np.percentile(commits, 90)

    return {
        "n_developers": n,
        "total_commits": int(total),
        "median_commits": median,
        "mean_commits": commits.mean(),
        "max_commits": int(commits.max()),
        "p90_commits": p90,
        "p99_commits": p99,
        "top_1pct_share": top1_share,
        "gini": gini,
    }


def sensitivity_to_top_k(dev_commits: pd.DataFrame, year: int, k_values: list = [1, 5, 10, 50, 100]) -> pd.DataFrame:
    """
    How sensitive are results to removing top k accounts?
    """
    year_data = dev_commits[dev_commits["year"] == year].copy()
    year_data = year_data.sort_values("commits", ascending=False)

    results = []
    for k in k_values:
        if k >= len(year_data):
            continue
        trimmed = year_data.iloc[k:]
        metrics = compute_concentration_metrics(trimmed["commits"])
        if metrics:
            metrics["k_removed"] = k
            metrics["year"] = year
            results.append(metrics)

    # Also compute with all data
    all_metrics = compute_concentration_metrics(year_data["commits"])
    if all_metrics:
        all_metrics["k_removed"] = 0
        all_metrics["year"] = year
        results.insert(0, all_metrics)

    return pd.DataFrame(results)


def sensitivity_to_min_commits(dev_commits: pd.DataFrame, year: int, min_values: list = [1, 2, 3, 5, 10]) -> pd.DataFrame:
    """
    How sensitive are results to excluding low-activity accounts?
    This addresses the denominator growth concern.
    """
    year_data = dev_commits[dev_commits["year"] == year]

    results = []
    for min_commits in min_values:
        filtered = year_data[year_data["commits"] >= min_commits]
        metrics = compute_concentration_metrics(filtered["commits"])
        if metrics:
            metrics["min_commits_threshold"] = min_commits
            metrics["year"] = year
            metrics["pct_excluded"] = 1 - len(filtered) / len(year_data)
            results.append(metrics)

    return pd.DataFrame(results)


def compute_denominator_insensitive_metrics(dev_commits: pd.DataFrame, year: int,
                                             min_commits: int = MIN_COMMITS, trim_top_pct: float = 0.001) -> dict:
    """
    Compute metrics that are INSENSITIVE to denominator growth.

    Key idea: Focus on the distribution among ACTIVE contributors only,
    and use rank-based metrics that don't depend on total N.

    Args:
        min_commits: Only include developers with >= this many commits
        trim_top_pct: Remove top X% as outliers (e.g., 0.001 = top 0.1%)
    """
    year_data = dev_commits[dev_commits["year"] == year].copy()

    # Filter to active contributors
    active = year_data[year_data["commits"] >= min_commits].copy()
    n_active = len(active)

    if n_active < 100:
        return None

    # Remove top outliers (top 0.1%)
    n_trim = max(1, int(n_active * trim_top_pct))
    active = active.sort_values("commits", ascending=False).iloc[n_trim:]

    commits = active["commits"].values

    # Percentile ratios (insensitive to denominator)
    p50 = np.percentile(commits, 50)
    p90 = np.percentile(commits, 90)
    p99 = np.percentile(commits, 99)
    p999 = np.percentile(commits, 99.9)

    # Mean among active (not affected by inactive account growth)
    mean_active = commits.mean()

    # Inter-percentile share: What fraction of commits come from top 10% of ACTIVE users?
    top_10_pct_n = max(1, int(len(commits) * 0.10))
    commits_sorted = np.sort(commits)[::-1]
    top_10_pct_share = commits_sorted[:top_10_pct_n].sum() / commits_sorted.sum()

    # Top 1% share among ACTIVE users only
    top_1_pct_n = max(1, int(len(commits) * 0.01))
    top_1_pct_share = commits_sorted[:top_1_pct_n].sum() / commits_sorted.sum()

    return {
        "year": year,
        "n_active": len(active),
        "n_trimmed": n_trim,
        "min_commits_threshold": min_commits,
        "p50": p50,
        "p90": p90,
        "p99": p99,
        "p999": p999,
        "p99_p50_ratio": p99 / p50 if p50 > 0 else np.nan,
        "p90_p50_ratio": p90 / p50 if p50 > 0 else np.nan,
        "mean_among_active": mean_active,
        "top_10pct_share_active": top_10_pct_share,
        "top_1pct_share_active": top_1_pct_share,
        "max_after_trim": int(commits.max()),
    }


def analyze_by_fixed_rank(dev_commits: pd.DataFrame) -> pd.DataFrame:
    """
    Track output of developers at FIXED rank positions over time.

    This is completely insensitive to denominator changes because we look
    at the same rank positions (e.g., #100, #1000, #10000) each year.

    If the top 100 developers are producing more commits over time, that's
    a real numerator effect, not denominator growth.
    """
    results = []

    for year in sorted(dev_commits["year"].unique()):
        year_data = dev_commits[dev_commits["year"] == year].copy()
        year_data = year_data.sort_values("commits", ascending=False).reset_index(drop=True)

        n = len(year_data)

        # Fixed rank positions
        ranks = [10, 50, 100, 500, 1000, 5000, 10000]

        row = {"year": year, "n_total": n}
        for rank in ranks:
            if rank <= n:
                row[f"commits_at_rank_{rank}"] = int(year_data.iloc[rank-1]["commits"])
                # Also: sum of top K
                row[f"sum_top_{rank}"] = int(year_data.iloc[:rank]["commits"].sum())
            else:
                row[f"commits_at_rank_{rank}"] = np.nan
                row[f"sum_top_{rank}"] = np.nan

        results.append(row)

    return pd.DataFrame(results)


def main():
    print("=" * 70)
    print("ROBUSTNESS ANALYSIS: Addressing Key Critiques")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Extract data
    print("\nExtracting data...")
    df = extract_commits_from_files()

    # Aggregate by developer-year
    dev_commits = df.groupby(["year", "actor_login"])["commits"].sum().reset_index()

    # =========================================================================
    # ROBUSTNESS CHECK 1: Sensitivity to removing top outliers
    # =========================================================================
    print("\n" + "=" * 70)
    print("ROBUSTNESS CHECK 1: Sensitivity to Removing Top K Outliers")
    print("=" * 70)

    sensitivity_results = []
    for year in sorted(dev_commits["year"].unique()):
        year_sens = sensitivity_to_top_k(dev_commits, year, k_values=[0, 1, 5, 10, 50, 100])
        sensitivity_results.append(year_sens)

    sens_df = pd.concat(sensitivity_results)
    sens_df.to_csv(OUTPUT_DIR / "robustness_outlier_sensitivity.csv", index=False)

    print("\n2024: Effect of removing top K accounts on Top 1% Share:")
    sens_2024 = sens_df[sens_df["year"] == 2024]
    print(sens_2024[["k_removed", "n_developers", "top_1pct_share", "gini", "max_commits"]].to_string(index=False))

    print("\nKey finding: How much does the 2024 result change when removing top 10 accounts?")
    baseline = sens_2024[sens_2024["k_removed"] == 0].iloc[0]
    trimmed = sens_2024[sens_2024["k_removed"] == 10].iloc[0] if len(sens_2024[sens_2024["k_removed"] == 10]) > 0 else None
    if trimmed is not None:
        print(f"  Top 1% share: {baseline['top_1pct_share']*100:.1f}% -> {trimmed['top_1pct_share']*100:.1f}% (change: {(trimmed['top_1pct_share']-baseline['top_1pct_share'])*100:+.1f} pp)")
        print(f"  Gini: {baseline['gini']:.3f} -> {trimmed['gini']:.3f} (change: {trimmed['gini']-baseline['gini']:+.3f})")
        print(f"  Max commits: {baseline['max_commits']:,} -> {trimmed['max_commits']:,}")

    # =========================================================================
    # ROBUSTNESS CHECK 2: Sensitivity to minimum commit threshold
    # =========================================================================
    print("\n" + "=" * 70)
    print("ROBUSTNESS CHECK 2: Excluding Low-Activity Accounts (Denominator Growth)")
    print("=" * 70)

    min_commit_results = []
    for year in sorted(dev_commits["year"].unique()):
        year_sens = sensitivity_to_min_commits(dev_commits, year, min_values=[1, 2, 3, 5, 10, 20])
        min_commit_results.append(year_sens)

    min_df = pd.concat(min_commit_results)
    min_df.to_csv(OUTPUT_DIR / "robustness_min_commits.csv", index=False)

    print("\nEffect of minimum commit threshold on Top 1% Share:")
    print("\n2019:")
    print(min_df[(min_df["year"] == 2019)][["min_commits_threshold", "n_developers", "pct_excluded", "top_1pct_share", "gini"]].to_string(index=False))

    print("\n2024:")
    print(min_df[(min_df["year"] == 2024)][["min_commits_threshold", "n_developers", "pct_excluded", "top_1pct_share", "gini"]].to_string(index=False))

    # Compare apples to apples: same threshold across years
    print("\n" + "-" * 70)
    print("Comparing years at same minimum commit threshold (min_commits >= 3):")
    print("-" * 70)
    threshold_3 = min_df[min_df["min_commits_threshold"] == 3][["year", "n_developers", "top_1pct_share", "gini"]]
    print(threshold_3.to_string(index=False))

    # =========================================================================
    # ROBUSTNESS CHECK 3: Both adjustments combined
    # =========================================================================
    print("\n" + "=" * 70)
    print("ROBUSTNESS CHECK 3: Combined (Remove Top 10 + Min 3 Commits)")
    print("=" * 70)

    combined_results = []
    for year in sorted(dev_commits["year"].unique()):
        year_data = dev_commits[dev_commits["year"] == year]
        # Filter: min 3 commits
        filtered = year_data[year_data["commits"] >= 3].copy()
        # Filter: remove top 10
        filtered = filtered.sort_values("commits", ascending=False).iloc[10:]

        metrics = compute_concentration_metrics(filtered["commits"])
        if metrics:
            metrics["year"] = year
            combined_results.append(metrics)

    combined_df = pd.DataFrame(combined_results)
    combined_df.to_csv(OUTPUT_DIR / "robustness_combined.csv", index=False)

    print("\nTop 1% share with BOTH adjustments (robust estimate):")
    print(combined_df[["year", "n_developers", "top_1pct_share", "gini"]].to_string(index=False))

    # =========================================================================
    # ROBUSTNESS CHECK 4: Year-over-year changes
    # =========================================================================
    print("\n" + "=" * 70)
    print("CORRECTED NARRATIVE: Year-over-Year Changes")
    print("=" * 70)

    # Baseline (no adjustments)
    baseline_results = []
    for year in sorted(dev_commits["year"].unique()):
        year_data = dev_commits[dev_commits["year"] == year]
        metrics = compute_concentration_metrics(year_data["commits"])
        if metrics:
            metrics["year"] = year
            baseline_results.append(metrics)

    baseline_df = pd.DataFrame(baseline_results)

    print("\nOriginal (potentially contaminated):")
    baseline_df["yoy_change"] = baseline_df["top_1pct_share"].diff() * 100
    print(baseline_df[["year", "top_1pct_share", "yoy_change"]].to_string(index=False))

    print("\nRobust (min 3 commits + top 10 removed):")
    combined_df["yoy_change"] = combined_df["top_1pct_share"].diff() * 100
    print(combined_df[["year", "top_1pct_share", "yoy_change"]].to_string(index=False))

    # =========================================================================
    # ROBUSTNESS CHECK 4: Denominator-Insensitive Metrics
    # =========================================================================
    print("\n" + "=" * 70)
    print("ROBUSTNESS CHECK 4: Denominator-Insensitive Metrics")
    print("=" * 70)
    print("These metrics focus on ACTIVE contributors only (>= 3 commits)")
    print("and trim top 0.1% as outliers from ALL years.\n")

    denom_insensitive = []
    for year in sorted(dev_commits["year"].unique()):
        metrics = compute_denominator_insensitive_metrics(dev_commits, year, min_commits=3, trim_top_pct=0.001)
        if metrics:
            denom_insensitive.append(metrics)

    di_df = pd.DataFrame(denom_insensitive)
    di_df.to_csv(OUTPUT_DIR / "robustness_denom_insensitive.csv", index=False)

    print("Percentile ratios (completely insensitive to inactive account growth):")
    print(di_df[["year", "n_active", "p99_p50_ratio", "p90_p50_ratio", "mean_among_active"]].to_string(index=False))

    print("\nTop 1% share among ACTIVE developers only:")
    print(di_df[["year", "n_active", "top_1pct_share_active", "top_10pct_share_active"]].to_string(index=False))

    # =========================================================================
    # ROBUSTNESS CHECK 5: Fixed Rank Analysis
    # =========================================================================
    print("\n" + "=" * 70)
    print("ROBUSTNESS CHECK 5: Fixed Rank Analysis (Cleanest Test)")
    print("=" * 70)
    print("Track commits at FIXED rank positions over time.")
    print("This is completely insensitive to denominator changes.\n")

    rank_df = analyze_by_fixed_rank(dev_commits)
    rank_df.to_csv(OUTPUT_DIR / "robustness_fixed_rank.csv", index=False)

    print("Commits by the person at rank #100, #1000, #10000 over time:")
    print(rank_df[["year", "commits_at_rank_100", "commits_at_rank_1000", "commits_at_rank_10000"]].to_string(index=False))

    print("\nTotal commits by top 100 and top 1000 developers:")
    print(rank_df[["year", "sum_top_100", "sum_top_1000"]].to_string(index=False))

    # =========================================================================
    # DESCRIPTIVE STATISTICS: Absolute output by top contributors
    # =========================================================================
    print("\n" + "=" * 70)
    print("DESCRIPTIVE STATISTICS: Absolute Output by Top Contributors")
    print("=" * 70)
    print("(Excluding top 10 outliers from each year for clean comparison)\n")

    desc_results = []
    for year in sorted(dev_commits["year"].unique()):
        year_data = dev_commits[dev_commits["year"] == year].copy()
        year_data = year_data.sort_values("commits", ascending=False)

        # Remove top 10 outliers
        clean_data = year_data.iloc[10:]
        n = len(clean_data)
        top_1pct_n = max(1, int(n * 0.01))
        top_100 = clean_data.iloc[:100] if len(clean_data) >= 100 else clean_data

        desc_results.append({
            "year": year,
            "n_developers_clean": n,
            "total_commits_clean": int(clean_data["commits"].sum()),
            "top_100_total_commits": int(top_100["commits"].sum()),
            "top_1pct_total_commits": int(clean_data.iloc[:top_1pct_n]["commits"].sum()),
            "top_100_mean_commits": top_100["commits"].mean(),
            "median_commits_clean": clean_data["commits"].median(),
        })

    desc_df = pd.DataFrame(desc_results)
    desc_df.to_csv(OUTPUT_DIR / "descriptive_stats_clean.csv", index=False)

    print("Absolute commits by top contributors (after removing top 10 outliers):")
    print(desc_df[["year", "top_100_total_commits", "top_1pct_total_commits", "top_100_mean_commits"]].to_string(index=False))

    # Year-over-year growth
    desc_df["top_100_growth_pct"] = desc_df["top_100_total_commits"].pct_change() * 100
    desc_df["top_1pct_growth_pct"] = desc_df["top_1pct_total_commits"].pct_change() * 100

    print("\nYear-over-year growth rates:")
    print(desc_df[["year", "top_100_growth_pct", "top_1pct_growth_pct"]].to_string(index=False))

    # Compute growth rates
    print("\nYear-over-year growth in sum of top 100:")
    rank_df["sum_top_100_growth"] = rank_df["sum_top_100"].pct_change() * 100
    print(rank_df[["year", "sum_top_100", "sum_top_100_growth"]].to_string(index=False))

    # =========================================================================
    # SUMMARY: Which findings survive robustness checks?
    # =========================================================================
    print("\n" + "=" * 70)
    print("SUMMARY: WHICH FINDINGS SURVIVE ROBUSTNESS CHECKS?")
    print("=" * 70)

    # Compare original vs robust top 1% share
    print("\nTop 1% Share Comparison:")
    print(f"{'Year':<6} {'Original':>12} {'Robust*':>12} {'Diff':>10}")
    print("-" * 40)
    for _, row_baseline in baseline_df.iterrows():
        year = row_baseline["year"]
        row_robust = di_df[di_df["year"] == year]
        if len(row_robust) > 0:
            orig = row_baseline["top_1pct_share"] * 100
            robust = row_robust.iloc[0]["top_1pct_share_active"] * 100
            print(f"{year:<6} {orig:>11.1f}% {robust:>11.1f}% {orig-robust:>+9.1f}pp")

    print("\n* Robust = among active developers (>=3 commits), top 0.1% trimmed")

    print("""
KEY TAKEAWAYS:

1. If the ROBUST top 1% share is MUCH lower than original, the original
   estimate was inflated by inactive accounts (denominator effect).

2. If the ROBUST top 1% share is still rising over time, concentration
   is genuinely increasing among active developers (numerator effect).

3. The FIXED RANK analysis is the cleanest test: if commits by the
   person at rank #100 are growing faster than commits by the person
   at rank #10000, that's genuine concentration, not an artifact.

4. Year-over-year changes in sum_top_100 show whether the numerator
   (output by top developers) is actually growing.
""")


if __name__ == "__main__":
    main()
