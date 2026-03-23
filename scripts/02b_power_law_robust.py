#!/usr/bin/env python3
"""
Robust Power Law Analysis following Clauset-Shalizi-Newman (2009) methodology.

This script implements the rigorous approach from:
- Clauset, Shalizi, Newman (2009). "Power-law distributions in empirical data." SIAM Review.
- Voitalov et al. (2019). "Scale-free networks well done." Physical Review Research.
- Strauss, Yang, Mazzucato (2025). "Rich-Get-Richer? Platform Attention and Earnings Inequality."

Key methodological requirements:
1. MLE estimation of alpha with KS-based xmin selection
2. Bootstrap goodness-of-fit test (p-value > 0.1 to accept power law)
3. Likelihood ratio tests vs. alternatives (log-normal, exponential)
4. Multiple estimator comparison for robustness
5. Track alpha over time with confidence intervals

Usage:
    python 02b_power_law_robust.py
"""

import gzip
import json
import warnings
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

try:
    import powerlaw
    HAS_POWERLAW = True
except ImportError:
    HAS_POWERLAW = False
    print("ERROR: 'powerlaw' package required. Install with: pip install powerlaw")
    exit(1)

warnings.filterwarnings("ignore", category=RuntimeWarning)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
OUTPUT_DIR = PROJECT_ROOT / "output"


def load_or_extract_data() -> pd.DataFrame:
    """Load previously extracted data or extract from raw files."""
    cache_path = DATA_DIR / "commits_by_developer_year.parquet"

    if cache_path.exists():
        print(f"Loading cached data from {cache_path}")
        return pd.read_parquet(cache_path)

    print("Extracting commit data from raw files...")
    records = []

    files = sorted(RAW_DIR.glob("*.json.gz"))
    if not files:
        raise FileNotFoundError(f"No data files in {RAW_DIR}")

    for filepath in files:
        filename = filepath.stem.replace(".json", "")
        date_str = "-".join(filename.split("-")[:3])

        with gzip.open(filepath, "rt", encoding="utf-8") as f:
            for line in f:
                try:
                    event = json.loads(line)
                    if event.get("type") != "PushEvent":
                        continue

                    actor = event.get("actor", {}).get("login")
                    if not actor:
                        continue

                    # Skip bots
                    actor_lower = actor.lower()
                    if any(bot in actor_lower for bot in ["[bot]", "-bot", "dependabot", "renovate", "github-actions"]):
                        continue

                    commits = event.get("payload", {}).get("size", 0)
                    if commits > 0:
                        records.append({
                            "date": date_str,
                            "actor_login": actor,
                            "commits": commits,
                        })
                except json.JSONDecodeError:
                    continue

        print(f"  Processed {filepath.name}")

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year

    # Aggregate by developer-year
    agg = df.groupby(["year", "actor_login"])["commits"].sum().reset_index()
    agg.columns = ["year", "developer", "commits"]

    # Cache for future runs
    agg.to_parquet(cache_path, index=False)
    print(f"Cached to {cache_path}")

    return agg


def hill_estimator(data: np.ndarray, xmin: float) -> tuple:
    """
    Hill estimator for power law exponent.

    Returns: (alpha, standard_error)
    """
    tail = data[data >= xmin]
    n = len(tail)
    if n < 2:
        return np.nan, np.nan

    log_ratio = np.log(tail / xmin)
    alpha = 1 + n / np.sum(log_ratio)
    se = (alpha - 1) / np.sqrt(n)

    return alpha, se


def moments_estimator(data: np.ndarray, xmin: float) -> float:
    """
    Moments-based estimator for power law exponent.
    Based on Voitalov et al. (2019).
    """
    tail = data[data >= xmin]
    if len(tail) < 10:
        return np.nan

    log_data = np.log(tail)
    mean_log = np.mean(log_data)
    var_log = np.var(log_data, ddof=1)

    # Method of moments estimator
    alpha = 1 + 1 / (mean_log - np.log(xmin))

    return alpha


