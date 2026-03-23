#!/usr/bin/env python3
"""
Power Law Analysis from Sampled GH Archive Data.

This script works with data downloaded directly from GH Archive
(using 01a_download_gharchive_direct.py) rather than BigQuery.

Methodology follows best practices from:
    - Kalliamvakou et al. (2014/2016) "Promises and Perils of Mining GitHub"
    - Dey et al. (2020) "Detecting and Characterizing Bots that Commit Code"

Sampling approach:
    - Download 4 hours per day (00:00, 06:00, 12:00, 18:00 UTC)
    - Sample 1 day per month (first of month)
    - Captures global activity across time zones

Quality filters applied:
    1. Bot accounts: 15+ patterns ([bot], dependabot, renovate, etc.)
    2. Distinct commits only: Uses distinct_size to filter merge commits
    3. Minimum activity: 3 commits/year (filters inactive accounts)
    4. Behavioral ceiling: >10K commits/year excluded (likely automation)

IMPORTANT: This version processes YEAR-BY-YEAR with incremental saves!

Usage:
    python 02a_power_law_from_sample.py
"""

import gzip
import json
from collections import defaultdict
from pathlib import Path
import gc

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

try:
    import powerlaw
    HAS_POWERLAW = True
except ImportError:
    HAS_POWERLAW = False
    print("Warning: 'powerlaw' package not installed. Install with: pip install powerlaw")

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
OUTPUT_DIR = PROJECT_ROOT / "output"
INTERMEDIATE_DIR = OUTPUT_DIR / "intermediate"

# Sample definition: minimum commits to be considered an "active" developer
# This filters out inactive/casual accounts that inflate the denominator
# (Kalliamvakou et al.: 50% of users have <10 commits total)
MIN_COMMITS = 3

# Behavioral filter: Maximum commits/year before flagging as potential bot/automation
# Pattern matching alone failed for 2024 (2.84M commit account survived filters)
MAX_COMMITS_PER_YEAR = 10000

# Bot patterns from MSR literature (Dey et al. 2020, Golzadeh et al. 2021)
BOT_PATTERNS = [
    "[bot]",           # GitHub Apps: dependabot[bot], renovate[bot]
    "-bot",            # Common suffix: my-ci-bot
    "dependabot",      # Dependency updates
    "renovate",        # Dependency updates
    "github-actions",  # CI/CD
    "codecov",         # Coverage bots
    "greenkeeper",     # Legacy dependency bot
    "snyk",            # Security scanning
    "imgbot",          # Image optimization
    "allcontributors", # Contributor recognition
    "semantic-release",# Release automation
    "pre-commit",      # Pre-commit CI
    "mergify",         # PR automation
    "stale",           # Stale issue bot
    "coveralls",       # Coverage
]


def get_files_by_year() -> dict:
    """Group data files by year for incremental processing."""
    files = sorted(RAW_DIR.glob("*.json.gz"))
    if not files:
        raise FileNotFoundError(f"No files in {RAW_DIR}")

    files_by_year = defaultdict(list)
    for f in files:
        # Filename: YYYY-MM-DD-H.json.gz
        year = int(f.name.split("-")[0])
        files_by_year[year].append(f)

    return dict(files_by_year)


def extract_year_data(files: list, year: int) -> pd.DataFrame:
    """
    Extract commit data for a single year.

    Returns DataFrame with: actor_login, repo_name, commits (aggregated per push event)
    """
    # Use dict for faster aggregation than building list of records
    # Key: (actor_login, repo_name), Value: total commits
    commit_counts = defaultdict(int)

    print(f"  Processing {len(files)} files for {year}...")

    for filepath in files:
        with gzip.open(filepath, "rt", encoding="utf-8") as f:
            for line in f:
                try:
                    event = json.loads(line)

                    if event.get("type") != "PushEvent":
                        continue

                    actor = event.get("actor", {}).get("login")
                    if not actor:
                        continue

                    # Skip bots (comprehensive pattern matching)
                    actor_lower = actor.lower()
                    if any(bot in actor_lower for bot in BOT_PATTERNS):
                        continue

                    payload = event.get("payload", {})

                    # Use distinct_size to filter merge commits
                    distinct_commits = payload.get("distinct_size", 0)
                    total_commits = payload.get("size", 0)
                    commits = distinct_commits if distinct_commits > 0 else total_commits

                    if commits > 0:
                        repo_name = event.get("repo", {}).get("name", "unknown")
                        commit_counts[(actor, repo_name)] += commits

                except json.JSONDecodeError:
                    continue

        print(f"    {filepath.name}: {len(commit_counts):,} unique (actor, repo) pairs")

    # Convert to DataFrame
    if not commit_counts:
        return pd.DataFrame(columns=["actor_login", "repo_name", "commits"])

    df = pd.DataFrame([
        {"actor_login": k[0], "repo_name": k[1], "commits": v}
        for k, v in commit_counts.items()
    ])

    return df


