#!/usr/bin/env python3
"""
Bootstrap Power Law Analysis for Org vs Personal Developers

Following Strauss, Yang & Mazzucato (2025) methodology:
1. Resample data with replacement (N=500 bootstrap iterations)
2. Estimate α for each bootstrap sample
3. Calculate 95% confidence intervals
4. Test whether 2019 and 2024 α are statistically different

This bootstraps the KEY finding: personal developers show increasing
concentration while org developers remain stable.
"""

import pandas as pd
import numpy as np
import gzip
import json
import powerlaw
from pathlib import Path
from typing import Dict, Tuple
import warnings
warnings.filterwarnings('ignore')

PROJECT_ROOT = Path(__file__).parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIR = PROJECT_ROOT / "output"

N_BOOTSTRAP = 500
RANDOM_SEED = 42

# Known major organizations (same as script 12)
MAJOR_ORGS = {
    "google", "microsoft", "facebook", "meta", "amazon", "aws", "apple",
    "netflix", "uber", "airbnb", "twitter", "x", "linkedin", "salesforce",
    "oracle", "ibm", "intel", "nvidia", "adobe", "vmware", "cisco",
    "apache", "mozilla", "linux", "kubernetes", "docker", "grafana",
    "elastic", "hashicorp", "redhat", "canonical", "debian", "fedora",
    "vercel", "netlify", "cloudflare", "digitalocean", "heroku",
    "stripe", "twilio", "shopify", "atlassian", "jetbrains",
    "openai", "anthropic", "huggingface", "pytorch", "tensorflow",
    "langchain", "deepmind",
    "github", "gitlab", "bitbucket", "npm", "yarn", "webpack",
    "babel", "eslint", "prettier", "rust-lang", "golang", "python",
}

BOT_PATTERNS = [
    "[bot]", "-bot", "dependabot", "renovate", "github-actions",
    "codecov", "greenkeeper", "snyk", "imgbot", "allcontributors",
    "semantic-release", "pre-commit", "mergify", "stale", "coveralls"
]


def is_bot(username: str) -> bool:
    username_lower = username.lower()
    return any(pattern in username_lower for pattern in BOT_PATTERNS)


def is_org_repo(repo_name: str) -> bool:
    if "/" not in repo_name:
        return False
    owner = repo_name.split("/")[0].lower()
    if owner in MAJOR_ORGS:
        return True
    company_indicators = [
        "-inc", "-io", "-dev", "-labs", "-team", "-org", "-hq",
        "-official", "-oss", "-foundation", "project-"
    ]
    if any(ind in owner for ind in company_indicators):
        return True
    if len(owner) >= 10 and "-" in owner:
        return True
    return False


