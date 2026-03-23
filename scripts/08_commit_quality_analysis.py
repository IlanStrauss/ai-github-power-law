#!/usr/bin/env python3
"""
Commit Quality Analysis: Quality Proxies from PushEvent Data

This script extracts quality signals to distinguish meaningful contributions
from low-quality commits:

1. Major project contributions - known high-impact repos (kubernetes, react, etc.)
2. Distinct commit ratio - filters merge-heavy accounts
3. Message quality - filters "test", "empty", "asdf" type commits
4. Org vs personal repos - org/repo typically higher quality than user/test-repo

Usage:
    python 08_commit_quality_analysis.py
"""

import gzip
import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Minimum commits to be considered active
MIN_COMMITS = 3

# =============================================================================
# QUALITY SIGNAL 1: Major Projects
# =============================================================================
# Top GitHub projects by stars/impact (curated list)
MAJOR_PROJECTS = {
    # AI/ML
    "tensorflow/tensorflow", "pytorch/pytorch", "huggingface/transformers",
    "keras-team/keras", "scikit-learn/scikit-learn", "openai/openai-python",
    "langchain-ai/langchain", "anthropics/anthropic-sdk-python",

    # Web frameworks
    "facebook/react", "vuejs/vue", "angular/angular", "sveltejs/svelte",
    "vercel/next.js", "nuxt/nuxt", "remix-run/remix",

    # Backend/Infrastructure
    "kubernetes/kubernetes", "docker/docker", "golang/go", "rust-lang/rust",
    "python/cpython", "nodejs/node", "microsoft/typescript",
    "apache/spark", "apache/kafka", "elastic/elasticsearch",

    # DevTools
    "microsoft/vscode", "neovim/neovim", "git/git",
    "github/gh-cli", "cli/cli",

    # Cloud/Infra
    "hashicorp/terraform", "ansible/ansible", "prometheus/prometheus",
    "grafana/grafana", "helm/helm",

    # Databases
    "postgres/postgres", "mongodb/mongo", "redis/redis",

    # Other major
    "microsoft/PowerToys", "home-assistant/core", "bitcoin/bitcoin",
    "ethereum/go-ethereum", "flutter/flutter", "electron/electron",
}

# Major orgs (any repo from these orgs is likely significant)
MAJOR_ORGS = {
    "google", "microsoft", "facebook", "meta", "amazon", "aws",
    "apple", "netflix", "uber", "airbnb", "stripe", "shopify",
    "kubernetes", "docker", "hashicorp", "elastic", "apache",
    "pytorch", "tensorflow", "openai", "anthropic", "huggingface",
    "rust-lang", "golang", "python", "nodejs", "vercel",
}

# =============================================================================
# QUALITY SIGNAL 3: Low-quality commit message patterns
# =============================================================================
LOW_QUALITY_PATTERNS = [
    re.compile(r"^(test|testing|wip|tmp|temp|fix|update|changes?)\.?$", re.I),
    re.compile(r"^(asdf|asd|foo|bar|baz|xxx|yyy|zzz)$", re.I),
    re.compile(r"^\.+$"),  # Just dots
    re.compile(r"^-+$"),   # Just dashes
    re.compile(r"^[a-z]$", re.I),  # Single letter
    re.compile(r"^(empty|blank|placeholder|todo|fixme)\.?\s*(commit)?$", re.I),
    re.compile(r"^(initial|first|start|begin|new)\.?\s*(commit)?$", re.I),
    re.compile(r"^(minor|small|tiny|quick)\.?\s*(fix|change|update)?s?$", re.I),
    re.compile(r"^commit\s*\d*$", re.I),
    re.compile(r"^merge\s+(branch|pull|remote)", re.I),  # Merge commits
    re.compile(r"^Merge pull request #\d+", re.I),
]


def is_major_project(repo_name: str) -> bool:
    """Check if repo is a known major project."""
    return repo_name.lower() in {p.lower() for p in MAJOR_PROJECTS}


def is_major_org(repo_name: str) -> bool:
    """Check if repo belongs to a major organization."""
    if "/" not in repo_name:
        return False
    org = repo_name.split("/")[0].lower()
    return org in MAJOR_ORGS


