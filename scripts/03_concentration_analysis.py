#!/usr/bin/env python3
"""
Concentration Analysis of GitHub Activity.

This script analyzes various concentration metrics to test whether
GitHub activity is becoming more concentrated over time.

Metrics:
    - Top N% share of commits
    - Herfindahl-Hirschman Index (HHI)
    - Gini coefficient
    - Lorenz curve analysis

Usage:
    python 03_concentration_analysis.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"


def load_yearly_stats() -> pd.DataFrame:
    """Load yearly distribution statistics."""
    path = DATA_DIR / "yearly_distribution_stats.csv"

    if not path.exists():
        raise FileNotFoundError(
            f"Data file not found: {path}\n"
            "Run 01_fetch_from_bigquery.py first."
        )

    return pd.read_csv(path)


def load_repo_concentration() -> pd.DataFrame:
    """Load repository concentration data."""
    path = DATA_DIR / "repo_concentration_hhi.csv"

    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")

    return pd.read_csv(path)


def load_persistence_data() -> pd.DataFrame:
    """Load top developer persistence data."""
    path = DATA_DIR / "top_developer_persistence.csv"

    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")

    return pd.read_csv(path)


def load_velocity_data() -> pd.DataFrame:
    """Load pre/post Copilot velocity data."""
    path = DATA_DIR / "velocity_change_pre_post.csv"

    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")

    return pd.read_csv(path)


def analyze_concentration_trends(stats_df: pd.DataFrame) -> pd.DataFrame:
    """Analyze trends in concentration metrics over time."""
    # Calculate year-over-year changes
    stats_df = stats_df.sort_values("year").copy()

    stats_df["top_1pct_share_pct"] = stats_df["top_1pct_share"] * 100
    stats_df["top_10pct_share_pct"] = stats_df["top_10pct_share"] * 100

    # Linear regression for trend
    years = stats_df["year"].values
    top1_share = stats_df["top_1pct_share_pct"].values

    slope, intercept, r_value, p_value, std_err = stats.linregress(years, top1_share)

    trend_result = {
        "metric": "top_1pct_share",
        "slope_per_year": slope,
        "r_squared": r_value**2,
        "p_value": p_value,
        "interpretation": (
            f"Top 1% share {'increasing' if slope > 0 else 'decreasing'} "
            f"by {abs(slope):.2f} pp/year"
        ),
    }

    print("\nConcentration Trend Analysis:")
    print(f"  Top 1% share trend: {slope:.3f} pp/year")
    print(f"  R² = {r_value**2:.3f}, p = {p_value:.4f}")

    return pd.DataFrame([trend_result])


def plot_concentration_metrics(stats_df: pd.DataFrame, output_path: Path):
    """Plot concentration metrics over time."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Plot 1: Top 1% and 10% share
    ax1 = axes[0, 0]
    ax1.plot(
        stats_df["year"],
        stats_df["top_1pct_share"] * 100,
        marker="o",
        linewidth=2,
        label="Top 1%",
        color="darkblue",
    )
    ax1.plot(
        stats_df["year"],
        stats_df["top_10pct_share"] * 100,
        marker="s",
        linewidth=2,
        label="Top 10%",
        color="steelblue",
    )
    ax1.axvline(x=2022, color="red", linestyle="--", alpha=0.7, label="Copilot GA")
    ax1.set_xlabel("Year")
    ax1.set_ylabel("Share of Total Commits (%)")
    ax1.set_title("Commit Concentration: Top Developer Shares")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: P99/P50 ratio (inequality within distribution)
    ax2 = axes[0, 1]
    ax2.plot(
        stats_df["year"],
        stats_df["p99_p50_ratio"],
        marker="^",
        linewidth=2,
        color="purple",
    )
    ax2.axvline(x=2022, color="red", linestyle="--", alpha=0.7, label="Copilot GA")
    ax2.set_xlabel("Year")
    ax2.set_ylabel("P99/P50 Ratio")
    ax2.set_title("Commit Inequality: 99th Percentile vs Median")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Plot 3: Total developers and commits
    ax3 = axes[1, 0]
    ax3_twin = ax3.twinx()

    line1 = ax3.plot(
        stats_df["year"],
        stats_df["n_developers"] / 1e6,
        marker="o",
        linewidth=2,
        color="green",
        label="Developers (M)",
    )
    line2 = ax3_twin.plot(
        stats_df["year"],
        stats_df["total_commits"] / 1e9,
        marker="s",
        linewidth=2,
        color="orange",
        label="Commits (B)",
    )

    ax3.axvline(x=2022, color="red", linestyle="--", alpha=0.7)
    ax3.set_xlabel("Year")
    ax3.set_ylabel("Active Developers (Millions)", color="green")
    ax3_twin.set_ylabel("Total Commits (Billions)", color="orange")
    ax3.set_title("GitHub Growth Over Time")

    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax3.legend(lines, labels, loc="upper left")
    ax3.grid(True, alpha=0.3)

    # Plot 4: Percentiles
    ax4 = axes[1, 1]
    ax4.plot(stats_df["year"], stats_df["p50_commits"], marker="o", label="Median (P50)")
    ax4.plot(stats_df["year"], stats_df["p90_commits"], marker="s", label="P90")
    ax4.plot(stats_df["year"], stats_df["p99_commits"], marker="^", label="P99")
    ax4.axvline(x=2022, color="red", linestyle="--", alpha=0.7, label="Copilot GA")
    ax4.set_xlabel("Year")
    ax4.set_ylabel("Commits")
    ax4.set_title("Commit Distribution Percentiles")
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    ax4.set_yscale("log")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Saved concentration plot to: {output_path}")