def load_org_personal_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load and split data into org developers vs personal-only."""

    # Check if we have cached intermediate data
    cache_file = OUTPUT_DIR / "intermediate" / "org_personal_commits.parquet"

    if cache_file.exists():
        print("Loading cached data...")
        df = pd.read_parquet(cache_file)
    else:
        print("Extracting from raw files (this takes a while)...")
        df = extract_with_org_info()
        cache_file.parent.mkdir(exist_ok=True)
        df.to_parquet(cache_file)

    # Apply standard filters
    df = df[
        (df["total_commits"] >= 3) &
        (df["total_commits"] <= 10000) &
        (df["n_repos"] >= 2)
    ]

    org_devs = df[df["has_org_commits"] == True].copy()
    personal_devs = df[df["has_org_commits"] == False].copy()

    return org_devs, personal_devs


def extract_with_org_info() -> pd.DataFrame:
    """Extract commits with organization information preserved."""
    raw_files = sorted(RAW_DIR.glob("*.json.gz"))

    if not raw_files:
        raise FileNotFoundError(f"No .json.gz files in {RAW_DIR}")

    print(f"Processing {len(raw_files)} files...")

    developer_stats: Dict[tuple, dict] = {}

    for i, filepath in enumerate(raw_files):
        if i % 20 == 0:
            print(f"  Processing file {i+1}/{len(raw_files)}...")

        year = int(filepath.stem.split("-")[0])

        with gzip.open(filepath, "rt", encoding="utf-8") as f:
            for line in f:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if event.get("type") != "PushEvent":
                    continue

                actor = event.get("actor", {}).get("login", "")
                if not actor or is_bot(actor):
                    continue

                repo_name = event.get("repo", {}).get("name", "")
                if not repo_name:
                    continue

                payload = event.get("payload", {})
                distinct_size = payload.get("distinct_size", 0)
                if distinct_size <= 0:
                    continue

                is_org = is_org_repo(repo_name)

                key = (year, actor)
                if key not in developer_stats:
                    developer_stats[key] = {
                        "total_commits": 0,
                        "org_commits": 0,
                        "repos": set(),
                        "org_repos": set(),
                    }

                developer_stats[key]["total_commits"] += distinct_size
                developer_stats[key]["repos"].add(repo_name)

                if is_org:
                    developer_stats[key]["org_commits"] += distinct_size
                    developer_stats[key]["org_repos"].add(repo_name)

    records = []
    for (year, actor), stats in developer_stats.items():
        records.append({
            "year": year,
            "actor_login": actor,
            "total_commits": stats["total_commits"],
            "org_commits": stats["org_commits"],
            "n_repos": len(stats["repos"]),
            "n_org_repos": len(stats["org_repos"]),
            "has_org_commits": stats["org_commits"] > 0,
        })

    return pd.DataFrame(records)


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
        sample = np.random.choice(commits, size=n, replace=True)

        try:
            fit_boot = powerlaw.Fit(sample, discrete=True, verbose=False)
            bootstrap_alphas.append(fit_boot.power_law.alpha)
        except:
            continue

    bootstrap_alphas = np.array(bootstrap_alphas)

    ci_lower = np.percentile(bootstrap_alphas, 2.5)
    ci_upper = np.percentile(bootstrap_alphas, 97.5)

    return point_estimate, ci_lower, ci_upper, bootstrap_alphas


def main():
    print("=" * 70)
    print("BOOTSTRAP POWER LAW: Org Developers vs Personal-Only")
    print(f"N={N_BOOTSTRAP} bootstrap iterations per year per group")
    print("=" * 70)

    # Load data
    org_devs, personal_devs = load_org_personal_data()
    print(f"\nOrg developers: {len(org_devs):,} developer-years")
    print(f"Personal-only: {len(personal_devs):,} developer-years")

    years = sorted(set(org_devs["year"].unique()) & set(personal_devs["year"].unique()))

    results = []
    all_bootstrap_alphas = {"org": {}, "personal": {}}

    # Bootstrap each group separately
    for group_name, group_df in [("org_developers", org_devs), ("personal_only", personal_devs)]:
        print(f"\n{'='*70}")
        print(f"Bootstrapping {group_name.upper()}")
        print("="*70)

        group_key = "org" if "org" in group_name else "personal"

        for year in years:
            year_data = group_df[group_df["year"] == year]["total_commits"].values
            n = len(year_data)

            if n < 100:
                print(f"{year}: n={n} (skipped, too few)")
                continue

            print(f"{year}: n={n:,} ... ", end="", flush=True)

            alpha, ci_lower, ci_upper, boot_alphas = bootstrap_alpha(year_data)
            all_bootstrap_alphas[group_key][year] = boot_alphas

            se = np.std(boot_alphas)

            results.append({
                "group": group_name,
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
    output_file = OUTPUT_DIR / "bootstrap_org_personal_results.csv"
    results_df.to_csv(output_file, index=False)
    print(f"\n\nSaved to: {output_file}")

    # Print formatted comparison table
    print("\n" + "=" * 70)
    print("BOOTSTRAP RESULTS: Power Law α with 95% Confidence Intervals")
    print("=" * 70)

    for group in ["org_developers", "personal_only"]:
        group_results = results_df[results_df["group"] == group]
        print(f"\n{group.upper()}:")
        print(f"{'Year':<6} {'n':>10} {'α':>8} {'SE':>8} {'95% CI':>20}")
        print("-" * 60)
        for _, row in group_results.iterrows():
            ci_str = f"[{row['ci_lower']:.3f}, {row['ci_upper']:.3f}]"
            print(f"{int(row['year']):<6} {int(row['n']):>10,} {row['alpha']:>8.3f} {row['se']:>8.3f} {ci_str:>20}")

    # Test 2019 vs 2024 significance for EACH group
    print("\n" + "=" * 70)
    print("SIGNIFICANCE TESTS: 2019 vs 2024 within each group")
    print("=" * 70)

    for group_key, group_name in [("org", "Org Developers"), ("personal", "Personal-Only")]:
        print(f"\n{group_name}:")

        if 2019 in all_bootstrap_alphas[group_key] and 2024 in all_bootstrap_alphas[group_key]:
            alpha_2019 = all_bootstrap_alphas[group_key][2019]
            alpha_2024 = all_bootstrap_alphas[group_key][2024]

            n_compare = min(len(alpha_2019), len(alpha_2024))
            diff = alpha_2019[:n_compare] - alpha_2024[:n_compare]

            mean_diff = np.mean(diff)
            se_diff = np.std(diff)
            ci_diff_lower = np.percentile(diff, 2.5)
            ci_diff_upper = np.percentile(diff, 97.5)

            # p-value: proportion of bootstrap samples where 2019 <= 2024
            p_value = np.mean(diff <= 0)

            print(f"  α(2019) - α(2024) = {mean_diff:.3f}")
            print(f"  SE of difference = {se_diff:.3f}")
            print(f"  95% CI: [{ci_diff_lower:.3f}, {ci_diff_upper:.3f}]")

            if ci_diff_lower > 0:
                print(f"  *** SIGNIFICANT DECLINE: α decreased from 2019 to 2024 ***")
            elif ci_diff_upper < 0:
                print(f"  *** SIGNIFICANT INCREASE: α increased from 2019 to 2024 ***")
            else:
                print(f"  Not significant: CI includes 0")

            print(f"  p-value (one-tailed, H0: α_2019 ≤ α_2024): {p_value:.4f}")

    # Compare Org vs Personal in 2024
    print("\n" + "=" * 70)
    print("SIGNIFICANCE TEST: Org vs Personal in 2024")
    print("=" * 70)

    if 2024 in all_bootstrap_alphas["org"] and 2024 in all_bootstrap_alphas["personal"]:
        alpha_org_2024 = all_bootstrap_alphas["org"][2024]
        alpha_personal_2024 = all_bootstrap_alphas["personal"][2024]

        n_compare = min(len(alpha_org_2024), len(alpha_personal_2024))
        diff = alpha_org_2024[:n_compare] - alpha_personal_2024[:n_compare]

        mean_diff = np.mean(diff)
        ci_diff_lower = np.percentile(diff, 2.5)
        ci_diff_upper = np.percentile(diff, 97.5)

        print(f"\nα(Org) - α(Personal) in 2024 = {mean_diff:.3f}")
        print(f"95% CI: [{ci_diff_lower:.3f}, {ci_diff_upper:.3f}]")

        if ci_diff_lower > 0:
            print("*** Org developers have SIGNIFICANTLY HIGHER α (less concentrated) ***")
        elif ci_diff_upper < 0:
            print("*** Personal developers have SIGNIFICANTLY HIGHER α (less concentrated) ***")
        else:
            print("Not significant: CI includes 0")


if __name__ == "__main__":
    main()
