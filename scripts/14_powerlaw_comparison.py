#!/usr/bin/env python3
"""
Power Law vs Log-Normal Comparison for Org/Personal Samples

Runs the full Clauset-Shalizi-Newman analysis on both subsamples:
- xmin estimation
- α (power law exponent)
- R statistic (comparison vs log-normal)
- Best fit determination
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

# Known major organizations
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


def fit_powerlaw_full(commits):
    """Fit power law and compare to log-normal."""
    if len(commits) < 100:
        return None

    fit = powerlaw.Fit(commits, discrete=True, verbose=False)

    # Compare to log-normal
    R, p = fit.distribution_compare('power_law', 'lognormal', normalized_ratio=True)

    best_fit = "Power law" if R > 0 else "Log-normal"

    return {
        "alpha": fit.power_law.alpha,
        "xmin": fit.power_law.xmin,
        "R": R,
        "p_value": p,
        "best_fit": best_fit,
    }


def main():
    print("=" * 70)
    print("POWER LAW vs LOG-NORMAL COMPARISON")
    print("Separate analysis for Org and Personal developers")
    print("=" * 70, flush=True)

    # Extract data with org info
    print("\nExtracting commits...", flush=True)
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

    # Split into org and personal
    print("\nSplitting into org/personal...", flush=True)

    org_records = []
    personal_records = []

    for (year, actor), stats in developer_stats.items():
        if stats["total_commits"] >= 3 and stats["total_commits"] <= 10000:
            if len(stats["repos"]) >= 2:
                record = {"year": year, "total_commits": stats["total_commits"]}
                if stats["org_commits"] > 0:
                    org_records.append(record)
                else:
                    personal_records.append(record)

    org_df = pd.DataFrame(org_records)
    personal_df = pd.DataFrame(personal_records)

    print(f"Org developers: {len(org_df):,}")
    print(f"Personal-only: {len(personal_df):,}")

    # Analyze each group
    results = []

    for group_name, df in [("Org Developers", org_df), ("Personal-Only", personal_df)]:
        print(f"\n{'='*70}")
        print(f"ANALYZING: {group_name.upper()}")
        print("="*70, flush=True)

        for year in sorted(df["year"].unique()):
            year_data = df[df["year"] == year]["total_commits"].values
            n = len(year_data)

            if n < 100:
                continue

            print(f"\n{year}: n={n:,}", flush=True)

            result = fit_powerlaw_full(year_data)

            if result:
                results.append({
                    "group": group_name,
                    "year": year,
                    "n": n,
                    **result
                })

                print(f"  α = {result['alpha']:.2f}, xmin = {result['xmin']:.0f}")
                print(f"  R = {result['R']:+.2f} → {result['best_fit']}")

    # Save results
    results_df = pd.DataFrame(results)
    output_file = OUTPUT_DIR / "powerlaw_lognormal_comparison.csv"
    results_df.to_csv(output_file, index=False)
    print(f"\n\nSaved to: {output_file}", flush=True)

    # Print formatted tables
    print("\n" + "=" * 70)
    print("SUMMARY TABLES")
    print("=" * 70)

    for group in ["Org Developers", "Personal-Only"]:
        group_df = results_df[results_df["group"] == group]
        print(f"\n{group}:")
        print(f"{'Year':<6} {'n':>10} {'α':>8} {'xmin':>8} {'R':>8} {'Best Fit':>12}")
        print("-" * 60)
        for _, row in group_df.iterrows():
            print(f"{int(row['year']):<6} {int(row['n']):>10,} {row['alpha']:>8.2f} {row['xmin']:>8.0f} {row['R']:>+8.2f} {row['best_fit']:>12}")


if __name__ == "__main__":
    main()