def plot_repo_concentration(repo_df: pd.DataFrame, output_path: Path):
    """Plot repository-level concentration metrics."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Plot 1: HHI over time
    ax1 = axes[0]
    ax1.plot(repo_df["year"], repo_df["hhi_index"], marker="o", linewidth=2, color="darkred")
    ax1.axvline(x=2022, color="red", linestyle="--", alpha=0.7, label="Copilot GA")
    ax1.set_xlabel("Year")
    ax1.set_ylabel("HHI Index")
    ax1.set_title("Repository Concentration (HHI)\nHigher = More Concentrated")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Top repo shares
    ax2 = axes[1]
    ax2.plot(repo_df["year"], repo_df["top_100_share"] * 100, marker="o", label="Top 100 repos")
    ax2.plot(repo_df["year"], repo_df["top_1000_share"] * 100, marker="s", label="Top 1000 repos")
    ax2.axvline(x=2022, color="red", linestyle="--", alpha=0.7, label="Copilot GA")
    ax2.set_xlabel("Year")
    ax2.set_ylabel("Share of Total Commits (%)")
    ax2.set_title("Top Repository Commit Shares")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Saved repo concentration plot to: {output_path}")


def plot_persistence(persist_df: pd.DataFrame, output_path: Path):
    """Plot top developer persistence over time."""
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(
        persist_df["year_from"],
        persist_df["top_100_retention_rate"] * 100,
        marker="o",
        linewidth=2,
        label="Top 100",
    )
    ax.plot(
        persist_df["year_from"],
        persist_df["top_1000_retention_rate"] * 100,
        marker="s",
        linewidth=2,
        label="Top 1000",
    )
    ax.plot(
        persist_df["year_from"],
        persist_df["top_10000_retention_rate"] * 100,
        marker="^",
        linewidth=2,
        label="Top 10000",
    )

    ax.axvline(x=2022, color="red", linestyle="--", alpha=0.7, label="Copilot GA")
    ax.axhline(y=50, color="gray", linestyle=":", alpha=0.5)

    ax.set_xlabel("Year")
    ax.set_ylabel("Retention Rate (%)")
    ax.set_title(
        "Top Developer Persistence: Year-over-Year Retention\n"
        "(% of top N developers who remain in top N next year)"
    )
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 100)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Saved persistence plot to: {output_path}")


def plot_velocity_change(velocity_df: pd.DataFrame, output_path: Path):
    """Plot velocity change by pre-Copilot productivity decile."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Plot 1: Velocity ratio by decile
    ax1 = axes[0]
    ax1.bar(
        velocity_df["pre_decile"],
        velocity_df["median_velocity_ratio"],
        color="steelblue",
        alpha=0.7,
        label="Median",
    )
    ax1.errorbar(
        velocity_df["pre_decile"],
        velocity_df["median_velocity_ratio"],
        yerr=[
            velocity_df["median_velocity_ratio"] - velocity_df["p25_velocity_ratio"],
            velocity_df["p75_velocity_ratio"] - velocity_df["median_velocity_ratio"],
        ],
        fmt="none",
        color="black",
        capsize=3,
    )
    ax1.axhline(y=1.0, color="red", linestyle="--", label="No change")
    ax1.set_xlabel("Pre-Copilot Productivity Decile\n(1 = lowest, 10 = highest)")
    ax1.set_ylabel("Post/Pre Velocity Ratio")
    ax1.set_title(
        "Commit Velocity Change: Pre (2019-21) vs Post (2022-24) Copilot\n"
        "by Pre-Period Productivity"
    )
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis="y")

    # Plot 2: Absolute commits by decile
    ax2 = axes[1]
    x = np.arange(len(velocity_df))
    width = 0.35

    ax2.bar(x - width / 2, velocity_df["avg_commits_pre"], width, label="Pre-Copilot (2019-21)")
    ax2.bar(x + width / 2, velocity_df["avg_commits_post"], width, label="Post-Copilot (2022-24)")

    ax2.set_xlabel("Pre-Copilot Productivity Decile")
    ax2.set_ylabel("Average Annual Commits")
    ax2.set_title("Average Commits by Productivity Decile")
    ax2.set_xticks(x)
    ax2.set_xticklabels(velocity_df["pre_decile"])
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis="y")
    ax2.set_yscale("log")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Saved velocity plot to: {output_path}")