def aggregate_developer_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate to developer level with diversity metrics.

    Input: DataFrame with actor_login, repo_name, commits
    Output: DataFrame with actor_login, total_commits, n_repos, top_repo_share
    """
    if df.empty:
        return pd.DataFrame(columns=["actor_login", "total_commits", "n_repos", "top_repo_share"])

    # Group by developer and calculate metrics efficiently
    dev_stats = df.groupby("actor_login").agg(
        total_commits=("commits", "sum"),
        n_repos=("repo_name", "nunique"),
        max_repo_commits=("commits", "max")
    ).reset_index()

    # Calculate top repo share
    dev_stats["top_repo_share"] = dev_stats["max_repo_commits"] / dev_stats["total_commits"]
    dev_stats = dev_stats.drop(columns=["max_repo_commits"])

    return dev_stats


def fit_power_law_to_year(commits: np.ndarray, year: int) -> dict:
    """Fit power law to a single year's commit distribution."""
    result = {
        "year": year,
        "n_developers": len(commits),
        "median_commits": np.median(commits),
        "mean_commits": np.mean(commits),
        "max_commits": np.max(commits),
        "p90_commits": np.percentile(commits, 90),
        "p99_commits": np.percentile(commits, 99),
    }

    # Top share metrics
    sorted_commits = np.sort(commits)[::-1]
    total = sorted_commits.sum()
    n = len(sorted_commits)

    result["top_1pct_share"] = sorted_commits[: max(1, int(n * 0.01))].sum() / total
    result["top_10pct_share"] = sorted_commits[: max(1, int(n * 0.10))].sum() / total

    # Gini coefficient
    result["gini"] = (2 * np.sum((np.arange(1, n + 1) * sorted_commits[::-1])) / (n * total)) - (
        n + 1
    ) / n

    # P99/P50 ratio
    result["p99_p50_ratio"] = result["p99_commits"] / result["median_commits"]

    # Power law fit (if package available)
    if HAS_POWERLAW:
        try:
            fit = powerlaw.Fit(commits, discrete=True, verbose=False)
            result["alpha"] = fit.power_law.alpha
            result["alpha_se"] = fit.power_law.sigma
            result["xmin"] = fit.power_law.xmin
            result["n_tail"] = np.sum(commits >= fit.power_law.xmin)

            # Compare to log-normal
            R, p = fit.distribution_compare("power_law", "lognormal", normalized_ratio=True)
            result["R_vs_lognormal"] = R
            result["p_vs_lognormal"] = p
        except Exception as e:
            print(f"    Power law fit failed: {e}")
            result["alpha"] = np.nan

    return result


