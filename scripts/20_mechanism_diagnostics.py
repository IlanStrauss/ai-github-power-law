#!/usr/bin/env python3
"""
Mechanism Diagnostics for Power Law Identification

With α ∈ (1.8, 2.1), multiple generative mechanisms are observationally equivalent.
This script implements diagnostic tests to distinguish between:

1. Preferential Attachment (Barabási-Albert): P(gain) ∝ current size
2. Multiplicative Growth + Barrier (Kesten/Gibrat): x(t+1) = η·x(t) with floor
3. Self-Organized Criticality: 1/f noise signature
4. Mixture of Exponentials: pure heterogeneity, no dynamics

Key diagnostics:
- Attachment kernel test: Is growth linear in size? (β ≈ 1 for pref. attachment)
- Taylor's Law: Var ~ Mean^τ (τ = 2 for lognormal/multiplicative)
- Cohort decomposition: Intensive (incumbents) vs Extensive (new entrants) margin
- Lower barrier test: Density spike near xmin
- Rank persistence: Fitness model vs pure preferential attachment

Reference: Clauset, Shalizi, Newman (2009); Gabaix (1999); Mitzenmacher (2004)
"""

import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_panel_data():
    """Load and prepare panel data for mechanism diagnostics."""
    # Primary panel: commits by developer-year
    commits = pd.read_parquet(DATA_DIR / "commits_by_developer_year.parquet")
    commits = commits.rename(columns={"developer": "actor_login"})

    # Org classification
    org_devs = pd.read_parquet(DATA_DIR / "developers_org_filtered.parquet")

    # Get set of org developers (ever contributed to org repo)
    org_set = set(org_devs["actor_login"].unique())
    commits["is_org"] = commits["actor_login"].isin(org_set)

    print(f"Panel shape: {commits.shape}")
    print(f"Years: {sorted(commits['year'].unique())}")
    print(f"Unique developers: {commits['actor_login'].nunique():,}")
    print(f"Org developers: {commits[commits['is_org']]['actor_login'].nunique():,}")
    print(f"Personal developers: {commits[~commits['is_org']]['actor_login'].nunique():,}")

    return commits


def create_balanced_panel(df, min_years=2):
    """Create balanced panel of developers appearing in multiple years."""
    # Count years per developer
    dev_years = df.groupby("actor_login")["year"].nunique()
    multi_year_devs = dev_years[dev_years >= min_years].index

    # Filter to multi-year developers
    panel = df[df["actor_login"].isin(multi_year_devs)].copy()

    # Pivot to wide format
    wide = panel.pivot_table(
        index="actor_login",
        columns="year",
        values="commits",
        fill_value=0
    )

    return panel, wide


# =============================================================================
# DIAGNOSTIC 1: Attachment Kernel Linearity Test
# =============================================================================

