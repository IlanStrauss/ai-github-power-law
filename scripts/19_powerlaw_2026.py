#!/usr/bin/env python3
"""
Power Law Analysis for 2026 Q1 (GraphQL API Data)
Compares to 2025 methodology from scripts 16 and 13
"""

import pandas as pd
import numpy as np
import powerlaw
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("POWER LAW ANALYSIS: 2026 Q1 (Jan-Mar)")
print("=" * 60)

# Load GraphQL data - try final first, then checkpoint
try:
    df = pd.read_csv("output/graphql_2026_filtered.csv")
    print(f"Loaded FINAL filtered data: {len(df):,} developers")
except FileNotFoundError:
    df = pd.read_csv("output/graphql_2026_checkpoint.csv")
    print(f"Loaded CHECKPOINT data: {len(df):,} developers")

    # Apply same filters as GH Archive analysis
    # Note: public_commits can be negative due to API quirk - use max(0, x)
    df["public_commits"] = df["public_commits"].clip(lower=0)

    df = df[
        (df["public_commits"] >= 3) &
        (df["public_commits"] <= 10000) &
        (df["n_repos_2025"] >= 2)
    ]
    print(f"After filters: {len(df):,} developers")

print(f"\nCommit column: public_commits")
print(f"  Min: {df['public_commits'].min()}")
print(f"  Max: {df['public_commits'].max()}")
print(f"  Mean: {df['public_commits'].mean():.1f}")
print(f"  Median: {df['public_commits'].median():.0f}")

# Split into org vs personal (using 2025 classification)
org_df = df[df["is_org"] == True]
personal_df = df[df["is_org"] == False]

print(f"\n  Org developers: {len(org_df):,}")
print(f"  Personal-only: {len(personal_df):,}")

# Bootstrap configuration
N_BOOTSTRAP = 500
np.random.seed(42)

def bootstrap_alpha(commits, n_bootstrap=N_BOOTSTRAP):
    """Bootstrap power law alpha with 95% CI."""
    n = len(commits)

    # Point estimate
    fit = powerlaw.Fit(commits, discrete=True, verbose=False)
    point_alpha = fit.power_law.alpha
    point_xmin = fit.power_law.xmin

    # Compare to log-normal
    R, p = fit.distribution_compare('power_law', 'lognormal', normalized_ratio=True)

    # Bootstrap
    bootstrap_alphas = []
    for _ in range(n_bootstrap):
        sample = np.random.choice(commits, size=n, replace=True)
        try:
            fit_boot = powerlaw.Fit(sample, discrete=True, verbose=False)
            bootstrap_alphas.append(fit_boot.power_law.alpha)
        except:
            continue

    bootstrap_alphas = np.array(bootstrap_alphas)
    ci_lower = np.percentile(bootstrap_alphas, 2.5)
    ci_upper = np.percentile(bootstrap_alphas, 97.5)
    se = np.std(bootstrap_alphas)

    return {
        "alpha": point_alpha,
        "xmin": point_xmin,
        "se": se,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "R": R,
        "n_bootstrap": len(bootstrap_alphas)
    }

results = []

for group_name, group_df in [("Org Developers", org_df), ("Personal-Only", personal_df)]:
    print(f"\n{'='*60}")
    print(f"{group_name.upper()}")
    print("="*60)

    commits = group_df["public_commits"].values
    n = len(commits)

    if n < 100:
        print(f"  n = {n} (too few for reliable estimation)")
        continue

    print(f"  n = {n:,}")
    print(f"  Bootstrapping {N_BOOTSTRAP} samples...", end=" ", flush=True)

    result = bootstrap_alpha(commits)

    print("done")
    print(f"  α = {result['alpha']:.3f} [{result['ci_lower']:.3f}, {result['ci_upper']:.3f}]")
    print(f"  SE = {result['se']:.3f}")
    print(f"  xmin = {result['xmin']:.0f}")
    print(f"  R vs log-normal = {result['R']:+.2f}")

    results.append({
        "group": group_name,
        "year": "2026 Q1",
        "n": n,
        "alpha": result["alpha"],
        "se": result["se"],
        "ci_lower": result["ci_lower"],
        "ci_upper": result["ci_upper"],
        "xmin": result["xmin"],
        "R": result["R"],
    })

# Save results
results_df = pd.DataFrame(results)
results_df.to_csv("output/powerlaw_2026_q1.csv", index=False)
print(f"\nSaved: output/powerlaw_2026_q1.csv")

# Compare to 2025 results
print("\n" + "=" * 60)
print("COMPARISON: 2025 vs 2026 Q1")
print("=" * 60)

try:
    df_2025 = pd.read_csv("output/powerlaw_2025.csv")

    print(f"\n{'Year':<10} {'Group':<15} {'n':>10} {'α':>8} {'95% CI':>20}")
    print("-" * 70)

    for _, row in df_2025.iterrows():
        ci_str = "—"  # No CI for 2025 if not bootstrapped
        print(f"{int(row['year']):<10} {row['group']:<15} {int(row['n']):>10,} {row['alpha']:>8.3f} {ci_str:>20}")

    for _, row in results_df.iterrows():
        ci_str = f"[{row['ci_lower']:.3f}, {row['ci_upper']:.3f}]"
        print(f"{row['year']:<10} {row['group']:<15} {int(row['n']):>10,} {row['alpha']:>8.3f} {ci_str:>20}")

except FileNotFoundError:
    print("2025 results not found for comparison")

print("\n" + "=" * 60)
print("INTERPRETATION")
print("=" * 60)
print("""
NOTE: 2026 Q1 data comes from GitHub GraphQL API, querying a random sample
of 10,000 developers known from 2025 GH Archive data. This means:

1. SURVIVORSHIP BIAS: We only see developers who were active in 2025.
   New developers who started in 2026 are NOT captured.

2. SAMPLE SIZE: Smaller n than full GH Archive analysis, but sufficient
   for power law estimation (α is scale-invariant).

3. CLASSIFICATION: Org vs Personal classification is carried forward
   from 2025 data - developers don't change classification.

4. COMPARABILITY: Commit counts should be comparable (both are public
   commits), but filtering criteria differ slightly.
""")
