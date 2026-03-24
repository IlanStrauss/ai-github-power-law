#!/usr/bin/env python3
"""
Transition Matrix Analysis: Testing Persistent Superstars

For developers appearing in multiple years, build a Markov transition matrix:
What fraction of top-1% developers in year T are still top-1% in year T+1?

If AI is creating persistent superstars (not just one-off high years),
we'd expect high persistence in the top quantile post-2022.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Config
OUTPUT_DIR = Path("output")
QUANTILES = [0.99, 0.90, 0.50]  # Top 1%, Top 10%, Bottom 50%
QUANTILE_LABELS = ['Top 1%', 'Top 10%', 'Bottom 50%']

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

def assign_quantile(commits, thresholds):
    """Assign quantile labels based on thresholds."""
    if commits >= thresholds['top_1']:
        return 'Top 1%'
    elif commits >= thresholds['top_10']:
        return 'Top 10%'
    elif commits >= thresholds['median']:
        return 'Middle'
    else:
        return 'Bottom 50%'

def compute_transition_matrix(df, year_from, year_to):
    """Compute transition probabilities between years."""
    # Filter to multi-repo developers with valid commits
    df_filtered = df[
        (df["n_repos"] >= 2) &
        (df["total_commits"] >= 3) &
        (df["total_commits"] <= 10000)
    ].copy()

    # Get developers in both years
    df_from = df_filtered[df_filtered["year"] == year_from].copy()
    df_to = df_filtered[df_filtered["year"] == year_to].copy()

    # Find overlapping developers
    common_devs = set(df_from["actor_login"]) & set(df_to["actor_login"])

    if len(common_devs) < 100:
        print(f"Warning: Only {len(common_devs)} common developers for {year_from}→{year_to}")
        return None, None

    # Filter to common developers
    df_from = df_from[df_from["actor_login"].isin(common_devs)].set_index("actor_login")
    df_to = df_to[df_to["actor_login"].isin(common_devs)].set_index("actor_login")

    # Compute quantile thresholds for each year
    thresholds_from = {
        'top_1': df_from["total_commits"].quantile(0.99),
        'top_10': df_from["total_commits"].quantile(0.90),
        'median': df_from["total_commits"].quantile(0.50)
    }
    thresholds_to = {
        'top_1': df_to["total_commits"].quantile(0.99),
        'top_10': df_to["total_commits"].quantile(0.90),
        'median': df_to["total_commits"].quantile(0.50)
    }

    # Assign quantiles
    df_from["quantile"] = df_from["total_commits"].apply(lambda x: assign_quantile(x, thresholds_from))
    df_to["quantile"] = df_to["total_commits"].apply(lambda x: assign_quantile(x, thresholds_to))

    # Build transition counts
    transitions = pd.crosstab(
        df_from["quantile"],
        df_to["quantile"],
        normalize='index'
    )

    # Ensure consistent ordering
    order = ['Top 1%', 'Top 10%', 'Middle', 'Bottom 50%']
    transitions = transitions.reindex(index=order, columns=order, fill_value=0)

    return transitions, len(common_devs)

def compute_top1_persistence(df):
    """Compute top-1% persistence rate for each year transition."""
    results = []
    years = sorted(df["year"].unique())

    for i in range(len(years) - 1):
        year_from = years[i]
        year_to = years[i + 1]

        matrix, n_common = compute_transition_matrix(df, year_from, year_to)

        if matrix is not None:
            persistence = matrix.loc['Top 1%', 'Top 1%']
            stay_top10 = matrix.loc['Top 1%', 'Top 1%'] + matrix.loc['Top 1%', 'Top 10%']

            results.append({
                'transition': f"{year_from}→{year_to}",
                'year_from': year_from,
                'year_to': year_to,
                'n_common': n_common,
                'top1_stay_top1': persistence,
                'top1_stay_top10': stay_top10,
                'top1_drop_below_median': matrix.loc['Top 1%', 'Bottom 50%'] if 'Bottom 50%' in matrix.columns else 0
            })

            print(f"{year_from}→{year_to}: Top 1% → Top 1% = {persistence:.1%}, n={n_common:,}")

    return pd.DataFrame(results)

def create_persistence_plot(results_df):
    """Create visualization of top-1% persistence over time."""
    fig, ax = plt.subplots(figsize=(10, 6))

    x = range(len(results_df))
    labels = results_df['transition'].values

    # Plot persistence rates
    ax.bar(x, results_df['top1_stay_top1'] * 100, color='#2E86AB', alpha=0.8, label='Stay Top 1%')
    ax.bar(x, (results_df['top1_stay_top10'] - results_df['top1_stay_top1']) * 100,
           bottom=results_df['top1_stay_top1'] * 100,
           color='#A23B72', alpha=0.6, label='Drop to Top 10%')

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.set_ylabel('Percentage of Top 1%', fontsize=12)
    ax.set_xlabel('Year Transition', fontsize=12)
    ax.set_title('Top 1% Developer Persistence (Year-over-Year)', fontsize=14, fontweight='bold')

    # Add Copilot launch line
    ax.axvline(x=2.5, color='green', linestyle='--', alpha=0.7, label='Copilot Launch (Jun 2022)')

    ax.legend(loc='upper right')
    ax.set_ylim(0, 100)
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    return fig

def main():
    print("=" * 60)
    print("Transition Matrix Analysis: Persistent Superstars")
    print("=" * 60)

    # Load data
    print("\nLoading data...")
    df = load_data()
    print(f"Total observations: {len(df):,}")
    print(f"Unique developers: {df['actor_login'].nunique():,}")

    # Compute persistence
    print("\nComputing top-1% persistence rates...")
    print("-" * 60)
    results = compute_top1_persistence(df)

    # Save results
    results.to_csv(OUTPUT_DIR / "transition_matrix_results.csv", index=False)
    print(f"\nSaved: {OUTPUT_DIR / 'transition_matrix_results.csv'}")

    # Create plot
    print("\nCreating persistence plot...")
    fig = create_persistence_plot(results)
    fig.savefig(OUTPUT_DIR / "top1_persistence.png", dpi=150, bbox_inches='tight')
    print(f"Saved: {OUTPUT_DIR / 'top1_persistence.png'}")

    # Summary statistics
    print("\n" + "=" * 60)
    print("SUMMARY: Top 1% Persistence")
    print("=" * 60)

    pre_ai = results[results['year_from'] < 2022]['top1_stay_top1'].mean()
    post_ai = results[results['year_from'] >= 2022]['top1_stay_top1'].mean()

    print(f"  Pre-AI (2019-2021 avg):  {pre_ai:.1%}")
    print(f"  Post-AI (2022-2024 avg): {post_ai:.1%}")
    print(f"  Change: {(post_ai - pre_ai)*100:+.1f} percentage points")

    if post_ai > pre_ai:
        print("\n  → Superstars are MORE persistent post-AI (supports persistent superstar hypothesis)")
    else:
        print("\n  → No increase in persistence (may be 'lucky year' effect)")

    plt.close('all')
    print("\n✓ Transition matrix analysis complete")

if __name__ == "__main__":
    main()