def bootstrap_gof_test(data: np.ndarray, fit, n_iterations: int = 100) -> float:
    """
    Bootstrap goodness-of-fit test for power law.

    Following Clauset et al. (2009):
    - Generate synthetic datasets from fitted power law
    - Compare KS statistics
    - p-value = fraction of synthetic KS >= observed KS

    Returns p-value. Power law is plausible if p > 0.1.

    Note: This is computationally expensive. Use n_iterations=100 for quick tests,
    n_iterations=1000+ for publication.
    """
    observed_ks = fit.power_law.D

    synthetic_ks_values = []
    n = len(data)
    xmin = fit.power_law.xmin
    alpha = fit.power_law.alpha

    # Data below xmin (empirical)
    data_below = data[data < xmin]
    n_below = len(data_below)
    n_above = n - n_below

    for _ in range(n_iterations):
        # Generate synthetic data
        # Below xmin: sample from empirical
        if n_below > 0:
            synthetic_below = np.random.choice(data_below, size=n_below, replace=True)
        else:
            synthetic_below = np.array([])

        # Above xmin: sample from fitted power law
        # Using inverse CDF: x = xmin * (1 - u)^(-1/(alpha-1))
        u = np.random.uniform(0, 1, n_above)
        synthetic_above = xmin * (1 - u) ** (-1 / (alpha - 1))

        synthetic_data = np.concatenate([synthetic_below, synthetic_above])

        # Fit power law to synthetic data
        try:
            synthetic_fit = powerlaw.Fit(synthetic_data, discrete=True, verbose=False)
            synthetic_ks_values.append(synthetic_fit.power_law.D)
        except:
            continue

    if not synthetic_ks_values:
        return np.nan

    # p-value: fraction of synthetic KS >= observed KS
    p_value = np.mean(np.array(synthetic_ks_values) >= observed_ks)

    return p_value


def fit_power_law_robust(data: np.ndarray, year: int, bootstrap_iterations: int = 100) -> dict:
    """
    Robust power law fitting following CSN (2009) methodology.

    Returns dict with:
    - Multiple alpha estimates (MLE/Hill, moments)
    - Goodness-of-fit p-value
    - Comparison with alternatives
    - Confidence intervals
    """
    result = {
        "year": year,
        "n_total": len(data),
    }

    # 1. Fit using powerlaw package (implements CSN method)
    fit = powerlaw.Fit(data, discrete=True, verbose=False)

    result["alpha_mle"] = fit.power_law.alpha
    result["alpha_se"] = fit.power_law.sigma
    result["xmin"] = fit.power_law.xmin
    result["n_tail"] = int(np.sum(data >= fit.power_law.xmin))
    result["tail_fraction"] = result["n_tail"] / len(data)
    result["ks_statistic"] = fit.power_law.D

    # 2. Alternative estimators for robustness
    result["alpha_hill"], _ = hill_estimator(data, fit.power_law.xmin)
    result["alpha_moments"] = moments_estimator(data, fit.power_law.xmin)

    # 3. Bootstrap goodness-of-fit test
    print(f"    Running bootstrap GoF test ({bootstrap_iterations} iterations)...")
    result["gof_pvalue"] = bootstrap_gof_test(data, fit, n_iterations=bootstrap_iterations)
    result["power_law_plausible"] = result["gof_pvalue"] > 0.1 if not np.isnan(result["gof_pvalue"]) else None

    # 4. Compare with alternative distributions
    try:
        R_ln, p_ln = fit.distribution_compare("power_law", "lognormal", normalized_ratio=True)
        result["R_vs_lognormal"] = R_ln
        result["p_vs_lognormal"] = p_ln
        result["prefer_powerlaw_over_lognormal"] = R_ln > 0 and p_ln < 0.1
    except:
        result["R_vs_lognormal"] = np.nan
        result["p_vs_lognormal"] = np.nan
        result["prefer_powerlaw_over_lognormal"] = None

    try:
        R_exp, p_exp = fit.distribution_compare("power_law", "exponential", normalized_ratio=True)
        result["R_vs_exponential"] = R_exp
        result["p_vs_exponential"] = p_exp
    except:
        result["R_vs_exponential"] = np.nan
        result["p_vs_exponential"] = np.nan

    # 5. Additional inequality metrics
    sorted_data = np.sort(data)[::-1]
    total = sorted_data.sum()
    n = len(sorted_data)

    result["top_1pct_share"] = sorted_data[:max(1, int(n * 0.01))].sum() / total
    result["top_10pct_share"] = sorted_data[:max(1, int(n * 0.10))].sum() / total
    result["gini"] = calculate_gini(data)
    result["p99_p50_ratio"] = np.percentile(data, 99) / np.percentile(data, 50)

    return result


def calculate_gini(data: np.ndarray) -> float:
    """Calculate Gini coefficient."""
    sorted_data = np.sort(data)
    n = len(sorted_data)
    cumsum = np.cumsum(sorted_data)
    return (2 * np.sum((np.arange(1, n + 1) * sorted_data)) / (n * cumsum[-1])) - (n + 1) / n