def process_single_year(year: int, files: list) -> tuple:
    """
    Process a single year completely: extract, aggregate, filter, analyze.

    Returns: (year_stats_dict, dev_year_df, monorepo_stats_dict)
    """
    print(f"\n{'='*50}")
    print(f"Processing {year}")
    print(f"{'='*50}")

    # Step 1: Extract raw data
    raw_df = extract_year_data(files, year)
    print(f"  Raw records (actor, repo pairs): {len(raw_df):,}")

    if raw_df.empty:
        return None, None, None

    # Step 2: Aggregate to developer level
    dev_df = aggregate_developer_stats(raw_df)
    print(f"  Unique developers (raw): {len(dev_df):,}")

    # Free memory
    del raw_df
    gc.collect()

    # Step 3: Apply filters

    # Filter 1: Minimum activity
    n_before = len(dev_df)
    dev_df = dev_df[dev_df["total_commits"] >= MIN_COMMITS]
    n_low = n_before - len(dev_df)
    print(f"  After min {MIN_COMMITS} commits filter: {len(dev_df):,} (removed {n_low:,})")

    # Filter 2: Behavioral ceiling (likely bots)
    outliers = dev_df[dev_df["total_commits"] > MAX_COMMITS_PER_YEAR]
    if len(outliers) > 0:
        print(f"  WARNING: {len(outliers)} accounts exceed {MAX_COMMITS_PER_YEAR:,} commits:")
        for _, row in outliers.head(5).iterrows():
            print(f"    {row['actor_login']}: {int(row['total_commits']):,} commits, "
                  f"{int(row['n_repos'])} repos, {row['top_repo_share']*100:.1f}% in top repo")
        dev_df = dev_df[dev_df["total_commits"] <= MAX_COMMITS_PER_YEAR]

    if dev_df.empty:
        print(f"  No developers remaining after filters!")
        return None, None, None

    # Add year column for combined output
    dev_df["year"] = year

    # Step 4: Monorepo stats (for robustness)
    monorepo = dev_df[dev_df["top_repo_share"] >= 0.95]
    diverse = dev_df[dev_df["top_repo_share"] < 0.95]
    monorepo_stats = {
        "year": year,
        "n_total": len(dev_df),
        "n_monorepo": len(monorepo),
        "n_diverse": len(diverse),
        "pct_monorepo": len(monorepo) / len(dev_df) * 100 if len(dev_df) > 0 else 0,
        "monorepo_commits": monorepo["total_commits"].sum(),
        "diverse_commits": diverse["total_commits"].sum(),
    }
    print(f"  Monorepo accounts (95%+ in single repo): {len(monorepo):,} ({monorepo_stats['pct_monorepo']:.1f}%)")

    # Step 5: Fit power law
    commits = dev_df["total_commits"].values
    if len(commits) >= 100:
        year_stats = fit_power_law_to_year(commits, year)
        print(f"  Top 1% share: {year_stats['top_1pct_share']*100:.1f}%")
        print(f"  Gini: {year_stats['gini']:.3f}")
    else:
        print(f"  Too few developers ({len(commits)}) for power law fit")
        year_stats = None

    return year_stats, dev_df, monorepo_stats


