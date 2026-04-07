#!/usr/bin/env python3
"""
Heterogeneity Tests: Is the Power Law a Mixture Artifact?

This script tests whether the observed power law arises from a MIXTURE OF EXPONENTIALS
rather than a dynamic concentration mechanism (preferential attachment, Kesten, etc.).

PRECISE DEFINITIONS:

1. RATE HETEROGENEITY
   - Each developer i has an underlying "intensity" or "rate" λᵢ governing their commit frequency
   - If individual commits follow Poisson(λᵢ), observed annual commits xᵢ ~ Poisson(λᵢ)
   - Rate heterogeneity = dispersion in λ across the population

   Measurement:
   - Coefficient of Variation: CV(λ) = σ_λ / μ_λ
   - Since we observe x not λ, we use the relationship:
     * For Poisson: Var(x) = E(x), so Fano factor F = Var(x)/E(x) = 1
     * For Gamma-mixed Poisson (Neg. Binomial): F > 1, and F - 1 measures overdispersion
   - The overdispersion parameter: δ = Var(x)/E(x) - 1
     * δ = 0: No heterogeneity (pure Poisson)
     * δ > 0: Rate heterogeneity exists
     * δ increasing over time: Heterogeneity is growing

2. NEGATIVE BINOMIAL AS MIXTURE TEST
   - If x | λ ~ Poisson(λ) and λ ~ Gamma(r, p/(1-p)), then x ~ NegBin(r, p)
   - The shape parameter r (also called "size" or "dispersion") controls heterogeneity:
     * r → ∞: NegBin → Poisson (no heterogeneity)
     * r small: High heterogeneity, heavy tails
   - CV of the underlying Gamma: CV(λ) = 1/√r
   - Lower r = higher rate heterogeneity

3. INCREASING HETEROGENEITY means:
   - The overdispersion δ is increasing year-over-year
   - Equivalently, the NegBin parameter r is decreasing
   - Equivalently, CV(λ) = 1/√r is increasing
   - This produces heavier tails (lower α) without any dynamic mechanism

References:
- Mitzenmacher (2004). "A Brief History of Generative Models for Power Law Distributions"
- Cameron & Trivedi (2013). "Regression Analysis of Count Data" (Ch. 3 on NegBin)
"""

import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from scipy import stats
from scipy.special import gammaln
from scipy.optimize import minimize_scalar, minimize
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_panel_data():
    """Load panel data with org classification."""
    commits = pd.read_parquet(DATA_DIR / "commits_by_developer_year.parquet")
    commits = commits.rename(columns={"developer": "actor_login"})

    org_devs = pd.read_parquet(DATA_DIR / "developers_org_filtered.parquet")
    org_set = set(org_devs["actor_login"].unique())
    commits["is_org"] = commits["actor_login"].isin(org_set)

    return commits


# =============================================================================
# TEST 1: Rate Heterogeneity Measurement
# =============================================================================

def measure_heterogeneity(data, min_commits=1):
    """
    Measure rate heterogeneity using multiple metrics.

    Returns:
    - mean: E(x)
    - variance: Var(x)
    - fano_factor: Var(x)/E(x) — equals 1 for Poisson, >1 for overdispersion
    - overdispersion_delta: Var(x)/E(x) - 1 — excess variance relative to Poisson
    - cv_observed: CV of observed commits = σ_x / μ_x
    - cv_squared_excess: CV²(x) - 1/μ — excess CV² above Poisson expectation
      (For Poisson, CV² = 1/μ; excess indicates rate heterogeneity)
    """
    x = data[data >= min_commits].values

    if len(x) < 100:
        return None

    mean = np.mean(x)
    var = np.var(x, ddof=1)

    fano = var / mean
    delta = fano - 1

    cv_observed = np.std(x, ddof=1) / mean
    cv_squared = cv_observed ** 2
    cv_squared_poisson = 1 / mean  # Expected CV² for Poisson with same mean
    cv_squared_excess = cv_squared - cv_squared_poisson

    # Index of dispersion confidence interval (chi-square based)
    n = len(x)
    chi2_lower = stats.chi2.ppf(0.025, n - 1)
    chi2_upper = stats.chi2.ppf(0.975, n - 1)
    fano_ci_lower = fano * (n - 1) / chi2_upper
    fano_ci_upper = fano * (n - 1) / chi2_lower

    return {
        "n": n,
        "mean": mean,
        "variance": var,
        "fano_factor": fano,
        "fano_ci_lower": fano_ci_lower,
        "fano_ci_upper": fano_ci_upper,
        "overdispersion_delta": delta,
        "cv_observed": cv_observed,
        "cv_squared_excess": cv_squared_excess,
    }