def plot_robust_results(results_df: pd.DataFrame, output_dir: Path):
    """Generate publication-quality figures following Strauss-Yang-Mazzucato style."""

    fig, axes = plt.subplots(2, 3, figsize=(14, 9))

    years = results_df["year"]

    # Panel A: Multiple alpha estimators (robustness check)
    ax = axes[0, 0]
    ax.errorbar(years, results_df["alpha_mle"], yerr=results_df["alpha_se"] * 1.96,
                marker="o", linewidth=2, label="MLE (CSN)", capsize=4)
    ax.plot(years, results_df["alpha_hill"], marker="s", linewidth=2, label="Hill", alpha=0.7)
    ax.plot(years, results_df["alpha_moments"], marker="^", linewidth=2, label="Moments", alpha=0.7)
    ax.axvline(x=2022, color="red", linestyle="--", alpha=0.7)
    ax.set_xlabel("Year")
    ax.set_ylabel("Power Law α")
    ax.set_title("A. Power Law Exponent\n(Multiple Estimators)")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # Panel B: Goodness-of-fit p-values
    ax = axes[0, 1]
    colors = ["green" if p > 0.1 else "red" for p in results_df["gof_pvalue"]]
    ax.bar(years, results_df["gof_pvalue"], color=colors, alpha=0.7)
    ax.axhline(y=0.1, color="black", linestyle="--", linewidth=1.5, label="p=0.1 threshold")
    ax.axvline(x=2022, color="red", linestyle="--", alpha=0.7)
    ax.set_xlabel("Year")
    ax.set_ylabel("Bootstrap p-value")
    ax.set_title("B. Goodness-of-Fit Test\n(p > 0.1 = power law plausible)")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # Panel C: R vs log-normal
    ax = axes[0, 2]
    colors = ["green" if r > 0 else "orange" for r in results_df["R_vs_lognormal"]]
    ax.bar(years, results_df["R_vs_lognormal"], color=colors, alpha=0.7)
    ax.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
    ax.axvline(x=2022, color="red", linestyle="--", alpha=0.7)
    ax.set_xlabel("Year")
    ax.set_ylabel("Log-Likelihood Ratio (R)")
    ax.set_title("C. Power Law vs Log-Normal\n(R > 0 = power law better)")
    ax.grid(True, alpha=0.3)

    # Panel D: Top 1% share over time
    ax = axes[1, 0]
    ax.plot(years, results_df["top_1pct_share"] * 100, marker="o", linewidth=2, color="darkblue")
    ax.axvline(x=2022, color="red", linestyle="--", alpha=0.7, label="Copilot GA")
    ax.set_xlabel("Year")
    ax.set_ylabel("Share of Commits (%)")
    ax.set_title("D. Top 1% Developer Share")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # Panel E: Gini coefficient
    ax = axes[1, 1]
    ax.plot(years, results_df["gini"], marker="s", linewidth=2, color="purple")
    ax.axvline(x=2022, color="red", linestyle="--", alpha=0.7)
    ax.set_xlabel("Year")
    ax.set_ylabel("Gini Coefficient")
    ax.set_title("E. Commit Inequality (Gini)")
    ax.grid(True, alpha=0.3)

    # Panel F: xmin and tail fraction
    ax = axes[1, 2]
    ax2 = ax.twinx()
    line1 = ax.plot(years, results_df["xmin"], marker="o", linewidth=2, color="teal", label="xmin")
    line2 = ax2.plot(years, results_df["tail_fraction"] * 100, marker="s", linewidth=2, color="coral", label="Tail %")
    ax.axvline(x=2022, color="red", linestyle="--", alpha=0.7)
    ax.set_xlabel("Year")
    ax.set_ylabel("xmin (commits)", color="teal")
    ax2.set_ylabel("Tail Fraction (%)", color="coral")
    ax.set_title("F. Power Law Tail Properties")
    lines = line1 + line2
    ax.legend(lines, [l.get_label() for l in lines], fontsize=9)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / "power_law_robust_analysis.png", dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Saved robust analysis plot")


def print_methodology_summary():
    """Print methodology summary for documentation."""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     POWER LAW ESTIMATION METHODOLOGY                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                                ║
║  Following Clauset, Shalizi, Newman (2009) and Voitalov et al. (2019):        ║
║                                                                                ║
║  1. ESTIMATION                                                                 ║
║     • MLE for α with KS-based xmin selection (CSN method)                     ║
║     • Hill estimator as robustness check                                       ║
║     • Moments estimator as additional check                                    ║
║                                                                                ║
║  2. GOODNESS-OF-FIT                                                            ║
║     • Bootstrap test: generate synthetic power law data                        ║
║     • Compare KS statistics                                                    ║
║     • p > 0.1: power law is plausible                                         ║
║     • p < 0.1: power law may not be appropriate                               ║
║                                                                                ║
║  3. MODEL COMPARISON                                                           ║
║     • Likelihood ratio test vs log-normal                                      ║
║     • R > 0: power law preferred                                              ║
║     • R < 0: log-normal preferred                                             ║
║     • p < 0.1: difference is significant                                      ║
║                                                                                ║
║  4. INTERPRETATION OF α                                                        ║
║     • Lower α → heavier tail → more inequality                                ║
║     • α ≈ 2: extreme concentration (rich-get-richer)                          ║
║     • α > 3: lighter tail, more egalitarian                                   ║
║                                                                                ║
║  References:                                                                   ║
║  • Clauset et al. (2009). SIAM Review 51(4):661-703                           ║
║  • Voitalov et al. (2019). Physical Review Research 1(3):033034               ║
║  • Strauss, Yang, Mazzucato (2025). arXiv:2509.26523                          ║
║                                                                                ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")


