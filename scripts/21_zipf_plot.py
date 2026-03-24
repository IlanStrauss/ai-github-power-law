#!/usr/bin/env python3
"""
Zipf Rank-Size Plot: The Hero Chart

Plot log(rank) vs log(commits) for each year overlaid.
Visually shows the tail getting fatter over time.
The slope of the line is -1/(α-1), so concentration is directly readable.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Config
OUTPUT_DIR = Path("output")
YEARS = [2019, 2021, 2023, 2024, 2025]  # Select years to avoid clutter
COLORS = {
    2019: '#2E86AB',  # Blue (baseline)
    2021: '#A23B72',  # Purple
    2023: '#F18F01',  # Orange
    2024: '#C73E1D',  # Red
    2025: '#3A5A40',  # Dark green
}

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

def compute_zipf(commits):
    """Compute rank and value for Zipf plot."""
    sorted_commits = np.sort(commits)[::-1]  # Descending order
    ranks = np.arange(1, len(sorted_commits) + 1)
    return ranks, sorted_commits

def create_zipf_plot(df):
    """Create the Zipf rank-size plot."""
    fig, ax = plt.subplots(figsize=(10, 7))

    for year in YEARS:
        year_data = df[df["year"] == year].copy()

        # Apply filters
        year_data = year_data[year_data["n_repos"] >= 2]
        year_data = year_data[
            (year_data["total_commits"] >= 3) &
            (year_data["total_commits"] <= 10000)
        ]

        commits = year_data["total_commits"].values
        ranks, values = compute_zipf(commits)

        # Subsample for plotting (every nth point to reduce clutter)
        n = len(ranks)
        if n > 1000:
            # Logarithmic subsampling to preserve tail detail
            indices = np.unique(np.geomspace(1, n, num=500).astype(int) - 1)
            ranks_plot = ranks[indices]
            values_plot = values[indices]
        else:
            ranks_plot = ranks
            values_plot = values

        label = f"{year}" if year != 2025 else "2025*"
        ax.loglog(ranks_plot, values_plot, 'o-',
                  color=COLORS[year], alpha=0.7,
                  markersize=3, linewidth=1.5,
                  label=label)

    ax.set_xlabel('Rank (1 = highest commits)', fontsize=12)
    ax.set_ylabel('Commits per Year', fontsize=12)
    ax.set_title('Commit Distribution by Developer Rank (2019-2025)', fontsize=14, fontweight='bold')

    ax.legend(loc='lower left', fontsize=10, title='Year')
    ax.grid(True, alpha=0.3, which='major')

    ax.set_xlim(1, 200000)
    ax.set_ylim(1, 15000)

    plt.tight_layout()
    return fig

def create_zoomed_tail_plot(df):
    """Create zoomed view of top 1% to show tail fattening."""
    fig, ax = plt.subplots(figsize=(10, 6))

    for year in YEARS:
        year_data = df[df["year"] == year].copy()

        # Apply filters
        year_data = year_data[year_data["n_repos"] >= 2]
        year_data = year_data[
            (year_data["total_commits"] >= 3) &
            (year_data["total_commits"] <= 10000)
        ]

        commits = year_data["total_commits"].values
        ranks, values = compute_zipf(commits)

        # Top 1% only
        top_1pct = int(len(ranks) * 0.01)
        ranks_top = ranks[:top_1pct]
        values_top = values[:top_1pct]

        label = f"{year} (n={len(ranks):,})" if year != 2025 else f"2025* (n={len(ranks):,})"
        ax.loglog(ranks_top, values_top, 'o-',
                  color=COLORS[year], alpha=0.8,
                  markersize=4, linewidth=2,
                  label=label)

    ax.set_xlabel('Rank (Top 1%)', fontsize=12)
    ax.set_ylabel('Commits per Year', fontsize=12)
    ax.set_title('Zipf Plot: Top 1% of Developers (Tail View)', fontsize=14, fontweight='bold')

    ax.legend(loc='lower left', fontsize=10)
    ax.grid(True, alpha=0.3, which='both')

    plt.tight_layout()
    return fig

def main():
    print("=" * 60)
    print("Zipf Rank-Size Plot: The Hero Chart")
    print("=" * 60)

    # Load data
    print("\nLoading data...")
    df = load_data()
    print(f"Total observations: {len(df):,}")

    # Create main Zipf plot
    print("\nCreating Zipf plot...")
    fig1 = create_zipf_plot(df)
    fig1.savefig(OUTPUT_DIR / "zipf_rank_size.png", dpi=150, bbox_inches='tight')
    print(f"Saved: {OUTPUT_DIR / 'zipf_rank_size.png'}")

    # Create zoomed tail plot
    print("\nCreating tail zoom plot...")
    fig2 = create_zoomed_tail_plot(df)
    fig2.savefig(OUTPUT_DIR / "zipf_tail_zoom.png", dpi=150, bbox_inches='tight')
    print(f"Saved: {OUTPUT_DIR / 'zipf_tail_zoom.png'}")

    plt.close('all')

    print("\n✓ Zipf plots created successfully")

if __name__ == "__main__":
    main()