def test_heterogeneity_trend(panel_df, group_name="All"):
    """
    Test whether rate heterogeneity is increasing over time.

    Key question: Is overdispersion δ trending upward?
    """
    results = []

    for year in sorted(panel_df["year"].unique()):
        year_data = panel_df[panel_df["year"] == year]["commits"]

        metrics = measure_heterogeneity(year_data, min_commits=1)
        if metrics:
            metrics["group"] = group_name
            metrics["year"] = year
            results.append(metrics)

    df = pd.DataFrame(results)

    if len(df) >= 3:
        # Test for trend in overdispersion
        slope, intercept, r, p, se = stats.linregress(df["year"], df["overdispersion_delta"])
        df["delta_trend_slope"] = slope
        df["delta_trend_p"] = p
        df["delta_trend_r"] = r

    return df


# =============================================================================
# TEST 2: Negative Binomial vs Poisson (Mixture Model Test)
# =============================================================================

def negbin_loglik(params, x):
    """
    Negative binomial log-likelihood.
    Parameterization: NB(r, p) where r = size (dispersion), p = success prob
    Mean = r(1-p)/p, Var = r(1-p)/p²
    """
    r, p = params
    if r <= 0 or p <= 0 or p >= 1:
        return 1e10

    # Log-likelihood: sum of log(NB PMF)
    # Using scipy's nbinom which uses (n, p) parameterization where n=r
    ll = np.sum(stats.nbinom.logpmf(x, n=r, p=p))
    return -ll  # Return negative for minimization


def poisson_loglik(lam, x):
    """Poisson log-likelihood."""
    if lam <= 0:
        return 1e10
    ll = np.sum(stats.poisson.logpmf(x, mu=lam))
    return -ll


def fit_negbin(x):
    """
    Fit Negative Binomial via MLE.
    Returns (r, p, loglik) where r is the dispersion parameter.

    Lower r = more heterogeneity
    CV of underlying rate distribution = 1/sqrt(r)
    """
    x = x[x > 0]  # NegBin is for positive counts

    mean_x = np.mean(x)
    var_x = np.var(x, ddof=1)

    # Method of moments initial estimates
    if var_x > mean_x:
        r_init = mean_x ** 2 / (var_x - mean_x)
        p_init = mean_x / var_x
    else:
        r_init = 10
        p_init = 0.5

    r_init = np.clip(r_init, 0.1, 1000)
    p_init = np.clip(p_init, 0.01, 0.99)

    # Optimize
    try:
        result = minimize(
            negbin_loglik,
            x0=[r_init, p_init],
            args=(x,),
            method='L-BFGS-B',
            bounds=[(0.01, 10000), (0.001, 0.999)]
        )
        r_hat, p_hat = result.x
        loglik = -result.fun
    except:
        r_hat, p_hat, loglik = np.nan, np.nan, np.nan

    return r_hat, p_hat, loglik


def fit_poisson(x):
    """Fit Poisson via MLE (trivial: lambda = mean)."""
    x = x[x > 0]
    lam_hat = np.mean(x)
    loglik = np.sum(stats.poisson.logpmf(x, mu=lam_hat))
    return lam_hat, loglik


def likelihood_ratio_test(panel_df, group_name="All"):
    """
    Compare Negative Binomial vs Poisson fit.

    H0: Poisson is adequate (no rate heterogeneity)
    H1: Negative Binomial fits better (rate heterogeneity exists)

    Test statistic: LR = 2 * (LL_NB - LL_Poisson) ~ chi²(1) under H0
    """
    results = []

    for year in sorted(panel_df["year"].unique()):
        x = panel_df[panel_df["year"] == year]["commits"].values
        x = x[x >= 1]  # Active developers only

        if len(x) < 100:
            continue

        # Fit both models
        lam_pois, ll_pois = fit_poisson(x)
        r_nb, p_nb, ll_nb = fit_negbin(x)

        if np.isnan(ll_nb):
            continue

        # Likelihood ratio test
        lr_stat = 2 * (ll_nb - ll_pois)
        p_value = 1 - stats.chi2.cdf(lr_stat, df=1)  # 1 extra parameter in NB

        # Implied CV of underlying rate distribution
        cv_rate = 1 / np.sqrt(r_nb) if r_nb > 0 else np.inf

        # Mean and variance under fitted NB
        mean_nb = r_nb * (1 - p_nb) / p_nb
        var_nb = r_nb * (1 - p_nb) / (p_nb ** 2)

        results.append({
            "group": group_name,
            "year": year,
            "n": len(x),
            "poisson_lambda": lam_pois,
            "poisson_loglik": ll_pois,
            "negbin_r": r_nb,
            "negbin_p": p_nb,
            "negbin_loglik": ll_nb,
            "negbin_mean": mean_nb,
            "negbin_var": var_nb,
            "lr_statistic": lr_stat,
            "lr_p_value": p_value,
            "cv_underlying_rate": cv_rate,
            "better_fit": "NegBin (heterogeneity)" if p_value < 0.05 else "Poisson",
        })

    return pd.DataFrame(results)