def is_org_repo(repo_name: str) -> bool:
    """
    Heuristic: org repos often have org names that don't match the repo name.
    Personal repos often follow pattern: username/username or username/project
    where username appears in both.

    Better heuristic: check if org name looks like a company/project vs personal name
    """
    if "/" not in repo_name:
        return False
    org, repo = repo_name.split("/", 1)
    org_lower = org.lower()

    # Known org patterns
    if is_major_org(repo_name):
        return True

    # Heuristics for org-like names
    org_indicators = [
        "-team", "-org", "-io", "-dev", "-labs", "-inc", "-co",
        "official", "community", "foundation", "project"
    ]
    if any(ind in org_lower for ind in org_indicators):
        return True

    # If org name == repo name, likely personal (e.g., username/username.github.io)
    if org_lower == repo.lower().replace(".github.io", "").replace("-", "").replace("_", ""):
        return False

    return False  # Default: assume personal


def is_low_quality_message(message: str) -> bool:
    """Check if commit message indicates low-quality commit."""
    if not message or len(message.strip()) < 3:
        return True

    message_clean = message.strip().split("\n")[0]  # First line only

    for pattern in LOW_QUALITY_PATTERNS:
        if pattern.match(message_clean):
            return True

    return False


def extract_quality_metrics() -> pd.DataFrame:
    """
    Extract quality metrics from raw GH Archive files.

    For each push event, we extract quality signals and aggregate.
    """
    records = []

    files = sorted(RAW_DIR.glob("*.json.gz"))
    if not files:
        raise FileNotFoundError(f"No data files in {RAW_DIR}")

    print(f"Processing {len(files)} files for quality analysis...")

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

                    repo_name = event.get("repo", {}).get("name", "")
                    payload = event.get("payload", {})

                    total_size = payload.get("size", 0)
                    distinct_size = payload.get("distinct_size", 0)
                    commits_list = payload.get("commits", [])

                    if total_size == 0:
                        continue

                    # Quality signals
                    is_major = is_major_project(repo_name)
                    is_org = is_org_repo(repo_name) or is_major_org(repo_name)

                    # Analyze commit messages
                    high_quality_commits = 0
                    low_quality_commits = 0

                    for commit in commits_list:
                        message = commit.get("message", "")
                        if is_low_quality_message(message):
                            low_quality_commits += 1
                        else:
                            high_quality_commits += 1

                    records.append({
                        "date": date_str,
                        "actor_login": actor,
                        "repo_name": repo_name,
                        "total_commits": total_size,
                        "distinct_commits": distinct_size,
                        "is_major_project": is_major,
                        "is_org_repo": is_org,
                        "high_quality_commits": high_quality_commits,
                        "low_quality_commits": low_quality_commits,
                    })

                except json.JSONDecodeError:
                    continue

        print(f"  {filepath.name}: {len(records):,} total records")

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year

    return df


