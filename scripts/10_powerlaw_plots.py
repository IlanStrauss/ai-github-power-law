#!/usr/bin/env python3
"""
Power Law Distribution Plots by Year

Generates publication-quality CCDF plots showing:
1. Empirical distribution on log-log scale
2. Fitted power law line
3. Year-over-year comparison showing heavier tails

Following visualization style from Strauss, Yang & Mazzucato (2025)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import powerlaw
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
INTERMEDIATE_DIR = OUTPUT_DIR / "intermediate"

# Color palette for years
YEAR_COLORS = {
    2019: '#1f77b4',  # blue
    2020: '#2ca02c',  # green
    2021: '#ff7f0e',  # orange
    2022: '#d62728',  # red
    2023: '#9467bd',  # purple
    2024: '#000000',  # black (emphasis)
}


def load_multi_repo_data():
    """Load multi-repo developer data."""
    parquet_files = list(INTERMEDIATE_DIR.glob("year_*_developers.parquet"))

    dfs = []
    for f in parquet_files:
        df = pd.read_parquet(f)
        dfs.append(df)

    all_data = pd.concat(dfs, ignore_index=True)

    # Apply multi-repo filter
    filtered = all_data[
        (all_data["n_repos"] >= 2) &
        (all_data["total_commits"] >= 3) &
        (all_data["total_commits"] <= 10000)
    ]

    return filtered


def plot_ccdf_by_year(data: pd.DataFrame, output_path: Path):
    """
    Plot CCDF for each year on log-log scale.
    Shows empirical distribution and fitted power law.
    """
    fig, ax = plt.subplots(figsize=(10, 7))

    years = sorted(data["year"].unique())

    for year in years:
        year_data = data[data["year"] == year]["total_commits"].values

        # Compute empirical CCDF
        sorted_data = np.sort(year_data)[::-1]
        ccdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)

        # Plot empirical CCDF
        color = YEAR_COLORS.get(year, 'gray')
        linewidth = 2.5 if year == 2024 else 1.5
        alpha = 1.0 if year == 2024 else 0.7

        ax.loglog(sorted_data, ccdf,
                  color=color,
                  linewidth=linewidth,
                  alpha=alpha,
                  label=f'{year}')

    ax.set_xlabel('Commits per Year', fontsize=12)
    ax.set_ylabel('P(X > x)', fontsize=12)
    ax.set_title('Commit Distribution CCDF by Year (Multi-Repo Developers)', fontsize=14)
    ax.legend(title='Year', loc='lower left')
    ax.grid(True, alpha=0.3, which='both')

    # Set axis limits
    ax.set_xlim(1, 15000)
    ax.set_ylim(1e-6, 1.1)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved: {output_path}")


def plot_powerlaw_fits(data: pd.DataFrame, output_path: Path):
    """
    Plot fitted power law lines for each year.
    Shows how α changes over time.
    """
    fig, ax = plt.subplots(figsize=(10, 7))

    years = sorted(data["year"].unique())
    fit_results = []

    for year in years:
        year_data = data[data["year"] == year]["total_commits"].values

        # Fit power law
        fit = powerlaw.Fit(year_data, discrete=True, verbose=False)
        alpha = fit.power_law.alpha
        xmin = fit.power_law.xmin

        fit_results.append({
            'year': year,
            'alpha': alpha,
            'xmin': xmin,
            'n': len(year_data)
        })

        # Plot empirical CCDF
        sorted_data = np.sort(year_data)[::-1]
        ccdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)

        color = YEAR_COLORS.get(year, 'gray')
        linewidth = 2.5 if year == 2024 else 1.5
        alpha_plot = 1.0 if year == 2024 else 0.7

        # Empirical line
        ax.loglog(sorted_data, ccdf,
                  color=color,
                  linewidth=linewidth,
                  alpha=alpha_plot,
                  label=f'{year} (α={alpha:.2f})')

        # Fitted power law line (dashed)
        x_fit = np.logspace(np.log10(xmin), np.log10(max(year_data)), 100)
        # CCDF of power law: P(X > x) = (x/xmin)^(-alpha+1)
        y_fit = (x_fit / xmin) ** (-(alpha - 1))
        # Scale to match empirical at xmin
        xmin_idx = np.searchsorted(sorted_data[::-1], xmin)
        if xmin_idx < len(ccdf):
            scale = ccdf[::-1][xmin_idx]
            y_fit = y_fit * scale

        ax.loglog(x_fit, y_fit,
                  color=color,
                  linestyle='--',
                  linewidth=1.0,
                  alpha=0.5)

    ax.set_xlabel('Commits per Year', fontsize=12)
    ax.set_ylabel('P(X > x)', fontsize=12)
    ax.set_title('Power Law Fits by Year\n(Dashed lines show fitted power law tail)', fontsize=14)
    ax.legend(title='Year (α)', loc='lower left', fontsize=9)
    ax.grid(True, alpha=0.3, which='both')

    ax.set_xlim(1, 15000)
    ax.set_ylim(1e-6, 1.1)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved: {output_path}")

    return pd.DataFrame(fit_results)


def plot_alpha_trend(fit_results: pd.DataFrame, output_path: Path):
    """
    Plot α exponent trend over time.
    """
    fig, ax = plt.subplots(figsize=(8, 5))

    ax.plot(fit_results['year'], fit_results['alpha'],
            marker='o', markersize=10, linewidth=2, color='#d62728')

    # Add horizontal reference lines
    ax.axhline(y=2.0, color='gray', linestyle='--', alpha=0.5, label='α=2 (infinite variance threshold)')
    ax.axhline(y=2.5, color='gray', linestyle=':', alpha=0.5, label='α=2.5 (typical labor income)')

    # Annotate key points
    for _, row in fit_results.iterrows():
        ax.annotate(f"α={row['alpha']:.2f}",
                   (row['year'], row['alpha']),
                   textcoords="offset points",
                   xytext=(0, 10),
                   ha='center',
                   fontsize=9)

    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Power Law Exponent (α)', fontsize=12)
    ax.set_title('Declining α Indicates Increasing Concentration\n(Lower α = heavier tail = more inequality)', fontsize=13)
    ax.legend(loc='upper right', fontsize=9)
    ax.grid(True, alpha=0.3)

    ax.set_ylim(1.4, 2.3)
    ax.set_xticks(fit_results['year'])

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved: {output_path}")


def plot_2019_vs_2024(data: pd.DataFrame, output_path: Path):
    """
    Direct comparison: 2019 vs 2024 distributions.
    """
    fig, ax = plt.subplots(figsize=(10, 7))

    for year in [2019, 2024]:
        year_data = data[data["year"] == year]["total_commits"].values

        # Fit power law
        fit = powerlaw.Fit(year_data, discrete=True, verbose=False)
        alpha = fit.power_law.alpha

        # Compute empirical CCDF
        sorted_data = np.sort(year_data)[::-1]
        ccdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)

        color = YEAR_COLORS[year]
        linewidth = 2.5

        ax.loglog(sorted_data, ccdf,
                  color=color,
                  linewidth=linewidth,
                  label=f'{year}: α={alpha:.2f}, n={len(year_data):,}')

    # Add annotation about the shift
    ax.annotate('Heavier tail in 2024\n(more extreme concentration)',
                xy=(1000, 0.001),
                fontsize=11,
                ha='center',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    ax.set_xlabel('Commits per Year', fontsize=12)
    ax.set_ylabel('P(X > x)', fontsize=12)
    ax.set_title('2019 vs 2024: The Rise of Superstar Coders', fontsize=14)
    ax.legend(loc='lower left', fontsize=11)
    ax.grid(True, alpha=0.3, which='both')

    ax.set_xlim(1, 15000)
    ax.set_ylim(1e-6, 1.1)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved: {output_path}")


def main():
    print("=" * 70)
    print("POWER LAW DISTRIBUTION PLOTS")
    print("=" * 70)

    # Load data
    data = load_multi_repo_data()
    print(f"Loaded {len(data):,} developer-year records (multi-repo filter)")

    # Generate plots
    print("\nGenerating plots...")

    # 1. CCDF by year
    plot_ccdf_by_year(data, OUTPUT_DIR / "powerlaw_ccdf_by_year.png")

    # 2. Power law fits
    fit_results = plot_powerlaw_fits(data, OUTPUT_DIR / "powerlaw_fits_by_year.png")

    # 3. Alpha trend
    plot_alpha_trend(fit_results, OUTPUT_DIR / "powerlaw_alpha_trend.png")

    # 4. 2019 vs 2024 comparison
    plot_2019_vs_2024(data, OUTPUT_DIR / "powerlaw_2019_vs_2024.png")

    print("\n" + "=" * 70)
    print("DONE! Generated 4 plots in output/")
    print("=" * 70)

    print("\nFit results:")
    print(fit_results.to_string(index=False))


if __name__ == "__main__":
    main()
