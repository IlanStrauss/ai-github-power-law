#!/usr/bin/env python3
"""
Organization Developer Analysis

Analyze developers who contribute to organization-owned repos
(likely professional/company developers) vs personal repos only.

This distinguishes:
- "Org developers": Make at least some commits to org repos (professional)
- "Personal-only": Only commit to personal repos (hobbyists/side projects)
"""

import pandas as pd
import numpy as np
import gzip
import json
import powerlaw
from pathlib import Path
from typing import Dict, Set
import warnings
warnings.filterwarnings('ignore')

PROJECT_ROOT = Path(__file__).parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Known major organizations
MAJOR_ORGS = {
    # Tech giants
    "google", "microsoft", "facebook", "meta", "amazon", "aws", "apple",
    "netflix", "uber", "airbnb", "twitter", "x", "linkedin", "salesforce",
    "oracle", "ibm", "intel", "nvidia", "adobe", "vmware", "cisco",
    # Open source foundations
    "apache", "mozilla", "linux", "kubernetes", "docker", "grafana",
    "elastic", "hashicorp", "redhat", "canonical", "debian", "fedora",
    # Web/Cloud
    "vercel", "netlify", "cloudflare", "digitalocean", "heroku",
    "stripe", "twilio", "shopify", "atlassian", "jetbrains",
    # AI/ML
    "openai", "anthropic", "huggingface", "pytorch", "tensorflow",
    "langchain", "deepmind",
    # Dev tools
    "github", "gitlab", "bitbucket", "npm", "yarn", "webpack",
    "babel", "eslint", "prettier", "rust-lang", "golang", "python",
}

# Bot patterns to exclude
BOT_PATTERNS = [
    "[bot]", "-bot", "dependabot", "renovate", "github-actions",
    "codecov", "greenkeeper", "snyk", "imgbot", "allcontributors",
    "semantic-release", "pre-commit", "mergify", "stale", "coveralls"
]


def is_bot(username: str) -> bool:
    """Check if username matches bot patterns."""
    username_lower = username.lower()
    return any(pattern in username_lower for pattern in BOT_PATTERNS)


def is_org_repo(repo_name: str) -> bool:
    """
    Determine if repo belongs to an organization vs personal account.
    """
    if "/" not in repo_name:
        return False

    owner = repo_name.split("/")[0].lower()

    # Known major orgs
    if owner in MAJOR_ORGS:
        return True

    # Heuristics for org accounts:
    # - Contains company-like suffixes
    # - All lowercase with hyphens (common for orgs)
    # - Doesn't look like a personal username

    company_indicators = [
        "-inc", "-io", "-dev", "-labs", "-team", "-org", "-hq",
        "-official", "-oss", "-foundation", "project-"
    ]

    if any(ind in owner for ind in company_indicators):
        return True

    # Personal accounts often have:
    # - Mixed case
    # - Numbers at end
    # - Very short names

    # This is a simple heuristic - org accounts tend to be longer
    # and use hyphens more frequently
    if len(owner) >= 10 and "-" in owner:
        return True

    return False


def extract_with_org_info():
    """
    Extract commits with organization information preserved.
    """
    raw_files = sorted(RAW_DIR.glob("*.json.gz"))

    if not raw_files:
        raise FileNotFoundError(f"No .json.gz files in {RAW_DIR}")

    print(f"Processing {len(raw_files)} files...")

    # Collect per-developer-year stats
    # Key: (year, actor_login)
    # Value: {total_commits, org_commits, n_repos, n_org_repos}
    developer_stats: Dict[tuple, dict] = {}

    for i, filepath in enumerate(raw_files):
        if i % 20 == 0:
            print(f"  Processing file {i+1}/{len(raw_files)}...")

        # Extract year from filename (e.g., 2024-01-01-0.json.gz)
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

                # Get commit count
                payload = event.get("payload", {})
                distinct_size = payload.get("distinct_size", 0)
                if distinct_size <= 0:
                    continue

                # Check if org repo
                is_org = is_org_repo(repo_name)

                # Update stats
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

    # Convert to DataFrame
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
            "org_commit_share": stats["org_commits"] / stats["total_commits"] if stats["total_commits"] > 0 else 0,
        })

    df = pd.DataFrame(records)
    print(f"\nExtracted {len(df):,} developer-year records")

    return df