def compute_quality_adjusted_concentration(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute concentration metrics under different quality filters.
    """
    results = []

    for year in sorted(df["year"].unique()):
        year_df = df[df["year"] == year]

        # Aggregate by developer
        dev_stats = (
            year_df.groupby("actor_login")
            .agg({
                "total_commits": "sum",
                "distinct_commits": "sum",
                "is_major_project": "sum",  # count of pushes to major projects
                "is_org_repo": "sum",       # count of pushes to org repos
                "high_quality_commits": "sum",
                "low_quality_commits": "sum",
            })
            .reset_index()
        )

        # Derived metrics
        dev_stats["distinct_ratio"] = dev_stats["distinct_commits"] / dev_stats["total_commits"].clip(lower=1)
        dev_stats["quality_ratio"] = dev_stats["high_quality_commits"] / (
            dev_stats["high_quality_commits"] + dev_stats["low_quality_commits"]
        ).clip(lower=1)

        # Filter to active developers
        dev_stats = dev_stats[dev_stats["total_commits"] >= MIN_COMMITS]

        if len(dev_stats) < 100:
            continue

        def calc_top1_share(commits):
            """Calculate top 1% share."""
            sorted_c = np.sort(commits)[::-1]
            n = len(sorted_c)
            top1_n = max(1, int(n * 0.01))
            return sorted_c[:top1_n].sum() / sorted_c.sum()

        def calc_gini(commits):
            """Calculate Gini coefficient."""
            sorted_c = np.sort(commits)
            n = len(sorted_c)
            index = np.arange(1, n + 1)
            return (2 * np.sum(index * sorted_c) / (n * sorted_c.sum())) - (n + 1) / n

        # Baseline: all commits
        results.append({
            "year": year,
            "filter": "all_commits",
            "n_developers": len(dev_stats),
            "total_commits": dev_stats["total_commits"].sum(),
            "top_1pct_share": calc_top1_share(dev_stats["total_commits"].values),
            "gini": calc_gini(dev_stats["total_commits"].values),
        })

        # Filter 1: Distinct commits only
        results.append({
            "year": year,
            "filter": "distinct_only",
            "n_developers": len(dev_stats),
            "total_commits": dev_stats["distinct_commits"].sum(),
            "top_1pct_share": calc_top1_share(dev_stats["distinct_commits"].values),
            "gini": calc_gini(dev_stats["distinct_commits"].values),
        })

        # Filter 2: High-quality commits only
        hq = dev_stats[dev_stats["high_quality_commits"] >= MIN_COMMITS]
        if len(hq) >= 100:
            results.append({
                "year": year,
                "filter": "high_quality_only",
                "n_developers": len(hq),
                "total_commits": hq["high_quality_commits"].sum(),
                "top_1pct_share": calc_top1_share(hq["high_quality_commits"].values),
                "gini": calc_gini(hq["high_quality_commits"].values),
            })

        # Filter 3: Org repos only
        org_devs = dev_stats[dev_stats["is_org_repo"] > 0]
        if len(org_devs) >= 100:
            results.append({
                "year": year,
                "filter": "org_repos_only",
                "n_developers": len(org_devs),
                "total_commits": org_devs["total_commits"].sum(),
                "top_1pct_share": calc_top1_share(org_devs["total_commits"].values),
                "gini": calc_gini(org_devs["total_commits"].values),
            })

        # Filter 4: Major projects only
        major_devs = dev_stats[dev_stats["is_major_project"] > 0]
        if len(major_devs) >= 50:  # Lower threshold for major projects
            results.append({
                "year": year,
                "filter": "major_projects_only",
                "n_developers": len(major_devs),
                "total_commits": major_devs["total_commits"].sum(),
                "top_1pct_share": calc_top1_share(major_devs["total_commits"].values),
                "gini": calc_gini(major_devs["total_commits"].values),
            })

    return pd.DataFrame(results)


def analyze_quality_by_tier(df: pd.DataFrame) -> pd.DataFrame:
    """
    Do top contributors have higher quality commits?
    """
    results = []

    for year in sorted(df["year"].unique()):
        year_df = df[df["year"] == year]

        # Aggregate by developer
        dev_stats = (
            year_df.groupby("actor_login")
            .agg({
                "total_commits": "sum",
                "distinct_commits": "sum",
                "is_major_project": "sum",
                "is_org_repo": "sum",
                "high_quality_commits": "sum",
                "low_quality_commits": "sum",
            })
            .reset_index()
        )

        # Derived metrics
        dev_stats["distinct_ratio"] = dev_stats["distinct_commits"] / dev_stats["total_commits"].clip(lower=1)
        dev_stats["quality_ratio"] = dev_stats["high_quality_commits"] / (
            dev_stats["high_quality_commits"] + dev_stats["low_quality_commits"]
        ).clip(lower=1)
        dev_stats["major_project_rate"] = (dev_stats["is_major_project"] > 0).astype(int)
        dev_stats["org_repo_rate"] = (dev_stats["is_org_repo"] > 0).astype(int)

        # Filter and rank
        dev_stats = dev_stats[dev_stats["total_commits"] >= MIN_COMMITS]
        dev_stats["rank"] = dev_stats["total_commits"].rank(ascending=False, method="min")
        n_devs = len(dev_stats)

        # Define tiers
        dev_stats["tier"] = "rest"
        dev_stats.loc[dev_stats["rank"] <= n_devs * 0.10, "tier"] = "top_10pct"
        dev_stats.loc[dev_stats["rank"] <= n_devs * 0.01, "tier"] = "top_1pct"

        for tier in ["top_1pct", "top_10pct", "rest"]:
            tier_df = dev_stats[dev_stats["tier"] == tier]
            if len(tier_df) == 0:
                continue

            results.append({
                "year": year,
                "tier": tier,
                "n_developers": len(tier_df),
                "mean_commits": tier_df["total_commits"].mean(),
                "mean_distinct_ratio": tier_df["distinct_ratio"].mean(),
                "mean_quality_ratio": tier_df["quality_ratio"].mean(),
                "pct_major_project": tier_df["major_project_rate"].mean() * 100,
                "pct_org_repo": tier_df["org_repo_rate"].mean() * 100,
            })

    return pd.DataFrame(results)


def main():
    print("=" * 70)
    print("COMMIT QUALITY ANALYSIS")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Extract quality data
    print("\nExtracting quality metrics from raw files...")
    df = extract_quality_metrics()

    print(f"\nTotal push events: {len(df):,}")
    print(f"Total commits: {df['total_commits'].sum():,}")
    print(f"Distinct commits: {df['distinct_commits'].sum():,}")
    print(f"High-quality commits: {df['high_quality_commits'].sum():,}")
    print(f"Low-quality commits: {df['low_quality_commits'].sum():,}")

    # Quality-adjusted concentration
    print("\n" + "-" * 70)
    print("CONCENTRATION BY QUALITY FILTER")
    print("-" * 70)

    conc_df = compute_quality_adjusted_concentration(df)
    conc_df.to_csv(OUTPUT_DIR / "quality_adjusted_concentration.csv", index=False)

    # Show 2024 comparison
    print("\n2024 Concentration by Filter:")
    print(conc_df[conc_df["year"] == 2024][["filter", "n_developers", "top_1pct_share", "gini"]].to_string(index=False))

    # Quality by tier
    print("\n" + "-" * 70)
    print("QUALITY METRICS BY PRODUCTIVITY TIER")
    print("-" * 70)

    tier_df = analyze_quality_by_tier(df)
    tier_df.to_csv(OUTPUT_DIR / "quality_by_tier.csv", index=False)

    print("\n2024 Quality by Tier:")
    cols = ["tier", "n_developers", "mean_distinct_ratio", "mean_quality_ratio", "pct_major_project", "pct_org_repo"]
    print(tier_df[tier_df["year"] == 2024][cols].to_string(index=False))

    # Summary statistics
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    for year in [2019, 2024]:
        year_conc = conc_df[(conc_df["year"] == year) & (conc_df["filter"] == "all_commits")]
        year_hq = conc_df[(conc_df["year"] == year) & (conc_df["filter"] == "high_quality_only")]

        if len(year_conc) > 0 and len(year_hq) > 0:
            print(f"\n{year}:")
            print(f"  All commits - Top 1% share: {year_conc.iloc[0]['top_1pct_share']*100:.1f}%")
            print(f"  High-quality only - Top 1% share: {year_hq.iloc[0]['top_1pct_share']*100:.1f}%")

    print("\n" + "=" * 70)
    print("INTERPRETATION")
    print("=" * 70)
    print("""
KEY QUESTIONS:

1. Does concentration hold for HIGH-QUALITY commits?
   -> If top 1% share is similar for high-quality filter, concentration is real
   -> If it drops significantly, concentration may be inflated by low-quality spam

2. Do superstars contribute to MAJOR PROJECTS?
   -> High pct_major_project for top 1% = real impact
   -> Low pct_major_project = possibly personal projects only

3. Do superstars work in ORGANIZATIONS?
   -> High pct_org_repo for top 1% = professional work
   -> Low pct_org_repo = personal/hobby projects

4. Is the distinct ratio higher for superstars?
   -> Higher = real original work
   -> Lower = may include merge commit inflation
""")


if __name__ == "__main__":
    main()
