#!/usr/bin/env python3
"""
Power Law Analysis for 2025 (Jan-Oct)
Same methodology as 2019-2024 analysis
"""

import pandas as pd
import numpy as np
import powerlaw
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("POWER LAW ANALYSIS: 2025 (Jan-Oct)")
print("=" * 60)

# Load filtered data
df = pd.read_csv("output/filtered_developers_2025.csv")
print(f"Loaded {len(df):,} developers")

# Split into org vs personal
org_df = df[df["is_org"] == True]
personal_df = df[df["is_org"] == False]

print(f"  Org developers: {len(org_df):,}")
print(f"  Personal-only: {len(personal_df):,}")

results = []

for group_name, group_df in [("Org Developers", org_df), ("Personal-Only", personal_df)]:
    print(f"\n{'='*60}")
    print(f"{group_name.upper()}")
    print("="*60)
    
    commits = group_df["total_commits"].values
    n = len(commits)
    
    print(f"n = {n:,}")
    
    # Fit power law
    fit = powerlaw.Fit(commits, discrete=True, verbose=False)
    
    # Compare to log-normal
    R, p = fit.distribution_compare('power_law', 'lognormal', normalized_ratio=True)
    
    alpha = fit.power_law.alpha
    xmin = fit.power_law.xmin
    best_fit = "Power law" if R > 0 else "Log-normal"
    
    print(f"  α = {alpha:.2f}")
    print(f"  xmin = {xmin:.0f}")
    print(f"  R = {R:+.2f} → {best_fit}")
    
    results.append({
        "group": group_name,
        "year": 2025,
        "n": n,
        "alpha": alpha,
        "xmin": xmin,
        "R": R,
        "best_fit": best_fit,
    })

# Save results
results_df = pd.DataFrame(results)
results_df.to_csv("output/powerlaw_2025.csv", index=False)
print(f"\nSaved: output/powerlaw_2025.csv")

print("\n" + "=" * 60)
print("SUMMARY: 2025 vs Previous Years")
print("=" * 60)

# Load previous results for comparison
try:
    prev_df = pd.read_csv("output/powerlaw_lognormal_comparison.csv")
    
    print(f"\n{'Year':<6} {'Group':<15} {'n':>10} {'α':>8} {'xmin':>6} {'R':>8}")
    print("-" * 60)
    
    for _, row in prev_df[prev_df["year"] >= 2022].iterrows():
        print(f"{int(row['year']):<6} {row['group']:<15} {int(row['n']):>10,} {row['alpha']:>8.2f} {row['xmin']:>6.0f} {row['R']:>+8.2f}")
    
    for _, row in results_df.iterrows():
        print(f"{int(row['year']):<6} {row['group']:<15} {int(row['n']):>10,} {row['alpha']:>8.2f} {row['xmin']:>6.0f} {row['R']:>+8.2f}")
        
except FileNotFoundError:
    print("Previous results not found")

print("\n" + "=" * 60)
print("KEY FINDING")
print("=" * 60)