def compute_concentration(commits: np.ndarray) -> dict:
    """Compute concentration metrics."""
    n = len(commits)
    if n == 0:
        return None

    total = commits.sum()
    sorted_commits = np.sort(commits)[::-1]

    # Top 1% share
    top_1pct_n = max(1, int(n * 0.01))
    top_1pct_share = sorted_commits[:top_1pct_n].sum() / total * 100

    # Gini
    cumsum = np.cumsum(sorted_commits[::-1])
    gini = 1 - 2 * cumsum.sum() / (n * total)

    return {
        "n_accounts": n,
        "total_commits": int(total),
        "mean_commits": commits.mean(),
        "median_commits": np.median(commits),
        "top_1pct_share": top_1pct_share,
        "gini": gini,
    }


def fit_power_law(commits: np.ndarray) -> dict:
    """Fit power law."""
    if len(commits) < 100:
        return {"alpha": np.nan, "xmin": np.nan}

    fit = powerlaw.Fit(commits, discrete=True, verbose=False)
    return {
        "alpha": fit.power_law.alpha,
        "xmin": fit.power_law.xmin,
    }


def main():
    print("=" * 70)
    print("ORGANIZATION DEVELOPER ANALYSIS")
    print("=" * 70)

    # Extract data with org info
    df = extract_with_org_info()

    # Apply standard filters
    df = df[
        (df["total_commits"] >= 3) &
        (df["total_commits"] <= 10000) &
        (df["n_repos"] >= 2)  # Multi-repo filter
    ]
    print(f"\nAfter filters: {len(df):,} developer-years")

    # Split into org developers vs personal-only
    org_devs = df[df["has_org_commits"] == True]
    personal_devs = df[df["has_org_commits"] == False]

    print(f"\nOrg developers (at least some org commits): {len(org_devs):,}")
    print(f"Personal-only developers: {len(personal_devs):,}")

    # Analyze by year
    results = []

    for year in sorted(df["year"].unique()):
        year_org = org_devs[org_devs["year"] == year]["total_commits"].values
        year_personal = personal_devs[personal_devs["year"] == year]["total_commits"].values

        # Org developers
        if len(year_org) >= 100:
            conc_org = compute_concentration(year_org)
            pl_org = fit_power_law(year_org)
            results.append({
                "year": year,
                "group": "org_developers",
                **conc_org,
                **pl_org
            })

        # Personal-only developers
        if len(year_personal) >= 100:
            conc_personal = compute_concentration(year_personal)
            pl_personal = fit_power_law(year_personal)
            results.append({
                "year": year,
                "group": "personal_only",
                **conc_personal,
                **pl_personal
            })

    results_df = pd.DataFrame(results)

    # Save
    output_file = OUTPUT_DIR / "org_developer_analysis.csv"
    results_df.to_csv(output_file, index=False)
    print(f"\nSaved to: {output_file}")

    # Print comparison
    print("\n" + "=" * 70)
    print("POWER LAW α COMPARISON: Org Developers vs Personal-Only")
    print("=" * 70)

    pivot = results_df.pivot_table(
        index="year",
        columns="group",
        values="alpha"
    )
    print("\nPower Law α:")
    print(pivot.round(2).to_string())

    print("\n" + "=" * 70)
    print("TOP 1% SHARE COMPARISON")
    print("=" * 70)

    pivot2 = results_df.pivot_table(
        index="year",
        columns="group",
        values="top_1pct_share"
    )
    print("\nTop 1% Share (%):")
    print(pivot2.round(1).to_string())

    print("\n" + "=" * 70)
    print("SAMPLE SIZES")
    print("=" * 70)

    pivot3 = results_df.pivot_table(
        index="year",
        columns="group",
        values="n_accounts"
    )
    print("\nN accounts:")
    print(pivot3.astype(int).to_string())


if __name__ == "__main__":
    main()