def test_attachment_kernel(panel_df, group_name="All"):
    """
    Test if growth is linear in size (preferential attachment).

    Estimate: Δx(t) = a * x(t-1)^β + ε

    β ≈ 1: Linear preferential attachment
    β < 1: Sublinear (advantages decelerate)
    β > 1: Superlinear (winner-take-all accelerates)

    The key distinction:
    - Preferential attachment: β = 1 with ADDITIVE errors
    - Multiplicative growth: β = 1 with MULTIPLICATIVE errors (log-linear)
    """
    results = []

    years = sorted(panel_df["year"].unique())

    for i in range(1, len(years)):
        year_prev, year_curr = years[i-1], years[i]

        # Get developers present in both years
        prev_data = panel_df[panel_df["year"] == year_prev][["actor_login", "commits"]]
        curr_data = panel_df[panel_df["year"] == year_curr][["actor_login", "commits"]]

        merged = prev_data.merge(
            curr_data,
            on="actor_login",
            suffixes=("_prev", "_curr")
        )

        # Filter to active developers (min 3 commits in base year)
        merged = merged[merged["commits_prev"] >= 3].copy()

        if len(merged) < 100:
            continue

        # Compute growth
        merged["growth"] = merged["commits_curr"] - merged["commits_prev"]
        merged["log_prev"] = np.log(merged["commits_prev"])
        merged["log_curr"] = np.log(merged["commits_curr"].clip(lower=1))
        merged["log_growth"] = merged["log_curr"] - merged["log_prev"]

        # Test 1: Log-log regression (β estimation)
        # log(Δx) = log(a) + β * log(x_prev)
        # But Δx can be negative, so we use: log(x_curr) = α + β * log(x_prev)

        valid = (merged["commits_curr"] > 0) & (merged["commits_prev"] > 0)
        if valid.sum() < 100:
            continue

        slope, intercept, r_value, p_value, std_err = stats.linregress(
            merged.loc[valid, "log_prev"],
            merged.loc[valid, "log_curr"]
        )

        # Test 2: Check residual structure
        merged["predicted_log"] = intercept + slope * merged["log_prev"]
        merged["residual"] = merged["log_curr"] - merged["predicted_log"]

        # Multiplicative growth predicts homoscedastic log residuals
        # Preferential attachment predicts heteroscedastic residuals (var increases with size)

        # Breusch-Pagan test approximation: regress squared residuals on x
        resid_sq = merged.loc[valid, "residual"] ** 2
        _, _, r_resid, p_resid, _ = stats.linregress(
            merged.loc[valid, "log_prev"],
            resid_sq
        )

        results.append({
            "group": group_name,
            "period": f"{year_prev}-{year_curr}",
            "n_developers": len(merged),
            "beta": slope,
            "beta_se": std_err,
            "r_squared": r_value ** 2,
            "p_value": p_value,
            "residual_heteroscedasticity_r": r_resid,
            "residual_hetero_p": p_resid,
            "interpretation": (
                "Preferential attachment (β≈1, hetero residuals)"
                if (0.9 < slope < 1.1 and p_resid < 0.05)
                else "Multiplicative growth (β≈1, homo residuals)"
                if (0.9 < slope < 1.1 and p_resid >= 0.05)
                else f"Sublinear (β={slope:.2f})" if slope < 0.9
                else f"Superlinear (β={slope:.2f})"
            )
        })

    return pd.DataFrame(results)


# =============================================================================
# DIAGNOSTIC 2: Taylor's Law (Variance Scaling)
# =============================================================================

def test_taylors_law(panel_df, group_name="All"):
    """
    Test Taylor's Law: Var(x) ~ Mean(x)^τ

    τ = 1: Poisson process
    τ = 2: Lognormal / multiplicative growth
    τ > 2: Power law / heavy tails

    We bin developers by their baseline (2019) commit level and compute
    mean and variance within each bin across subsequent years.
    """
    years = sorted(panel_df["year"].unique())
    base_year = years[0]

    # Get baseline commits
    baseline = panel_df[panel_df["year"] == base_year][["actor_login", "commits"]]
    baseline = baseline.rename(columns={"commits": "baseline_commits"})

    # Filter to active baseline (≥3 commits)
    baseline = baseline[baseline["baseline_commits"] >= 3]

    # Create baseline decile bins
    baseline["baseline_decile"] = pd.qcut(
        baseline["baseline_commits"],
        q=10,
        labels=False,
        duplicates="drop"
    )

    results = []

    for year in years[1:]:
        year_data = panel_df[panel_df["year"] == year][["actor_login", "commits"]]
        merged = baseline.merge(year_data, on="actor_login", how="inner")

        if len(merged) < 100:
            continue

        # Compute mean and variance by baseline decile
        stats_by_decile = merged.groupby("baseline_decile").agg(
            mean_commits=("commits", "mean"),
            var_commits=("commits", "var"),
            n=("commits", "count")
        ).reset_index()

        # Filter deciles with enough observations
        stats_by_decile = stats_by_decile[stats_by_decile["n"] >= 10]

        if len(stats_by_decile) < 5:
            continue

        # Log-log regression: log(Var) = log(a) + τ * log(Mean)
        valid = (stats_by_decile["var_commits"] > 0) & (stats_by_decile["mean_commits"] > 0)
        if valid.sum() < 4:
            continue

        log_mean = np.log(stats_by_decile.loc[valid, "mean_commits"])
        log_var = np.log(stats_by_decile.loc[valid, "var_commits"])

        tau, intercept, r_value, p_value, std_err = stats.linregress(log_mean, log_var)

        results.append({
            "group": group_name,
            "year": year,
            "tau": tau,
            "tau_se": std_err,
            "r_squared": r_value ** 2,
            "p_value": p_value,
            "interpretation": (
                "Poisson (τ≈1)" if tau < 1.5
                else "Lognormal/multiplicative (τ≈2)" if 1.5 <= tau <= 2.5
                else "Heavy-tailed/power law (τ>2)"
            )
        })

    return pd.DataFrame(results)


