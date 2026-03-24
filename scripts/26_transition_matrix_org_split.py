#!/usr/bin/env python3
"""
Transition Matrix: Org vs Personal Developers (Separate)

Creates transition matrices for EACH group separately:
1. Org developers - do professional coders become persistent superstars?
2. Personal developers - do hobbyists become persistent superstars?

This properly separates the two populations instead of pooling them.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

OUTPUT_DIR = Path("output")


def load_split_data():
    """Load org and personal developer data separately."""
    df_org = pd.read_parquet(OUTPUT_DIR / "developers_org_filtered.parquet")
    df_personal = pd.read_parquet(OUTPUT_DIR / "developers_personal_filtered.parquet")
    return df_org, df_personal


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
    df_from = df[df["year"] == year_from].copy()
    df_to = df[df["year"] == year_to].copy()

    # Find overlapping developers
    common_devs = set(df_from["actor_login"]) & set(df_to["actor_login"])

    if len(common_devs) < 50:
        return None, len(common_devs)

    df_from = df_from[df_from["actor_login"].isin(common_devs)].set_index("actor_login")
    df_to = df_to[df_to["actor_login"].isin(common_devs)].set_index("actor_login")

    # Compute quantile thresholds
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

    df_from["quantile"] = df_from["total_commits"].apply(lambda x: assign_quantile(x, thresholds_from))
    df_to["quantile"] = df_to["total_commits"].apply(lambda x: assign_quantile(x, thresholds_to))

    transitions = pd.crosstab(df_from["quantile"], df_to["quantile"], normalize='index')

    order = ['Top 1%', 'Top 10%', 'Middle', 'Bottom 50%']
    transitions = transitions.reindex(index=order, columns=order, fill_value=0)

    return transitions, len(common_devs)


def compute_persistence(df, group_name):
    """Compute top-1% persistence for all year transitions."""
    results = []
    years = sorted(df["year"].unique())

    print(f"\n{group_name}:")
    print("-" * 50)

    for i in range(len(years) - 1):
        year_from = years[i]
        year_to = years[i + 1]

        matrix, n_common = compute_transition_matrix(df, year_from, year_to)

        if matrix is not None and 'Top 1%' in matrix.index:
            persistence = matrix.loc['Top 1%', 'Top 1%']
            stay_top10 = matrix.loc['Top 1%', 'Top 1%'] + matrix.loc['Top 1%', 'Top 10%']

            results.append({
                'group': group_name,
                'transition': f"{year_from}→{year_to}",
                'year_from': year_from,
                'year_to': year_to,
                'n_common': n_common,
                'top1_stay_top1': persistence,
                'top1_stay_top10': stay_top10,
            })

            print(f"  {year_from}→{year_to}: Top 1% → Top 1% = {persistence:.1%}, n={n_common:,}")
        else:
            print(f"  {year_from}→{year_to}: Insufficient data (n={n_common})")

    return pd.DataFrame(results)


def create_comparison_plot(results_org, results_personal):
    """Create side-by-side comparison of persistence rates."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    for ax, results, title, color in [
        (axes[0], results_org, "Org Developers", '#2E86AB'),
        (axes[1], results_personal, "Personal Developers", '#A23B72')
    ]:
        if len(results) == 0:
            ax.text(0.5, 0.5, 'Insufficient data', ha='center', va='center')
            ax.set_title(title)
            continue

        x = range(len(results))
        labels = results['transition'].values

        ax.bar(x, results['top1_stay_top1'] * 100, color=color, alpha=0.8)

        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.set_ylabel('% of Top 1% Staying Top 1%', fontsize=11)
        ax.set_title(f'Top 1% Persistence: {title}', fontsize=12, fontweight='bold')

        # Copilot launch line
        if len(results) > 2:
            ax.axvline(x=2.5, color='green', linestyle='--', alpha=0.7, label='Copilot (Jun 2022)')
            ax.legend()

        ax.set_ylim(0, 100)
        ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    return fig


def main():
    print("=" * 60)
    print("Transition Matrix: Org vs Personal Developers")
    print("=" * 60)

    df_org, df_personal = load_split_data()
    print(f"Org developers: {len(df_org):,}")
    print(f"Personal developers: {len(df_personal):,}")

    # Compute persistence for each group
    results_org = compute_persistence(df_org, "Org Developers")
    results_personal = compute_persistence(df_personal, "Personal Developers")

    # Combine and save
    results_all = pd.concat([results_org, results_personal], ignore_index=True)
    results_all.to_csv(OUTPUT_DIR / "transition_matrix_org_split.csv", index=False)
    print(f"\nSaved: {OUTPUT_DIR / 'transition_matrix_org_split.csv'}")

    # Create comparison plot
    fig = create_comparison_plot(results_org, results_personal)
    fig.savefig(OUTPUT_DIR / "transition_matrix_org_split.png", dpi=150, bbox_inches='tight')
    print(f"Saved: {OUTPUT_DIR / 'transition_matrix_org_split.png'}")
    plt.close(fig)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY: Top 1% Persistence Comparison")
    print("=" * 60)

    for name, results in [("Org", results_org), ("Personal", results_personal)]:
        if len(results) == 0:
            continue
        pre_ai = results[results['year_from'] < 2022]['top1_stay_top1'].mean()
        post_ai = results[results['year_from'] >= 2022]['top1_stay_top1'].mean()
        print(f"\n{name} Developers:")
        print(f"  Pre-AI (avg):  {pre_ai:.1%}")
        print(f"  Post-AI (avg): {post_ai:.1%}")
        print(f"  Change: {(post_ai - pre_ai)*100:+.1f} pp")

    print("\n✓ Org-split transition matrix analysis complete")


if __name__ == "__main__":
    main()