def main():
    print("=" * 60)
    print("Concentration Analysis of GitHub Activity")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load and analyze yearly stats
    try:
        print("\nLoading yearly distribution statistics...")
        stats_df = load_yearly_stats()
        print(f"Loaded data for years: {stats_df['year'].min()}-{stats_df['year'].max()}")

        trend_results = analyze_concentration_trends(stats_df)
        trend_results.to_csv(OUTPUT_DIR / "concentration_trends.csv", index=False)

        plot_concentration_metrics(stats_df, OUTPUT_DIR / "concentration_metrics.png")

    except FileNotFoundError as e:
        print(f"Warning: {e}")

    # Load and analyze repo concentration
    try:
        print("\nLoading repository concentration data...")
        repo_df = load_repo_concentration()
        plot_repo_concentration(repo_df, OUTPUT_DIR / "repo_concentration.png")

    except FileNotFoundError as e:
        print(f"Warning: {e}")

    # Load and analyze persistence
    try:
        print("\nLoading developer persistence data...")
        persist_df = load_persistence_data()
        plot_persistence(persist_df, OUTPUT_DIR / "developer_persistence.png")

    except FileNotFoundError as e:
        print(f"Warning: {e}")

    # Load and analyze velocity change
    try:
        print("\nLoading velocity change data...")
        velocity_df = load_velocity_data()
        plot_velocity_change(velocity_df, OUTPUT_DIR / "velocity_change.png")

        # Key finding: Do top deciles show larger velocity increases?
        print("\nVelocity Change Summary:")
        print(velocity_df[["pre_decile", "median_velocity_ratio", "n_developers"]].to_string())

    except FileNotFoundError as e:
        print(f"Warning: {e}")

    print("\n" + "=" * 60)
    print("Analysis complete! Check output/ directory for results.")
    print("=" * 60)


if __name__ == "__main__":
    main()