# =============================================================================
# DIAGNOSTIC 3: Cohort Decomposition (Intensive vs Extensive Margin)
# =============================================================================

def cohort_decomposition(panel_df, group_name="All"):
    """
    Decompose concentration changes into:
    - Intensive margin: existing top developers increasing output
    - Extensive margin: new developers entering the top

    Pure preferential attachment: new entrants can displace incumbents
    Kesten + fitness: persistent incumbents dominate
    """
    years = sorted(panel_df["year"].unique())
    results = []

    for i in range(1, len(years)):
        year_prev, year_curr = years[i-1], years[i]

        prev_data = panel_df[panel_df["year"] == year_prev].copy()
        curr_data = panel_df[panel_df["year"] == year_curr].copy()

        # Define top 1% in each year
        prev_threshold = prev_data["commits"].quantile(0.99)
        curr_threshold = curr_data["commits"].quantile(0.99)

        prev_top1 = set(prev_data[prev_data["commits"] >= prev_threshold]["actor_login"])
        curr_top1 = set(curr_data[curr_data["commits"] >= curr_threshold]["actor_login"])

        # Decomposition
        persistent = prev_top1 & curr_top1  # In top 1% both years
        churned_out = prev_top1 - curr_top1  # Fell out of top 1%
        new_entrants = curr_top1 - prev_top1  # New to top 1%

        # Compute shares
        n_prev_top1 = len(prev_top1)
        n_curr_top1 = len(curr_top1)

        # Total commits by each group in current year
        curr_commits = curr_data.set_index("actor_login")["commits"]

        persistent_commits = curr_commits.reindex(list(persistent)).sum()
        new_entrant_commits = curr_commits.reindex(list(new_entrants)).sum()
        total_top1_commits = curr_commits.reindex(list(curr_top1)).sum()

        results.append({
            "group": group_name,
            "period": f"{year_prev}-{year_curr}",
            "n_prev_top1": n_prev_top1,
            "n_curr_top1": n_curr_top1,
            "n_persistent": len(persistent),
            "n_churned_out": len(churned_out),
            "n_new_entrants": len(new_entrants),
            "persistence_rate": len(persistent) / n_prev_top1 if n_prev_top1 > 0 else 0,
            "new_entrant_rate": len(new_entrants) / n_curr_top1 if n_curr_top1 > 0 else 0,
            "persistent_commit_share": persistent_commits / total_top1_commits if total_top1_commits > 0 else 0,
            "new_entrant_commit_share": new_entrant_commits / total_top1_commits if total_top1_commits > 0 else 0,
        })

    df = pd.DataFrame(results)

    # Add interpretation
    df["margin_dominance"] = df.apply(
        lambda r: "Intensive (incumbents)" if r["persistent_commit_share"] > 0.6
        else "Extensive (new entrants)" if r["new_entrant_commit_share"] > 0.6
        else "Mixed",
        axis=1
    )

    return df


# =============================================================================
# DIAGNOSTIC 4: Lower Absorbing Barrier Test
# =============================================================================