def main():
    print("=" * 70)
    print("ROBUST POWER LAW ANALYSIS")
    print("Following Clauset-Shalizi-Newman (2009) Methodology")
    print("=" * 70)

    print_methodology_summary()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load data
    df = load_or_extract_data()
    print(f"\nLoaded {len(df):,} developer-year observations")
    print(f"Years: {df['year'].min()} - {df['year'].max()}")

    # Fit power law for each year
    print("\n" + "-" * 70)
    print("Fitting power law distributions with robustness checks...")
    print("-" * 70)

    results = []
    for year in sorted(df["year"].unique()):
        data = df[df["year"] == year]["commits"].values

        if len(data) < 100:
            print(f"\n{year}: Skipping (n={len(data)} < 100)")
            continue

        print(f"\n{year}: n={len(data):,} developers")

        result = fit_power_law_robust(data, year, bootstrap_iterations=100)
        results.append(result)

        # Print key results
        print(f"    α (MLE):    {result['alpha_mle']:.3f} ± {result['alpha_se']:.3f}")
        print(f"    α (Hill):   {result['alpha_hill']:.3f}")
        print(f"    α (Moments):{result['alpha_moments']:.3f}")
        print(f"    xmin:       {result['xmin']:.0f}")
        print(f"    GoF p-value:{result['gof_pvalue']:.3f} {'✓' if result['gof_pvalue'] > 0.1 else '✗'}")
        print(f"    R vs LN:    {result['R_vs_lognormal']:.3f}")
        print(f"    Top 1%:     {result['top_1pct_share']*100:.1f}%")

    results_df = pd.DataFrame(results)

    # Save results
    output_path = OUTPUT_DIR / "power_law_robust_results.csv"
    results_df.to_csv(output_path, index=False)
    print(f"\n\nSaved results to: {output_path}")

    # Generate plots
    print("\nGenerating plots...")
    plot_robust_results(results_df, OUTPUT_DIR)

    # Summary table
    print("\n" + "=" * 70)
    print("SUMMARY TABLE")
    print("=" * 70)
    summary_cols = ["year", "n_total", "alpha_mle", "alpha_se", "gof_pvalue",
                    "R_vs_lognormal", "top_1pct_share", "gini"]
    print(results_df[summary_cols].to_string(index=False, float_format=lambda x: f"{x:.3f}"))

    # Structural break analysis
    print("\n" + "=" * 70)
    print("STRUCTURAL BREAK ANALYSIS (2022)")
    print("=" * 70)

    pre = results_df[results_df["year"] < 2022]
    post = results_df[results_df["year"] >= 2022]

    if len(pre) > 0 and len(post) > 0:
        metrics = ["alpha_mle", "top_1pct_share", "gini"]
        for metric in metrics:
            pre_mean = pre[metric].mean()
            post_mean = post[metric].mean()
            change = post_mean - pre_mean
            t_stat, p_val = stats.ttest_ind(pre[metric], post[metric])

            print(f"\n{metric}:")
            print(f"  Pre-2022 mean:  {pre_mean:.4f}")
            print(f"  Post-2022 mean: {post_mean:.4f}")
            print(f"  Change:         {change:+.4f}")
            print(f"  t-statistic:    {t_stat:.3f}")
            print(f"  p-value:        {p_val:.4f}")

    print("\n" + "=" * 70)
    print("INTERPRETATION")
    print("=" * 70)
    print("""
Key findings to report:

1. POWER LAW VALIDITY
   - Check GoF p-values: If p > 0.1 for all years, power law is appropriate
   - If some years have p < 0.1, note which distributions fit better

2. ESTIMATOR AGREEMENT
   - If MLE, Hill, and Moments estimates agree (within ~0.1), results are robust
   - Disagreement suggests tail behavior may be complex

3. CONCENTRATION TREND
   - Decreasing α over time → increasing concentration
   - Increasing top 1% share → winner-take-all dynamics strengthening

4. STRUCTURAL BREAK
   - Compare pre-2022 vs post-2022 means
   - Significant change supports AI amplification hypothesis
""")


if __name__ == "__main__":
    main()
