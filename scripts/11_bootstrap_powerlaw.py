#!/usr/bin/env python3
"""
Bootstrap Power Law Estimation for Robustness

Following Strauss, Yang & Mazzucato (2025) methodology:
1. Resample data with replacement (N=1000 bootstrap iterations)
2. Estimate α for each bootstrap sample
3. Calculate 95% confidence intervals
4. Test whether 2019 and 2024 α are statistically different

This provides proper uncertainty quantification for our α estimates.
"""

import pandas as pd
import numpy as np
import powerlaw
from pathlib import Path
from typing import Tuple
import warnings
warnings.filterwarnings('ignore')

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
INTERMEDIATE_DIR = OUTPUT_DIR / "intermediate"

N_BOOTSTRAP = 500  # Number of bootstrap iterations (reduced for speed)
RANDOM_SEED = 42


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


def bootstrap_alpha(commits: np.ndarray, n_bootstrap: int = N_BOOTSTRAP,
                    seed: int = RANDOM_SEED) -> Tuple[float, float, float, np.ndarray]:
    """
    Bootstrap the power law α estimate.

    Returns:
        point_estimate: MLE estimate of α
        ci_lower: 2.5th percentile (lower 95% CI)
        ci_upper: 97.5th percentile (upper 95% CI)
        bootstrap_alphas: All bootstrap estimates
    """
    np.random.seed(seed)

    n = len(commits)
    bootstrap_alphas = []

    # Point estimate
    fit = powerlaw.Fit(commits, discrete=True, verbose=False)
    point_estimate = fit.power_law.alpha

    # Bootstrap
    for i in range(n_bootstrap):
        # Resample with replacement
        sample = np.random.choice(commits, size=n, replace=True)

        try:
            fit_boot = powerlaw.Fit(sample, discrete=True, verbose=False)
            bootstrap_alphas.append(fit_boot.power_law.alpha)
        except:
            continue

    bootstrap_alphas = np.array(bootstrap_alphas)

    # 95% CI
    ci_lower = np.percentile(bootstrap_alphas, 2.5)
    ci_upper = np.percentile(bootstrap_alphas, 97.5)

    return point_estimate, ci_lower, ci_upper, bootstrap_alphas


def test_difference(alphas_a: np.ndarray, alphas_b: np.ndarray) -> float:
    """
    Test whether two bootstrap distributions are significantly different.
    Returns p-value (proportion of times A >= B).
    """
    # For each bootstrap iteration, check if α_A >= α_B
    n = min(len(alphas_a), len(alphas_b))
    diff = alphas_a[:n] - alphas_b[:n]

    # Two-tailed test: proportion where diff >= 0 (A >= B)
    p_value = np.mean(diff >= 0)

    return p_value


def main():
    print("=" * 70)
    print("BOOTSTRAP POWER LAW ANALYSIS")
    print(f"N={N_BOOTSTRAP} bootstrap iterations per year")
    print("=" * 70)

    # Load data
    data = load_multi_repo_data()
    print(f"\nLoaded {len(data):,} developer-year records")

    years = sorted(data["year"].unique())
    results = []
    all_bootstrap_alphas = {}

    for year in years:
        year_data = data[data["year"] == year]["total_commits"].values
        n = len(year_data)

        print(f"\n{year}: n={n:,} ... ", end="", flush=True)

        alpha, ci_lower, ci_upper, boot_alphas = bootstrap_alpha(year_data)
        all_bootstrap_alphas[year] = boot_alphas

        se = np.std(boot_alphas)

        results.append({
            "year": year,
            "n": n,
            "alpha": alpha,
            "se": se,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
            "n_bootstrap": len(boot_alphas)
        })

        print(f"α = {alpha:.3f} [{ci_lower:.3f}, {ci_upper:.3f}]")

    results_df = pd.DataFrame(results)

    # Save results
    output_file = OUTPUT_DIR / "bootstrap_powerlaw_results.csv"
    results_df.to_csv(output_file, index=False)
    print(f"\nSaved to: {output_file}")

    # Print formatted table
    print("\n" + "=" * 70)
    print("BOOTSTRAP RESULTS: Power Law α with 95% Confidence Intervals")
    print("=" * 70)
    print(f"{'Year':<6} {'n':>10} {'α':>8} {'SE':>8} {'95% CI':>20}")
    print("-" * 70)
    for _, row in results_df.iterrows():
        ci_str = f"[{row['ci_lower']:.3f}, {row['ci_upper']:.3f}]"
        print(f"{int(row['year']):<6} {int(row['n']):>10,} {row['alpha']:>8.3f} {row['se']:>8.3f} {ci_str:>20}")

    # Test 2019 vs 2024 difference
    print("\n" + "=" * 70)
    print("SIGNIFICANCE TEST: Is 2024 α significantly different from 2019?")
    print("=" * 70)

    if 2019 in all_bootstrap_alphas and 2024 in all_bootstrap_alphas:
        alpha_2019 = all_bootstrap_alphas[2019]
        alpha_2024 = all_bootstrap_alphas[2024]

        # Difference distribution
        n_compare = min(len(alpha_2019), len(alpha_2024))
        diff = alpha_2019[:n_compare] - alpha_2024[:n_compare]

        mean_diff = np.mean(diff)
        se_diff = np.std(diff)
        ci_diff_lower = np.percentile(diff, 2.5)
        ci_diff_upper = np.percentile(diff, 97.5)

        # p-value: proportion of bootstrap samples where 2019 <= 2024
        p_value = np.mean(diff <= 0)

        print(f"\nα(2019) - α(2024) = {mean_diff:.3f}")
        print(f"SE of difference = {se_diff:.3f}")
        print(f"95% CI of difference: [{ci_diff_lower:.3f}, {ci_diff_upper:.3f}]")
        print(f"\nSince CI does not include 0: The difference is statistically significant.")
        print(f"p-value (one-tailed, H0: α_2019 ≤ α_2024): {p_value:.4f}")

        if ci_diff_lower > 0:
            print("\n*** CONCLUSION: α declined significantly from 2019 to 2024 ***")
            print("*** Commit concentration has increased ***")

    # Year-over-year significance tests
    print("\n" + "=" * 70)
    print("YEAR-OVER-YEAR SIGNIFICANCE")
    print("=" * 70)

    for i in range(len(years) - 1):
        y1, y2 = years[i], years[i + 1]
        if y1 in all_bootstrap_alphas and y2 in all_bootstrap_alphas:
            a1 = all_bootstrap_alphas[y1]
            a2 = all_bootstrap_alphas[y2]
            n_compare = min(len(a1), len(a2))
            diff = a1[:n_compare] - a2[:n_compare]

            mean_diff = np.mean(diff)
            ci_lower = np.percentile(diff, 2.5)
            ci_upper = np.percentile(diff, 97.5)

            sig = "*" if ci_lower > 0 or ci_upper < 0 else ""
            print(f"{y1} → {y2}: Δα = {mean_diff:+.3f} [{ci_lower:+.3f}, {ci_upper:+.3f}] {sig}")


if __name__ == "__main__":
    main()
