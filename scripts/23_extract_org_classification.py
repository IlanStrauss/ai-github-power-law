#!/usr/bin/env python3
"""
Extract Developer Data with Organization Classification

Creates a parquet file with developer-level org classification that can be
used by downstream analyses (Zipf, transition matrix, etc.)

Classification:
- "org_developer": At least one commit to an organization-owned repo
- "personal_only": Only commits to personal repos
"""

import pandas as pd
import numpy as np
import gzip
import json
from pathlib import Path
from typing import Dict, Set

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

BOT_PATTERNS = [
    "[bot]", "-bot", "dependabot", "renovate", "github-actions",
    "codecov", "greenkeeper", "snyk", "imgbot", "allcontributors",
    "semantic-release", "pre-commit", "mergify", "stale", "coveralls"
]


def is_bot(username: str) -> bool:
    username_lower = username.lower()
    return any(pattern in username_lower for pattern in BOT_PATTERNS)


def is_org_repo(repo_name: str) -> bool:
    """Determine if repo belongs to an organization vs personal account."""
    if "/" not in repo_name:
        return False

    owner = repo_name.split("/")[0].lower()

    # Known major orgs
    if owner in MAJOR_ORGS:
        return True

    # Heuristics for org accounts
    company_indicators = [
        "-inc", "-io", "-dev", "-labs", "-team", "-org", "-hq",
        "-official", "-oss", "-foundation", "project-"
    ]

    if any(ind in owner for ind in company_indicators):
        return True

    # Org accounts tend to be longer with hyphens
    if len(owner) >= 10 and "-" in owner:
        return True

    return False


def extract_with_org_classification():
    """Extract commits with organization classification preserved."""
    raw_files = sorted(RAW_DIR.glob("*.json.gz"))

    if not raw_files:
        raise FileNotFoundError(f"No .json.gz files in {RAW_DIR}")

    print(f"Processing {len(raw_files)} files...")

    # Key: (year, actor_login)
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
            "is_org_developer": stats["org_commits"] > 0,
        })

    df = pd.DataFrame(records)
    print(f"\nExtracted {len(df):,} developer-year records")

    return df


def main():
    print("=" * 70)
    print("EXTRACTING DEVELOPER DATA WITH ORG CLASSIFICATION")
    print("=" * 70)

    df = extract_with_org_classification()

    # Apply standard filters
    df_filtered = df[
        (df["total_commits"] >= 3) &
        (df["total_commits"] <= 10000) &
        (df["n_repos"] >= 2)
    ].copy()

    print(f"\nAfter filters: {len(df_filtered):,} developer-years")
    print(f"  Org developers: {df_filtered['is_org_developer'].sum():,}")
    print(f"  Personal-only:  {(~df_filtered['is_org_developer']).sum():,}")

    # Save
    output_file = OUTPUT_DIR / "all_developers_with_org.parquet"
    df_filtered.to_parquet(output_file, index=False)
    print(f"\nSaved to: {output_file}")

    # Summary by year
    print("\n" + "=" * 70)
    print("BREAKDOWN BY YEAR")
    print("=" * 70)

    summary = df_filtered.groupby(['year', 'is_org_developer']).size().unstack(fill_value=0)
    summary.columns = ['Personal', 'Org']
    print(summary)


if __name__ == "__main__":
    main()