def test_lower_barrier(panel_df, group_name="All"):
    """
    Test for reflecting barrier at xmin (Kesten mechanism).

    If there's a barrier, we expect:
    1. Excess density just above xmin compared to fitted power law
    2. A "pile-up" of developers at minimum activity levels

    We look for: density ratio near xmin vs slightly above.
    """
    results = []

    for year in sorted(panel_df["year"].unique()):
        year_data = panel_df[panel_df["year"] == year]["commits"].values
        year_data = year_data[year_data >= 3]  # Active developers only

        if len(year_data) < 1000:
            continue

        # Compute empirical density in bins
        bins = [3, 5, 10, 20, 50, 100, 200, 500, 1000, 10000]
        counts, _ = np.histogram(year_data, bins=bins)

        # Expected counts under power law (using α ≈ 1.9)
        alpha = 1.9
        bin_centers = [(bins[i] + bins[i+1]) / 2 for i in range(len(bins)-1)]
        expected_probs = np.array([c ** (-alpha) for c in bin_centers])
        expected_probs = expected_probs / expected_probs.sum()
        expected_counts = expected_probs * len(year_data)

        # Ratio: actual / expected near xmin
        ratios = counts / expected_counts

        # Barrier evidence: excess density in lowest bins
        low_bin_ratio = ratios[0]  # 3-5 commits
        mid_bin_ratio = ratios[2]  # 10-20 commits

        results.append({
            "group": group_name,
            "year": year,
            "n_active": len(year_data),
            "density_ratio_3_5": low_bin_ratio,
            "density_ratio_10_20": mid_bin_ratio,
            "barrier_evidence": low_bin_ratio / mid_bin_ratio if mid_bin_ratio > 0 else np.nan,
            "interpretation": (
                "Strong barrier evidence" if low_bin_ratio / mid_bin_ratio > 1.5
                else "Weak barrier evidence" if low_bin_ratio / mid_bin_ratio > 1.0
                else "No barrier evidence"
            )
        })

    return pd.DataFrame(results)


# =============================================================================
# DIAGNOSTIC 5: Rank Persistence (Fitness Model Test)
# =============================================================================