def plot_results(results_df: pd.DataFrame, output_dir: Path):
    """Generate visualization of results."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    years = results_df["year"]

    # Plot 1: Top 1% and 10% share
    ax1 = axes[0, 0]
    ax1.plot(years, results_df["top_1pct_share"] * 100, marker="o", linewidth=2, label="Top 1%")
    ax1.plot(years, results_df["top_10pct_share"] * 100, marker="s", linewidth=2, label="Top 10%")
    ax1.axvline(x=2022, color="red", linestyle="--", alpha=0.7, label="Copilot GA")
    ax1.set_xlabel("Year")
    ax1.set_ylabel("Share of Total Commits (%)")
    ax1.set_title("Commit Concentration Over Time")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Power law alpha (if available)
    ax2 = axes[0, 1]
    if "alpha" in results_df.columns and results_df["alpha"].notna().any():
        ax2.errorbar(
            years,
            results_df["alpha"],
            yerr=results_df.get("alpha_se", 0) * 1.96,
            marker="o",
            capsize=4,
            linewidth=2,
        )
        ax2.axvline(x=2022, color="red", linestyle="--", alpha=0.7, label="Copilot GA")
        ax2.set_xlabel("Year")
        ax2.set_ylabel("Power Law α")
        ax2.set_title("Power Law Exponent\n(Lower = More Inequality)")
        ax2.legend()
    else:
        ax2.text(
            0.5,
            0.5,
            "Install 'powerlaw' package\nfor α estimation",
            ha="center",
            va="center",
            transform=ax2.transAxes,
        )
    ax2.grid(True, alpha=0.3)

    # Plot 3: Gini coefficient
    ax3 = axes[1, 0]
    ax3.plot(years, results_df["gini"], marker="^", linewidth=2, color="purple")
    ax3.axvline(x=2022, color="red", linestyle="--", alpha=0.7, label="Copilot GA")
    ax3.set_xlabel("Year")
    ax3.set_ylabel("Gini Coefficient")
    ax3.set_title("Commit Inequality (Gini)\nHigher = More Unequal")
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # Plot 4: P99/P50 ratio
    ax4 = axes[1, 1]
    ax4.plot(years, results_df["p99_p50_ratio"], marker="D", linewidth=2, color="orange")
    ax4.axvline(x=2022, color="red", linestyle="--", alpha=0.7, label="Copilot GA")
    ax4.set_xlabel("Year")
    ax4.set_ylabel("P99 / P50 Ratio")
    ax4.set_title("Tail Heaviness: 99th Percentile vs Median")
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()

    output_path = output_dir / "power_law_analysis_sample.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Saved plot to: {output_path}")


def main():
    print("=" * 60)
    print("Power Law Analysis from Sampled GH Archive Data")
    print("=" * 60)
    print("Processing YEAR-BY-YEAR with incremental saves")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)

    # Check for data
    if not RAW_DIR.exists() or not list(RAW_DIR.glob("*.json.gz")):
        print(f"\nNo data files found in {RAW_DIR}")
        return

    # Get files organized by year
    files_by_year = get_files_by_year()
    print(f"\nFound data for years: {sorted(files_by_year.keys())}")
    print(f"Total files: {sum(len(f) for f in files_by_year.values())}")

    # Check for existing intermediate results
    existing_results = list(INTERMEDIATE_DIR.glob("year_*.csv"))
    existing_years = {int(f.stem.split("_")[1]) for f in existing_results}
    print(f"Existing intermediate results for: {sorted(existing_years) if existing_years else 'none'}")

    # Process each year
    all_results = []
    all_dev_dfs = []
    all_monorepo_stats = []

    for year in sorted(files_by_year.keys()):
        # Check if we already have this year's results
        year_file = INTERMEDIATE_DIR / f"year_{year}_stats.csv"
        dev_file = INTERMEDIATE_DIR / f"year_{year}_developers.parquet"

        if year_file.exists() and dev_file.exists():
            print(f"\n{'='*50}")
            print(f"Loading cached results for {year}")
            print(f"{'='*50}")

            year_stats = pd.read_csv(year_file).to_dict('records')[0]
            dev_df = pd.read_parquet(dev_file)

            # Reconstruct monorepo stats
            monorepo = dev_df[dev_df["top_repo_share"] >= 0.95]
            diverse = dev_df[dev_df["top_repo_share"] < 0.95]
            monorepo_stats = {
                "year": year,
                "n_total": len(dev_df),
                "n_monorepo": len(monorepo),
                "n_diverse": len(diverse),
                "pct_monorepo": len(monorepo) / len(dev_df) * 100 if len(dev_df) > 0 else 0,
                "monorepo_commits": monorepo["total_commits"].sum(),
                "diverse_commits": diverse["total_commits"].sum(),
            }

            all_results.append(year_stats)
            all_dev_dfs.append(dev_df)
            all_monorepo_stats.append(monorepo_stats)

            print(f"  Loaded {len(dev_df):,} developers, top_1pct_share: {year_stats['top_1pct_share']*100:.1f}%")
            continue

        # Process this year
        year_stats, dev_df, monorepo_stats = process_single_year(year, files_by_year[year])

        if year_stats is not None:
            # Save intermediate results immediately
            pd.DataFrame([year_stats]).to_csv(year_file, index=False)
            dev_df.to_parquet(dev_file, index=False)
            print(f"  SAVED: {year_file.name} and {dev_file.name}")

            all_results.append(year_stats)
            all_dev_dfs.append(dev_df)
            all_monorepo_stats.append(monorepo_stats)

        # Force garbage collection between years
        gc.collect()

    # Combine all results
    if not all_results:
        print("\nNo results to combine!")
        return

    results_df = pd.DataFrame(all_results)

    # Save combined results
    output_path = OUTPUT_DIR / "power_law_results_sample.csv"
    results_df.to_csv(output_path, index=False)
    print(f"\nSaved combined results to: {output_path}")

    # Save monorepo robustness
    monorepo_df = pd.DataFrame(all_monorepo_stats)
    monorepo_df.to_csv(OUTPUT_DIR / "monorepo_robustness.csv", index=False)

    # Save combined developer data
    all_devs = pd.concat(all_dev_dfs, ignore_index=True)
    all_devs.to_parquet(OUTPUT_DIR / "all_developers_filtered.parquet", index=False)
    print(f"Saved {len(all_devs):,} total developer-year observations")

    # Generate plots
    print("\nGenerating plots...")
    plot_results(results_df, OUTPUT_DIR)

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(
        results_df[
            ["year", "n_developers", "top_1pct_share", "gini", "p99_p50_ratio"]
            + (["alpha"] if "alpha" in results_df.columns else [])
        ].to_string(index=False)
    )

    # Simple trend analysis
    if len(results_df) >= 4:
        pre_2022 = results_df[results_df["year"] < 2022]["top_1pct_share"].mean()
        post_2022 = results_df[results_df["year"] >= 2022]["top_1pct_share"].mean()

        print(f"\nTop 1% Share:")
        print(f"  Pre-2022 average:  {pre_2022*100:.1f}%")
        print(f"  Post-2022 average: {post_2022*100:.1f}%")
        print(f"  Change: {(post_2022 - pre_2022)*100:+.1f} pp")


if __name__ == "__main__":
    main()
