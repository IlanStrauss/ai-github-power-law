#!/usr/bin/env python3
"""
Publication-Quality Visualizations for GitHub Concentration Analysis.

This script generates clean, publication-ready figures for the research.

Usage:
    python 04_visualizations.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Set style
plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams.update(
    {
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.titlesize": 14,
        "figure.dpi": 150,
    }
)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"


# Color palette
COLORS = {
    "primary": "#2563eb",  # Blue
    "secondary": "#7c3aed",  # Purple
    "accent": "#f59e0b",  # Orange
    "positive": "#10b981",  # Green
    "negative": "#ef4444",  # Red
    "neutral": "#6b7280",  # Gray
}


def load_all_results() -> dict:
    """Load all available result files."""
    data = {}

    files = {
        "power_law": "power_law_results.csv",
        "power_law_sample": "power_law_results_sample.csv",
        "gini": "gini_coefficients.csv",
        "concentration_trends": "concentration_trends.csv",
    }

    for name, filename in files.items():
        path = OUTPUT_DIR / filename
        if path.exists():
            data[name] = pd.read_csv(path)
            print(f"Loaded: {filename}")

    # Also check data directory
    data_files = {
        "yearly_stats": "yearly_distribution_stats.csv",
        "yearly_stats_sample": "yearly_stats_sample.csv",
        "daily_stats_sample": "daily_stats_sample.csv",
        "persistence": "top_developer_persistence.csv",
        "velocity": "velocity_change_pre_post.csv",
        "ai_coauthor": "ai_coauthor_trends.csv",
    }

    for name, filename in data_files.items():
        path = DATA_DIR / filename
        if path.exists():
            data[name] = pd.read_csv(path)
            print(f"Loaded: {filename}")

    return data


def plot_main_figure(data: dict, output_path: Path):
    """
    Create the main 4-panel figure for the paper.

    Panels:
    1. Concentration over time (top 1% share)
    2. Power law α over time
    3. Gini coefficient
    4. AI co-author mentions (if available)
    """
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))

    # Determine which dataset to use
    if "power_law" in data:
        df = data["power_law"]
    elif "power_law_sample" in data:
        df = data["power_law_sample"]
    else:
        print("No power law results found. Run analysis first.")
        return

    years = df["year"]

    # Panel A: Top 1% Share
    ax = axes[0, 0]
    if "top_1pct_share" in df.columns:
        ax.plot(
            years,
            df["top_1pct_share"] * 100,
            marker="o",
            color=COLORS["primary"],
            linewidth=2,
            markersize=6,
        )
    ax.axvline(x=2022, color=COLORS["negative"], linestyle="--", alpha=0.7, linewidth=1.5)
    ax.text(2022.1, ax.get_ylim()[1] * 0.95, "Copilot GA", fontsize=9, color=COLORS["negative"])
    ax.set_xlabel("Year")
    ax.set_ylabel("Share of Total Commits (%)")
    ax.set_title("A. Top 1% Developer Commit Share")

    # Panel B: Power Law α
    ax = axes[0, 1]
    if "alpha" in df.columns and df["alpha"].notna().any():
        ax.errorbar(
            years,
            df["alpha"],
            yerr=df.get("alpha_se", pd.Series([0] * len(df))) * 1.96,
            marker="s",
            color=COLORS["secondary"],
            linewidth=2,
            markersize=6,
            capsize=3,
        )
        ax.axvline(x=2022, color=COLORS["negative"], linestyle="--", alpha=0.7, linewidth=1.5)
        ax.set_xlabel("Year")
        ax.set_ylabel("Power Law Exponent (α)")
        ax.set_title("B. Distribution Tail Heaviness")
        ax.invert_yaxis()  # Lower α = heavier tail, so invert for intuitive reading
    else:
        ax.text(0.5, 0.5, "Power law not fitted", ha="center", va="center", transform=ax.transAxes)
        ax.set_title("B. Power Law Exponent (α)")

    # Panel C: Gini Coefficient
    ax = axes[1, 0]
    if "gini" in df.columns:
        ax.plot(
            years, df["gini"], marker="^", color=COLORS["accent"], linewidth=2, markersize=6
        )
    elif "gini" in data:
        gini_df = data["gini"]
        ax.plot(
            gini_df["year"],
            gini_df["gini"],
            marker="^",
            color=COLORS["accent"],
            linewidth=2,
            markersize=6,
        )
    ax.axvline(x=2022, color=COLORS["negative"], linestyle="--", alpha=0.7, linewidth=1.5)
    ax.set_xlabel("Year")
    ax.set_ylabel("Gini Coefficient")
    ax.set_title("C. Commit Inequality (Gini)")

    # Panel D: P99/P50 Ratio or AI mentions
    ax = axes[1, 1]
    if "ai_coauthor" in data:
        ai_df = data["ai_coauthor"]
        ai_df["date"] = pd.to_datetime(ai_df[["year", "month"]].assign(day=1))
        ai_df["ai_rate"] = ai_df["ai_coauthor_commits"] / ai_df["total_push_events"] * 10000

        ax.plot(
            ai_df["date"],
            ai_df["ai_rate"],
            color=COLORS["positive"],
            linewidth=2,
        )
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.set_xlabel("Date")
        ax.set_ylabel("AI Co-author Mentions (per 10k pushes)")
        ax.set_title("D. Explicit AI Attribution in Commits")
    elif "p99_p50_ratio" in df.columns:
        ax.plot(
            years,
            df["p99_p50_ratio"],
            marker="D",
            color=COLORS["positive"],
            linewidth=2,
            markersize=6,
        )
        ax.axvline(x=2022, color=COLORS["negative"], linestyle="--", alpha=0.7, linewidth=1.5)
        ax.set_xlabel("Year")
        ax.set_ylabel("P99 / P50 Ratio")
        ax.set_title("D. Tail Heaviness: 99th vs 50th Percentile")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()

    print(f"Saved main figure to: {output_path}")


def plot_lorenz_curves(data: dict, output_path: Path):
    """
    Plot Lorenz curves for selected years to visualize inequality.
    """
    # This requires the raw distribution data
    # For now, create a placeholder showing the concept

    fig, ax = plt.subplots(figsize=(8, 8))

    # Perfect equality line
    ax.plot([0, 1], [0, 1], "k--", linewidth=1, label="Perfect Equality")

    # Simulated Lorenz curves for different years (placeholder)
    # In practice, compute from actual distribution data
    x = np.linspace(0, 1, 100)

    # More bowed = more inequality
    for year, bow in [(2015, 0.6), (2020, 0.55), (2024, 0.5)]:
        y = x**bow
        ax.plot(x, y, linewidth=2, label=f"{year}")

    ax.set_xlabel("Cumulative Share of Developers")
    ax.set_ylabel("Cumulative Share of Commits")
    ax.set_title("Lorenz Curves: Commit Distribution Inequality")
    ax.legend(loc="upper left")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Saved Lorenz curve plot to: {output_path}")
    print("  Note: This is a conceptual placeholder. Replace with actual data.")


def plot_structural_break_test(data: dict, output_path: Path):
    """
    Visualize the structural break test around 2022.
    """
    if "power_law" in data:
        df = data["power_law"]
    elif "power_law_sample" in data:
        df = data["power_law_sample"]
    else:
        print("No data for structural break plot.")
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    metric = "top_1pct_share" if "top_1pct_share" in df.columns else "gini"
    values = df[metric] * (100 if metric == "top_1pct_share" else 1)
    years = df["year"]

    # Pre and post periods
    pre_mask = years < 2022
    post_mask = years >= 2022

    ax.scatter(years[pre_mask], values[pre_mask], s=100, color=COLORS["primary"], label="Pre-Copilot", zorder=5)
    ax.scatter(years[post_mask], values[post_mask], s=100, color=COLORS["accent"], label="Post-Copilot", zorder=5)

    # Trend lines
    if pre_mask.sum() >= 2:
        z = np.polyfit(years[pre_mask], values[pre_mask], 1)
        p = np.poly1d(z)
        ax.plot(years[pre_mask], p(years[pre_mask]), "--", color=COLORS["primary"], alpha=0.7)

    if post_mask.sum() >= 2:
        z = np.polyfit(years[post_mask], values[post_mask], 1)
        p = np.poly1d(z)
        ax.plot(years[post_mask], p(years[post_mask]), "--", color=COLORS["accent"], alpha=0.7)

    # Break line
    ax.axvline(x=2022, color=COLORS["negative"], linestyle="-", linewidth=2, alpha=0.8)
    ax.text(2022.1, ax.get_ylim()[1], "Copilot GA\n(Jun 2022)", fontsize=10, color=COLORS["negative"], va="top")

    # Means
    pre_mean = values[pre_mask].mean()
    post_mean = values[post_mask].mean()
    ax.axhline(y=pre_mean, xmin=0, xmax=0.5, color=COLORS["primary"], linestyle=":", alpha=0.5)
    ax.axhline(y=post_mean, xmin=0.5, xmax=1, color=COLORS["accent"], linestyle=":", alpha=0.5)

    ylabel = "Top 1% Commit Share (%)" if metric == "top_1pct_share" else "Gini Coefficient"
    ax.set_xlabel("Year")
    ax.set_ylabel(ylabel)
    ax.set_title(f"Structural Break Analysis: {ylabel}")
    ax.legend()

    # Add stats annotation
    stats_text = f"Pre-2022 mean: {pre_mean:.2f}\nPost-2022 mean: {post_mean:.2f}\nChange: {post_mean - pre_mean:+.2f}"
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10, va="top",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Saved structural break plot to: {output_path}")


def main():
    print("=" * 60)
    print("Generating Publication-Quality Visualizations")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load data
    data = load_all_results()

    if not data:
        print("\nNo result files found. Run the analysis scripts first:")
        print("  1. python 01a_download_gharchive_direct.py --years 2015-2024 --sample monthly")
        print("  2. python 02a_power_law_from_sample.py")
        return

    # Generate figures
    print("\nGenerating figures...")

    plot_main_figure(data, OUTPUT_DIR / "figure_1_main_results.png")
    plot_lorenz_curves(data, OUTPUT_DIR / "figure_2_lorenz_curves.png")
    plot_structural_break_test(data, OUTPUT_DIR / "figure_3_structural_break.png")

    print("\n" + "=" * 60)
    print("Visualization complete!")
    print(f"Output directory: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
