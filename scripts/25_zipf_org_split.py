#!/usr/bin/env python3
"""
Zipf Rank-Size Plots: Org vs Personal Developers (Separate)

Creates TWO Zipf plots:
1. Org developers only
2. Personal developers only

This properly separates the two populations instead of pooling them.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

OUTPUT_DIR = Path("output")
YEARS = [2019, 2021, 2023, 2024, 2025]
COLORS = {
    2019: '#2E86AB',  # Blue (baseline)
    2021: '#A23B72',  # Purple
    2023: '#F18F01',  # Orange
    2024: '#C73E1D',  # Red
    2025: '#3A5A40',  # Dark green
}


def load_split_data():
    """Load org and personal developer data separately."""
    df_org = pd.read_parquet(OUTPUT_DIR / "developers_org_filtered.parquet")
    df_personal = pd.read_parquet(OUTPUT_DIR / "developers_personal_filtered.parquet")
    return df_org, df_personal


def compute_zipf(commits):
    """Compute rank and value for Zipf plot."""
    sorted_commits = np.sort(commits)[::-1]
    ranks = np.arange(1, len(sorted_commits) + 1)
    return ranks, sorted_commits


def create_zipf_plot(df, title_suffix, filename):
    """Create Zipf rank-size plot for a developer group."""
    fig, ax = plt.subplots(figsize=(10, 7))

    for year in YEARS:
        year_data = df[df["year"] == year].copy()

        if len(year_data) < 100:
            print(f"  Skipping {year}: only {len(year_data)} developers")
            continue

        commits = year_data["total_commits"].values
        ranks, values = compute_zipf(commits)

        # Subsample for plotting
        n = len(ranks)
        if n > 1000:
            indices = np.unique(np.geomspace(1, n, num=500).astype(int) - 1)
            ranks_plot = ranks[indices]
            values_plot = values[indices]
        else:
            ranks_plot = ranks
            values_plot = values

        label = f"{year} (n={n:,})"
        ax.loglog(ranks_plot, values_plot, 'o-',
                  color=COLORS[year], alpha=0.7,
                  markersize=3, linewidth=1.5,
                  label=label)

    ax.set_xlabel('Rank (1 = highest commits)', fontsize=12)
    ax.set_ylabel('Commits per Year', fontsize=12)
    ax.set_title(f'Commit Distribution by Developer Rank\n{title_suffix}', fontsize=14, fontweight='bold')

    ax.legend(loc='lower left', fontsize=10, title='Year')
    ax.grid(True, alpha=0.3, which='major')

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / filename, dpi=150, bbox_inches='tight')
    print(f"Saved: {OUTPUT_DIR / filename}")
    plt.close(fig)


def main():
    print("=" * 60)
    print("Zipf Plots: Org vs Personal Developers (Separate)")
    print("=" * 60)

    df_org, df_personal = load_split_data()
    print(f"Org developers: {len(df_org):,}")
    print(f"Personal developers: {len(df_personal):,}")

    print("\nCreating Org Developers Zipf plot...")
    create_zipf_plot(df_org, "Organization Developers Only", "zipf_org_developers.png")

    print("\nCreating Personal Developers Zipf plot...")
    create_zipf_plot(df_personal, "Personal/Hobbyist Developers Only", "zipf_personal_developers.png")

    print("\n✓ Org-split Zipf plots created successfully")


if __name__ == "__main__":
    main()
