#!/usr/bin/env python3
"""
Bootstrap Power Law Analysis - PERSONAL-ONLY DEVELOPERS

Run this after 13a_bootstrap_org.py completes.
"""

import pandas as pd
import numpy as np
import powerlaw
from pathlib import Path
import gzip
import json
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


def is_bot(username):
    username_lower = username.lower()
    return any(pattern in username_lower for pattern in BOT_PATTERNS)


def is_org_repo(repo_name):
    if "/" not in repo_name:
        return False
    owner = repo_name.split("/")[0].lower()
    if owner in MAJOR_ORGS:
        return True
    company_indicators = ["-inc", "-io", "-dev", "-labs", "-team", "-org", "-hq",
                         "-official", "-oss", "-foundation", "project-"]
    if any(ind in owner for ind in company_indicators):
        return True
    if len(owner) >= 10 and "-" in owner:
        return True
    return False


def bootstrap_alpha(commits: np.ndarray, n_bootstrap: int = N_BOOTSTRAP,
                    seed: int = RANDOM_SEED):
    """Bootstrap the power law α estimate."""
    np.random.seed(seed)
    n = len(commits)
    bootstrap_alphas = []

    # Point estimate
    fit = powerlaw.Fit(commits, discrete=True, verbose=False)
    point_estimate = fit.power_law.alpha

    # Bootstrap
    for i in range(n_bootstrap):
        if i % 100 == 0:
            print(f"    iteration {i}/{n_bootstrap}", flush=True)
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
    print("BOOTSTRAP: PERSONAL-ONLY DEVELOPERS")
    print(f"N={N_BOOTSTRAP} bootstrap iterations per year")
    print("=" * 70, flush=True)

    # Extract personal developer commits
    print("\nExtracting personal developer commits...", flush=True)
    raw_files = sorted(RAW_DIR.glob("*.json.gz"))

    developer_stats = {}

    for i, filepath in enumerate(raw_files):
        if i % 20 == 0:
            print(f"  Processing file {i+1}/{len(raw_files)}...", flush=True)

        year = int(filepath.stem.split("-")[0])

        with gzip.open(filepath, "rt", encoding="utf-8") as f:
            for line in f:
                try:
                    event = json.loads(line)
                except:
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
                    }

                developer_stats[key]["total_commits"] += distinct_size
                developer_stats[key]["repos"].add(repo_name)
                if is_org:
                    developer_stats[key]["org_commits"] += distinct_size

    # Convert to dataframe and filter for PERSONAL-ONLY developers
    print("\nFiltering for personal-only developers...", flush=True)
    records = []
    for (year, actor), stats in developer_stats.items():
        if stats["org_commits"] == 0:  # NO org commits = personal only
            if stats["total_commits"] >= 3 and stats["total_commits"] <= 10000:
                if len(stats["repos"]) >= 2:
                    records.append({
                        "year": year,
                        "total_commits": stats["total_commits"],
                    })

    df = pd.DataFrame(records)
    print(f"Personal-only developers after filters: {len(df):,}", flush=True)

    # Bootstrap by year
    results = []
    all_bootstrap_alphas = {}

    for year in sorted(df["year"].unique()):
        year_data = df[df["year"] == year]["total_commits"].values
        n = len(year_data)

        print(f"\n{year}: n={n:,}", flush=True)

        if n < 100:
            print("  Skipped (too few)", flush=True)
            continue

        alpha, ci_lower, ci_upper, boot_alphas = bootstrap_alpha(year_data)
        all_bootstrap_alphas[year] = boot_alphas

        se = np.std(boot_alphas)

        results.append({
            "group": "personal_only",
            "year": year,
            "n": n,
            "alpha": alpha,
            "se": se,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
        })

        print(f"  α = {alpha:.3f} [{ci_lower:.3f}, {ci_upper:.3f}]", flush=True)

    # Save results
    results_df = pd.DataFrame(results)
    output_file = OUTPUT_DIR / "bootstrap_personal_developers.csv"
    results_df.to_csv(output_file, index=False)
    print(f"\nSaved to: {output_file}", flush=True)

    # Test 2019 vs 2024
    print("\n" + "=" * 70)
    print("SIGNIFICANCE TEST: 2019 vs 2024")
    print("=" * 70, flush=True)

    if 2019 in all_bootstrap_alphas and 2024 in all_bootstrap_alphas:
        alpha_2019 = all_bootstrap_alphas[2019]
        alpha_2024 = all_bootstrap_alphas[2024]

        n_compare = min(len(alpha_2019), len(alpha_2024))
        diff = alpha_2019[:n_compare] - alpha_2024[:n_compare]

        mean_diff = np.mean(diff)
        ci_diff_lower = np.percentile(diff, 2.5)
        ci_diff_upper = np.percentile(diff, 97.5)

        print(f"\nα(2019) - α(2024) = {mean_diff:.3f}")
        print(f"95% CI: [{ci_diff_lower:.3f}, {ci_diff_upper:.3f}]")

        if ci_diff_lower > 0:
            print("*** SIGNIFICANT DECLINE: α decreased from 2019 to 2024 ***")
        elif ci_diff_upper < 0:
            print("*** SIGNIFICANT INCREASE ***")
        else:
            print("Not significant (CI includes 0)")


if __name__ == "__main__":
    main()