# =============================================================================
# TEST 3: New Entrant Analysis
# =============================================================================

def analyze_new_entrants(panel_df, group_name="All"):
    """
    Analyze who the new entrants to top 1% are:

    1. Genuinely new accounts (first year in data)
    2. Existing developers who increased activity
    3. Existing developers who were already near the top

    This distinguishes between:
    - Statistical churn (different draws from same distribution)
    - True mobility (developers improving)
    - Platform growth (new users dominating)
    """
    years = sorted(panel_df["year"].unique())
    results = []

    # Track first appearance of each developer
    first_appearance = panel_df.groupby("actor_login")["year"].min().to_dict()

    for i in range(1, len(years)):
        year_prev, year_curr = years[i-1], years[i]

        prev_data = panel_df[panel_df["year"] == year_prev].set_index("actor_login")
        curr_data = panel_df[panel_df["year"] == year_curr].set_index("actor_login")

        # Define top 1% in current year
        curr_threshold = curr_data["commits"].quantile(0.99)
        curr_top1 = set(curr_data[curr_data["commits"] >= curr_threshold].index)

        # Define top 1% in previous year
        prev_threshold = prev_data["commits"].quantile(0.99)
        prev_top1 = set(prev_data[prev_data["commits"] >= prev_threshold].index)

        # New entrants to top 1%
        new_entrants = curr_top1 - prev_top1
        n_new = len(new_entrants)

        if n_new == 0:
            continue

        # Categorize new entrants
        genuinely_new = 0  # First year in data
        increased_activity = 0  # Were in data but below top 1%
        near_top_before = 0  # Were in top 5% but not top 1%

        prev_commits_of_new_entrants = []
        curr_commits_of_new_entrants = []
        growth_ratios = []

        for dev in new_entrants:
            first_year = first_appearance.get(dev, year_curr)

            if first_year == year_curr:
                genuinely_new += 1
            elif dev in prev_data.index:
                prev_commits = prev_data.loc[dev, "commits"]
                curr_commits = curr_data.loc[dev, "commits"]
                prev_percentile = (prev_data["commits"] <= prev_commits).mean() * 100

                prev_commits_of_new_entrants.append(prev_commits)
                curr_commits_of_new_entrants.append(curr_commits)

                if prev_commits > 0:
                    growth_ratios.append(curr_commits / prev_commits)

                if prev_percentile >= 95:
                    near_top_before += 1
                else:
                    increased_activity += 1
            else:
                genuinely_new += 1

        # Statistics on growth
        median_prev_commits = np.median(prev_commits_of_new_entrants) if prev_commits_of_new_entrants else np.nan
        median_curr_commits = np.median(curr_commits_of_new_entrants) if curr_commits_of_new_entrants else np.nan
        median_growth_ratio = np.median(growth_ratios) if growth_ratios else np.nan

        results.append({
            "group": group_name,
            "period": f"{year_prev}-{year_curr}",
            "n_top1_current": len(curr_top1),
            "n_new_entrants": n_new,
            "n_genuinely_new_accounts": genuinely_new,
            "n_increased_activity": increased_activity,
            "n_near_top_before": near_top_before,
            "pct_genuinely_new": genuinely_new / n_new * 100,
            "pct_increased_activity": increased_activity / n_new * 100,
            "pct_near_top_before": near_top_before / n_new * 100,
            "median_prev_commits_of_entrants": median_prev_commits,
            "median_curr_commits_of_entrants": median_curr_commits,
            "median_growth_ratio": median_growth_ratio,
        })

    df = pd.DataFrame(results)

    # Add interpretation
    if len(df) > 0:
        df["dominant_source"] = df.apply(
            lambda r: "New accounts" if r["pct_genuinely_new"] > 50
            else "Activity increases" if r["pct_increased_activity"] > 40
            else "Near-top promotion" if r["pct_near_top_before"] > 30
            else "Mixed",
            axis=1
        )

    return df


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("HETEROGENEITY TESTS: Is the Power Law a Mixture Artifact?")
    print("=" * 80)

    print("""
PRECISE DEFINITIONS:

1. RATE HETEROGENEITY
   Each developer i has an underlying commit "rate" λᵢ. If commits follow Poisson(λᵢ),
   then rate heterogeneity = dispersion in λ across the population.

   Measured by:
   - Overdispersion δ = Var(x)/E(x) - 1
     * δ = 0: Pure Poisson (no heterogeneity)
     * δ > 0: Rate heterogeneity exists
     * δ increasing: Heterogeneity is growing → heavier tails

2. NEGATIVE BINOMIAL TEST
   If x|λ ~ Poisson(λ) and λ ~ Gamma(r, β), then x ~ NegBin(r, p)
   - Parameter r (shape/dispersion) controls heterogeneity
   - CV of underlying rates = 1/√r
   - Lower r = more heterogeneous rates = heavier tails

3. INCREASING HETEROGENEITY means:
   - δ trending upward over time
   - Equivalently: r decreasing over time
   - This produces power-law-like tails WITHOUT dynamic "winner-take-all"
    """)

    # Load data
    print("\nLoading data...")
    panel = load_panel_data()
    org_panel = panel[panel["is_org"]].copy()
    personal_panel = panel[~panel["is_org"]].copy()

    print(f"Total developers: {panel['actor_login'].nunique():,}")
    print(f"Org developers: {org_panel['actor_login'].nunique():,}")
    print(f"Personal developers: {personal_panel['actor_login'].nunique():,}")

    # =========================================================================
    # TEST 1: Rate Heterogeneity Trends
    # =========================================================================
    print("\n" + "=" * 80)
    print("TEST 1: Is Rate Heterogeneity Increasing Over Time?")
    print("=" * 80)
    print("""
    Key metric: Overdispersion δ = Var(x)/E(x) - 1
    - δ = 0 means Poisson (no heterogeneity)
    - δ > 0 means overdispersion (heterogeneity exists)
    - δ increasing over time means heterogeneity is growing
    """)

    het_all = test_heterogeneity_trend(panel, "All Developers")
    het_org = test_heterogeneity_trend(org_panel, "Org Developers")
    het_personal = test_heterogeneity_trend(personal_panel, "Personal Developers")

    het_results = pd.concat([het_all, het_org, het_personal])
    het_results.to_csv(OUTPUT_DIR / "heterogeneity_trends.csv", index=False)

    print("\nOverdispersion (δ) by year:")
    print(het_results[["group", "year", "mean", "variance", "fano_factor",
                       "overdispersion_delta", "cv_observed"]].to_string(index=False))

    # Report trends
    print("\n" + "-" * 60)
    print("TREND IN OVERDISPERSION (δ):")
    print("-" * 60)

    for group in ["All Developers", "Org Developers", "Personal Developers"]:
        df = het_results[het_results["group"] == group]
        if len(df) >= 3 and "delta_trend_slope" in df.columns:
            slope = df["delta_trend_slope"].iloc[0]
            p = df["delta_trend_p"].iloc[0]
            r = df["delta_trend_r"].iloc[0]
            delta_2019 = df[df["year"] == 2019]["overdispersion_delta"].values[0]
            delta_2024 = df[df["year"] == 2024]["overdispersion_delta"].values[0]

            print(f"\n{group}:")
            print(f"  δ (2019): {delta_2019:.1f}")
            print(f"  δ (2024): {delta_2024:.1f}")
            print(f"  Change:  {delta_2024 - delta_2019:+.1f} ({(delta_2024/delta_2019 - 1)*100:+.1f}%)")
            print(f"  Trend slope: {slope:.2f} per year (p = {p:.4f})")
            print(f"  Interpretation: {'INCREASING heterogeneity' if slope > 0 and p < 0.1 else 'No significant trend'}")

    # =========================================================================
    # TEST 2: Negative Binomial vs Poisson
    # =========================================================================
    print("\n" + "=" * 80)
    print("TEST 2: Negative Binomial vs Poisson (Mixture Model Fit)")
    print("=" * 80)
    print("""
    H0: Poisson adequate (homogeneous rates)
    H1: Negative Binomial better (heterogeneous rates from Gamma mixture)

    Key output:
    - negbin_r: Dispersion parameter (lower = more heterogeneity)
    - cv_underlying_rate: CV of λ distribution = 1/√r
    - If r decreases over time → heterogeneity increasing
    """)

    lr_all = likelihood_ratio_test(panel, "All Developers")
    lr_org = likelihood_ratio_test(org_panel, "Org Developers")
    lr_personal = likelihood_ratio_test(personal_panel, "Personal Developers")

    lr_results = pd.concat([lr_all, lr_org, lr_personal])
    lr_results.to_csv(OUTPUT_DIR / "negbin_vs_poisson.csv", index=False)

    print("\nLikelihood Ratio Test Results:")
    print(lr_results[["group", "year", "negbin_r", "cv_underlying_rate",
                      "lr_statistic", "lr_p_value", "better_fit"]].to_string(index=False))

    # Report r trends
    print("\n" + "-" * 60)
    print("TREND IN DISPERSION PARAMETER (r):")
    print("-" * 60)
    print("(Lower r = more heterogeneity in underlying rates)")

    for group in ["All Developers", "Org Developers", "Personal Developers"]:
        df = lr_results[lr_results["group"] == group]
        if len(df) >= 3:
            slope, _, r_corr, p, _ = stats.linregress(df["year"], df["negbin_r"])
            r_2019 = df[df["year"] == 2019]["negbin_r"].values[0]
            r_2024 = df[df["year"] == 2024]["negbin_r"].values[0]
            cv_2019 = df[df["year"] == 2019]["cv_underlying_rate"].values[0]
            cv_2024 = df[df["year"] == 2024]["cv_underlying_rate"].values[0]

            print(f"\n{group}:")
            print(f"  r (2019): {r_2019:.4f} → CV(λ) = {cv_2019:.2f}")
            print(f"  r (2024): {r_2024:.4f} → CV(λ) = {cv_2024:.2f}")
            print(f"  Trend slope: {slope:.4f} per year (p = {p:.4f})")
            print(f"  Interpretation: {'DECREASING r → INCREASING heterogeneity' if slope < 0 and p < 0.1 else 'No significant trend in r'}")

    # =========================================================================
    # TEST 3: New Entrant Analysis
    # =========================================================================
    print("\n" + "=" * 80)
    print("TEST 3: Who Are the New Entrants to Top 1%?")
    print("=" * 80)
    print("""
    Categories:
    1. Genuinely new accounts (first appearance in data)
    2. Increased activity (were in data but below top 1%)
    3. Near-top before (were in top 5%, promoted to top 1%)

    This distinguishes:
    - Platform growth (new accounts dominate)
    - True mobility (activity increases)
    - Statistical churn (near-top shuffling)
    """)

    entrants_all = analyze_new_entrants(panel, "All Developers")
    entrants_org = analyze_new_entrants(org_panel, "Org Developers")
    entrants_personal = analyze_new_entrants(personal_panel, "Personal Developers")

    entrants_results = pd.concat([entrants_all, entrants_org, entrants_personal])
    entrants_results.to_csv(OUTPUT_DIR / "new_entrant_analysis.csv", index=False)

    print("\nNew Entrant Composition:")
    print(entrants_results[["group", "period", "n_new_entrants",
                            "pct_genuinely_new", "pct_increased_activity",
                            "pct_near_top_before", "dominant_source"]].to_string(index=False))

    print("\n" + "-" * 60)
    print("GROWTH PATTERNS OF NEW ENTRANTS:")
    print("-" * 60)
    print(entrants_results[["group", "period", "median_prev_commits_of_entrants",
                            "median_curr_commits_of_entrants",
                            "median_growth_ratio"]].to_string(index=False))

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "=" * 80)
    print("SUMMARY: MECHANISM IDENTIFICATION")
    print("=" * 80)

    print("""
    EVIDENCE FOR MIXTURE OF EXPONENTIALS:

    1. OVERDISPERSION TEST:
       - If δ is large and positive → heterogeneity exists
       - If δ is INCREASING over time → explains declining α without dynamics

    2. NEGATIVE BINOMIAL TEST:
       - If NegBin >> Poisson (LR test significant) → mixture confirmed
       - If r is DECREASING over time → heterogeneity increasing
       - CV(λ) = 1/√r gives the coefficient of variation of underlying rates

    3. NEW ENTRANT ANALYSIS:
       - If dominated by "genuinely new" → platform growth effect
       - If dominated by "increased activity" → true mobility exists
       - If dominated by "near-top" → statistical churn at margin

    COMBINED INTERPRETATION:
    - If δ increasing AND r decreasing AND new accounts dominate:
      → Power law is statistical artifact of growing heterogeneity + platform growth
      → NOT dynamic concentration ("superstars pulling ahead")

    - If δ stable AND mobility high AND increased activity dominates:
      → Power law reflects true dynamic mobility
      → Consistent with rotating superstars
    """)


if __name__ == "__main__":
    main()
