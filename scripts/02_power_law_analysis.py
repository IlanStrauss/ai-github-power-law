#!/usr/bin/env python3
"""
Power Law Analysis of GitHub Commit Distributions.

This script fits power law distributions to yearly commit data and tests
whether the distribution is becoming more heavy-tailed over time.

Key outputs:
    - Power law α parameter for each year
    - Comparison with alternative distributions (log-normal, exponential)
    - Structural break tests around AI tool introduction (2022)

Usage:
    python 02_power_law_analysis.py

Prerequisites:
    pip install powerlaw pandas numpy scipy matplotlib
"""

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import powerlaw
from scipy import stats
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore", category=RuntimeWarning)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"


def load_commit_data() -> pd.DataFrame:
    """Load the commits per developer data."""
    path = DATA_DIR / "commits_per_developer_yearly.parquet"

    if not path.exists():
        raise FileNotFoundError(
            f"Data file not found: {path}\n"
            "Run 01_fetch_from_bigquery.py first to download data."
        )

    return pd.read_parquet(path)


def fit_power_law_by_year(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fit power law to commit distribution for each year.

    Returns DataFrame with:
        - year
        - alpha: power law exponent (lower = heavier tail)
        - xmin: minimum value where power law holds
        - sigma: standard error on alpha
        - n_tail: number of observations in the tail (x >= xmin)
        - R_lognormal: log-likelihood ratio vs log-normal
        - p_lognormal: p-value for power law vs log-normal comparison
    """
    results = []

    years = sorted(df["year"].unique())

    for year in years:
        year_data = df[df["year"] == year]["commits"].values

        print(f"\nFitting year {year} (n={len(year_data):,})...")

        # Fit power law
        fit = powerlaw.Fit(year_data, discrete=True, verbose=False)

        # Compare to log-normal (main alternative for heavy-tailed data)
        R_ln, p_ln = fit.distribution_compare("power_law", "lognormal", normalized_ratio=True)

        # Compare to exponential
        R_exp, p_exp = fit.distribution_compare("power_law", "exponential", normalized_ratio=True)

        # Calculate tail fraction
        n_tail = np.sum(year_data >= fit.power_law.xmin)
        tail_fraction = n_tail / len(year_data)

        result = {
            "year": year,
            "n_developers": len(year_data),
            "alpha": fit.power_law.alpha,
            "alpha_se": fit.power_law.sigma,
            "xmin": fit.power_law.xmin,
            "n_tail": n_tail,
            "tail_fraction": tail_fraction,
            # Positive R = power law better; p < 0.05 = significant difference
            "R_vs_lognormal": R_ln,
            "p_vs_lognormal": p_ln,
            "R_vs_exponential": R_exp,
            "p_vs_exponential": p_exp,
            # Additional summary stats
            "median_commits": np.median(year_data),
            "mean_commits": np.mean(year_data),
            "max_commits": np.max(year_data),
            "p99_commits": np.percentile(year_data, 99),
        }

        results.append(result)

        print(f"  α = {result['alpha']:.3f} ± {result['alpha_se']:.3f}")
        print(f"  xmin = {result['xmin']:.0f}")
        print(f"  R vs lognormal = {R_ln:.3f} (p={p_ln:.3f})")

    return pd.DataFrame(results)


def test_structural_break(results: pd.DataFrame, break_year: int = 2022) -> dict:
    """
    Test for structural break in alpha time series.

    Uses a simple difference-in-means test. For more sophisticated analysis,
    consider Chow test or Bai-Perron multiple break test.
    """
    pre = results[results["year"] < break_year]["alpha"]
    post = results[results["year"] >= break_year]["alpha"]

    # Two-sample t-test
    t_stat, p_value = stats.ttest_ind(pre, post)

    # Effect size (Cohen's d)
    pooled_std = np.sqrt((pre.var() + post.var()) / 2)
    cohens_d = (post.mean() - pre.mean()) / pooled_std if pooled_std > 0 else 0

    return {
        "break_year": break_year,
        "pre_mean_alpha": pre.mean(),
        "post_mean_alpha": post.mean(),
        "alpha_change": post.mean() - pre.mean(),
        "t_statistic": t_stat,
        "p_value": p_value,
        "cohens_d": cohens_d,
        "interpretation": (
            "Tail getting HEAVIER (more inequality)"
            if post.mean() < pre.mean()
            else "Tail getting LIGHTER (less inequality)"
        ),
    }


def calculate_gini_coefficient(values: np.ndarray) -> float:
    """Calculate Gini coefficient of inequality."""
    sorted_values = np.sort(values)
    n = len(sorted_values)
    cumsum = np.cumsum(sorted_values)
    return (2 * np.sum((np.arange(1, n + 1) * sorted_values)) / (n * cumsum[-1])) - (n + 1) / n


def calculate_yearly_gini(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate Gini coefficient for each year."""
    results = []

    for year in sorted(df["year"].unique()):
        year_data = df[df["year"] == year]["commits"].values
        gini = calculate_gini_coefficient(year_data)

        results.append({"year": year, "gini": gini, "n_developers": len(year_data)})

    return pd.DataFrame(results)


def plot_alpha_over_time(results: pd.DataFrame, output_path: Path):
    """Plot alpha coefficient over time with confidence intervals."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Plot 1: Alpha over time
    ax1 = axes[0, 0]
    ax1.errorbar(
        results["year"],
        results["alpha"],
        yerr=results["alpha_se"] * 1.96,  # 95% CI
        marker="o",
        capsize=4,
        capthick=1,
        linewidth=2,
        markersize=8,
    )
    ax1.axvline(x=2022, color="red", linestyle="--", alpha=0.7, label="Copilot GA (Jun 2022)")
    ax1.axvline(x=2024, color="orange", linestyle="--", alpha=0.7, label="Claude Code (2024)")
    ax1.set_xlabel("Year")
    ax1.set_ylabel("Power Law α")
    ax1.set_title("Power Law Exponent Over Time\n(Lower α = Heavier Tail = More Inequality)")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: R vs log-normal
    ax2 = axes[0, 1]
    colors = ["green" if r > 0 else "red" for r in results["R_vs_lognormal"]]
    ax2.bar(results["year"], results["R_vs_lognormal"], color=colors, alpha=0.7)
    ax2.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
    ax2.axvline(x=2022, color="red", linestyle="--", alpha=0.7)
    ax2.set_xlabel("Year")
    ax2.set_ylabel("Log-Likelihood Ratio (R)")
    ax2.set_title("Power Law vs Log-Normal Fit\n(Positive = Power Law Better)")
    ax2.grid(True, alpha=0.3)

    # Plot 3: Tail fraction
    ax3 = axes[1, 0]
    ax3.plot(results["year"], results["tail_fraction"] * 100, marker="s", linewidth=2, markersize=8)
    ax3.axvline(x=2022, color="red", linestyle="--", alpha=0.7, label="Copilot GA")
    ax3.set_xlabel("Year")
    ax3.set_ylabel("Tail Fraction (%)")
    ax3.set_title("Fraction of Developers in Power Law Tail")
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # Plot 4: Number of developers
    ax4 = axes[1, 1]
    ax4.plot(
        results["year"],
        results["n_developers"] / 1e6,
        marker="^",
        linewidth=2,
        markersize=8,
        color="purple",
    )
    ax4.axvline(x=2022, color="red", linestyle="--", alpha=0.7)
    ax4.set_xlabel("Year")
    ax4.set_ylabel("Active Developers (Millions)")
    ax4.set_title("Total Active Developers per Year")
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Saved plot to: {output_path}")


def main():
    print("=" * 60)
    print("Power Law Analysis of GitHub Commit Distributions")
    print("=" * 60)

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load data
    print("\nLoading data...")
    df = load_commit_data()
    print(f"Loaded {len(df):,} developer-year observations")
    print(f"Years: {df['year'].min()} - {df['year'].max()}")

    # Fit power law for each year
    print("\n" + "-" * 40)
    print("Fitting power law distributions...")
    print("-" * 40)
    results = fit_power_law_by_year(df)

    # Save results
    results_path = OUTPUT_DIR / "power_law_results.csv"
    results.to_csv(results_path, index=False)
    print(f"\nSaved results to: {results_path}")

    # Calculate Gini coefficients
    print("\n" + "-" * 40)
    print("Calculating Gini coefficients...")
    print("-" * 40)
    gini_results = calculate_yearly_gini(df)
    gini_path = OUTPUT_DIR / "gini_coefficients.csv"
    gini_results.to_csv(gini_path, index=False)
    print(f"Saved Gini results to: {gini_path}")

    # Test for structural break
    print("\n" + "-" * 40)
    print("Testing for structural break at 2022 (Copilot)...")
    print("-" * 40)
    break_test = test_structural_break(results, break_year=2022)
    for key, value in break_test.items():
        print(f"  {key}: {value}")

    # Also test 2024 break
    print("\nTesting for structural break at 2024 (Claude Code/Cursor)...")
    if results["year"].max() >= 2024:
        break_test_2024 = test_structural_break(results, break_year=2024)
        for key, value in break_test_2024.items():
            print(f"  {key}: {value}")

    # Generate plots
    print("\n" + "-" * 40)
    print("Generating plots...")
    print("-" * 40)
    plot_alpha_over_time(results, OUTPUT_DIR / "power_law_over_time.png")

    # Print summary table
    print("\n" + "=" * 60)
    print("SUMMARY: Power Law α by Year")
    print("=" * 60)
    print(results[["year", "alpha", "alpha_se", "xmin", "R_vs_lognormal"]].to_string(index=False))

    print("\n" + "=" * 60)
    print("INTERPRETATION")
    print("=" * 60)
    print(
        """
    - α (alpha): Power law exponent. P(x) ∝ x^(-α)
      Lower α = heavier tail = more extreme inequality

    - xmin: Minimum value where power law holds.
      Power law typically only applies to the upper tail.

    - R vs lognormal: Log-likelihood ratio comparing power law to log-normal.
      Positive = power law fits better
      Negative = log-normal fits better
      |R| < 0.1 with p > 0.1 = inconclusive

    KEY HYPOTHESIS:
      If AI tools amplify top contributor productivity,
      α should DECREASE over time (especially after 2022).
    """
    )


if __name__ == "__main__":
    main()