def test_rank_persistence(panel_df, group_name="All"):
    """
    Test rank-rank correlation over time.

    Pure preferential attachment: Moderate persistence, early movers advantage
    Fitness model: High-fitness developers rise regardless of start time

    We compute:
    - Spearman rank correlation between years
    - Transition matrix for percentile movements
    """
    years = sorted(panel_df["year"].unique())
    results = []

    # First vs Last year comparison
    first_year, last_year = years[0], years[-1]

    first_data = panel_df[panel_df["year"] == first_year][["actor_login", "commits"]]
    last_data = panel_df[panel_df["year"] == last_year][["actor_login", "commits"]]

    # Developers present in both
    merged = first_data.merge(
        last_data,
        on="actor_login",
        suffixes=("_first", "_last")
    )

    # Filter to active in both years
    merged = merged[(merged["commits_first"] >= 3) & (merged["commits_last"] >= 3)]

    if len(merged) >= 100:
        # Rank correlation
        rho, p_value = stats.spearmanr(merged["commits_first"], merged["commits_last"])

        # Percentile transition
        merged["pct_first"] = merged["commits_first"].rank(pct=True) * 100
        merged["pct_last"] = merged["commits_last"].rank(pct=True) * 100

        # Top 10% persistence
        top10_first = merged[merged["pct_first"] >= 90]["actor_login"]
        top10_last = merged[merged["pct_last"] >= 90]["actor_login"]
        top10_persist = len(set(top10_first) & set(top10_last)) / len(top10_first) if len(top10_first) > 0 else 0

        # Bottom 50% who reached top 10% ("risers")
        bottom50_first = merged[merged["pct_first"] < 50]["actor_login"]
        risers = len(set(bottom50_first) & set(top10_last))
        riser_rate = risers / len(bottom50_first) if len(bottom50_first) > 0 else 0

        results.append({
            "group": group_name,
            "period": f"{first_year}-{last_year}",
            "n_matched": len(merged),
            "rank_correlation_rho": rho,
            "rank_corr_p_value": p_value,
            "top10_persistence": top10_persist,
            "bottom50_to_top10_rate": riser_rate,
            "interpretation": (
                "High fitness heterogeneity" if rho > 0.6 and top10_persist > 0.5
                else "Moderate persistence" if 0.3 < rho < 0.6
                else "High mobility (pure preferential attachment)"
            )
        })

    # Also compute year-over-year correlations
    for i in range(1, len(years)):
        year_prev, year_curr = years[i-1], years[i]

        prev_data = panel_df[panel_df["year"] == year_prev][["actor_login", "commits"]]
        curr_data = panel_df[panel_df["year"] == year_curr][["actor_login", "commits"]]

        merged = prev_data.merge(curr_data, on="actor_login", suffixes=("_prev", "_curr"))
        merged = merged[(merged["commits_prev"] >= 3) & (merged["commits_curr"] >= 3)]

        if len(merged) >= 100:
            rho, p_value = stats.spearmanr(merged["commits_prev"], merged["commits_curr"])

            results.append({
                "group": group_name,
                "period": f"{year_prev}-{year_curr}",
                "n_matched": len(merged),
                "rank_correlation_rho": rho,
                "rank_corr_p_value": p_value,
                "top10_persistence": np.nan,
                "bottom50_to_top10_rate": np.nan,
                "interpretation": ""
            })

    return pd.DataFrame(results)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("MECHANISM DIAGNOSTICS: Identifying Power Law Generative Process")
    print("=" * 80)
    print()

    # Load data
    print("Loading panel data...")
    panel = load_panel_data()
    print()

    # Split by org status
    org_panel = panel[panel["is_org"]].copy()
    personal_panel = panel[~panel["is_org"]].copy()

    # ==========================================================================
    # DIAGNOSTIC 1: Attachment Kernel
    # ==========================================================================
    print("=" * 80)
    print("DIAGNOSTIC 1: Attachment Kernel Linearity (β Estimation)")
    print("=" * 80)
    print("""
    Testing: Δx(t) = a * x(t-1)^β
    β ≈ 1 with homoscedastic log residuals → Multiplicative/Gibrat growth
    β ≈ 1 with heteroscedastic residuals → Preferential attachment
    β < 1 → Sublinear (mean reversion)
    β > 1 → Superlinear (winner-take-all)
    """)

    kernel_all = test_attachment_kernel(panel, "All Developers")
    kernel_org = test_attachment_kernel(org_panel, "Org Developers")
    kernel_personal = test_attachment_kernel(personal_panel, "Personal Developers")

    kernel_results = pd.concat([kernel_all, kernel_org, kernel_personal])
    kernel_results.to_csv(OUTPUT_DIR / "mechanism_attachment_kernel.csv", index=False)

    print("\nResults:")
    print(kernel_results[["group", "period", "beta", "beta_se", "r_squared",
                          "residual_hetero_p", "interpretation"]].to_string(index=False))

    # ==========================================================================
    # DIAGNOSTIC 2: Taylor's Law
    # ==========================================================================
    print("\n" + "=" * 80)
    print("DIAGNOSTIC 2: Taylor's Law (Variance Scaling)")
    print("=" * 80)
    print("""
    Testing: Var(x) ~ Mean(x)^τ
    τ ≈ 1 → Poisson process
    τ ≈ 2 → Lognormal / multiplicative growth
    τ > 2 → Heavy-tailed / power law
    """)

    taylor_all = test_taylors_law(panel, "All Developers")
    taylor_org = test_taylors_law(org_panel, "Org Developers")
    taylor_personal = test_taylors_law(personal_panel, "Personal Developers")

    taylor_results = pd.concat([taylor_all, taylor_org, taylor_personal])
    taylor_results.to_csv(OUTPUT_DIR / "mechanism_taylors_law.csv", index=False)

    print("\nResults:")
    print(taylor_results[["group", "year", "tau", "tau_se", "r_squared",
                          "interpretation"]].to_string(index=False))

    # ==========================================================================
    # DIAGNOSTIC 3: Cohort Decomposition
    # ==========================================================================
    print("\n" + "=" * 80)
    print("DIAGNOSTIC 3: Cohort Decomposition (Intensive vs Extensive Margin)")
    print("=" * 80)
    print("""
    Breaking down concentration changes:
    - Intensive margin: Existing top developers increasing output (incumbents)
    - Extensive margin: New developers entering the top (new entrants)

    Kesten + fitness → Intensive margin dominates
    Pure preferential attachment → More extensive margin
    """)

    cohort_all = cohort_decomposition(panel, "All Developers")
    cohort_org = cohort_decomposition(org_panel, "Org Developers")
    cohort_personal = cohort_decomposition(personal_panel, "Personal Developers")

    cohort_results = pd.concat([cohort_all, cohort_org, cohort_personal])
    cohort_results.to_csv(OUTPUT_DIR / "mechanism_cohort_decomposition.csv", index=False)

    print("\nResults:")
    print(cohort_results[["group", "period", "persistence_rate", "new_entrant_rate",
                          "persistent_commit_share", "margin_dominance"]].to_string(index=False))

    # ==========================================================================
    # DIAGNOSTIC 4: Lower Barrier Test
    # ==========================================================================
    print("\n" + "=" * 80)
    print("DIAGNOSTIC 4: Lower Absorbing Barrier Test (Kesten Mechanism)")
    print("=" * 80)
    print("""
    Testing for reflecting barrier at xmin.
    If barrier exists: excess density just above minimum activity level
    Barrier evidence ratio > 1.5 suggests Kesten mechanism
    """)

    barrier_all = test_lower_barrier(panel, "All Developers")
    barrier_org = test_lower_barrier(org_panel, "Org Developers")
    barrier_personal = test_lower_barrier(personal_panel, "Personal Developers")

    barrier_results = pd.concat([barrier_all, barrier_org, barrier_personal])
    barrier_results.to_csv(OUTPUT_DIR / "mechanism_lower_barrier.csv", index=False)

    print("\nResults:")
    print(barrier_results[["group", "year", "barrier_evidence",
                           "interpretation"]].to_string(index=False))

    # ==========================================================================
    # DIAGNOSTIC 5: Rank Persistence
    # ==========================================================================
    print("\n" + "=" * 80)
    print("DIAGNOSTIC 5: Rank Persistence (Fitness Model Test)")
    print("=" * 80)
    print("""
    Testing rank stability over time.
    High ρ + high top persistence → Fitness heterogeneity dominates
    Low ρ + mobility → Pure preferential attachment
    """)

    rank_all = test_rank_persistence(panel, "All Developers")
    rank_org = test_rank_persistence(org_panel, "Org Developers")
    rank_personal = test_rank_persistence(personal_panel, "Personal Developers")

    rank_results = pd.concat([rank_all, rank_org, rank_personal])
    rank_results.to_csv(OUTPUT_DIR / "mechanism_rank_persistence.csv", index=False)

    print("\nResults:")
    cols = ["group", "period", "n_matched", "rank_correlation_rho",
            "top10_persistence", "interpretation"]
    print(rank_results[cols].dropna(subset=["interpretation"]).to_string(index=False))

    # ==========================================================================
    # SUMMARY
    # ==========================================================================
    print("\n" + "=" * 80)
    print("SUMMARY: Mechanism Identification")
    print("=" * 80)

    print("""
    DIAGNOSTIC RESULTS INTERPRETATION:

    1. ATTACHMENT KERNEL (β):
       - If β ≈ 1 with homoscedastic residuals → Multiplicative/Gibrat
       - If β ≈ 1 with heteroscedastic residuals → Preferential attachment
       - If β significantly ≠ 1 → Nonlinear dynamics

    2. TAYLOR'S LAW (τ):
       - τ ≈ 2 → Consistent with lognormal/multiplicative
       - τ > 2 → Power law mechanism

    3. COHORT DECOMPOSITION:
       - Intensive margin dominates → Incumbent advantage (Kesten + fitness)
       - Extensive margin dominates → New entrant dynamics

    4. LOWER BARRIER:
       - Strong evidence → Kesten mechanism confirmed
       - Weak evidence → Pure multiplicative or preferential attachment

    5. RANK PERSISTENCE:
       - High persistence → Fitness heterogeneity
       - Low persistence → Dynamic preferential attachment

    COMBINED INFERENCE:
    - Personal developers: Likely KESTEN/GIBRAT with fitness heterogeneity
      (lognormal body, power tail, barrier at minimum activity)
    - Org developers: Likely PREFERENTIAL ATTACHMENT + institutional dynamics
      (true power law, network effects in organizations)
    """)

    print("\nAll results saved to output/mechanism_*.csv")


if __name__ == "__main__":
    main()
