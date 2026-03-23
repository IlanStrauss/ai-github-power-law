#!/usr/bin/env python3
"""
Collaboration Analysis: Do Superstars Have More Collaborators?

This script examines whether top contributors achieve high output through:
1. Individual productivity (more commits per repo)
2. Collaboration/coordination (more repos, more co-authors)

We extract:
- Number of distinct repositories per contributor
- Number of distinct commit authors per pusher (team size proxy)
- Whether AI users have different collaboration patterns

Usage:
    python 06_collaboration_analysis.py
"""

import gzip
import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Sample definition: minimum commits to be considered an "active" developer
MIN_COMMITS = 3

# AI detection patterns (same as before)
AI_PATTERNS = {
    "claude": re.compile(r"(?i)(co-authored-by:\s*claude|anthropic|claude\s*(code|sonnet|opus|haiku))"),
    "copilot": re.compile(r"(?i)(co-authored-by:\s*(github\s*)?copilot|copilot)"),
    "gpt": re.compile(r"(?i)(co-authored-by:\s*(openai|gpt|chatgpt)|openai|gpt-[34])"),
    "cursor": re.compile(r"(?i)cursor"),
    "aider": re.compile(r"(?i)\(aider\)|aider"),
}


def extract_collaboration_data() -> pd.DataFrame:
    """
    Extract collaboration metrics from raw GH Archive files.

    For each push event, we extract:
    - actor_login: who pushed
    - repo_name: which repository
    - commit_count: number of commits in push
    - commit_authors: list of distinct commit authors
    - has_ai: whether AI co-author detected
    """
    records = []

    files = sorted(RAW_DIR.glob("*.json.gz"))
    if not files:
        raise FileNotFoundError(f"No data files in {RAW_DIR}")

    print(f"Processing {len(files)} files for collaboration analysis...")

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

                    # Extract repo name
                    repo_name = event.get("repo", {}).get("name", "")

                    payload = event.get("payload", {})
                    commits_list = payload.get("commits", [])
                    commit_count = payload.get("size", 0)

                    if commit_count == 0:
                        continue

                    # Extract distinct commit authors and check for AI
                    commit_authors = set()
                    has_ai = False

                    for commit in commits_list:
                        # Get commit author
                        author_info = commit.get("author", {})
                        author_name = author_info.get("name", "")
                        author_email = author_info.get("email", "")
                        if author_name:
                            commit_authors.add(author_name)

                        # Check for AI patterns
                        message = commit.get("message", "")
                        full_text = f"{message} {author_name}"
                        for pattern in AI_PATTERNS.values():
                            if pattern.search(full_text):
                                has_ai = True
                                break

                    # Is the pusher also the only author? (solo work vs team work)
                    is_solo = len(commit_authors) <= 1

                    records.append({
                        "date": date_str,
                        "actor_login": actor,
                        "repo_name": repo_name,
                        "commits": commit_count,
                        "n_authors": len(commit_authors),
                        "is_solo": is_solo,
                        "has_ai": has_ai,
                    })

                except json.JSONDecodeError:
                    continue

        print(f"  {filepath.name}: {len(records):,} total records")

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year

    return df


def analyze_collaboration_by_tier(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze collaboration metrics by productivity tier.

    For each year:
    - Rank developers by total commits
    - Group into tiers (top 1%, top 10%, rest)
    - Calculate collaboration metrics for each tier
    """
    results = []

    for year in sorted(df["year"].unique()):
        year_df = df[df["year"] == year]

        # Aggregate by developer
        dev_stats = (
            year_df.groupby("actor_login")
            .agg({
                "commits": "sum",
                "repo_name": "nunique",  # distinct repos
                "n_authors": "mean",     # avg authors per push
                "is_solo": "mean",       # fraction of solo pushes
                "has_ai": "max",         # ever used AI
            })
            .reset_index()
        )
        dev_stats.columns = ["actor_login", "total_commits", "n_repos", "avg_authors", "solo_rate", "has_ai"]

        # Filter for active developers (min commits threshold)
        dev_stats = dev_stats[dev_stats["total_commits"] >= MIN_COMMITS]

        # Rank by commits
        dev_stats["rank"] = dev_stats["total_commits"].rank(ascending=False, method="min")
        n_devs = len(dev_stats)

        # Define tiers
        dev_stats["tier"] = "rest"
        dev_stats.loc[dev_stats["rank"] <= n_devs * 0.10, "tier"] = "top_10pct"
        dev_stats.loc[dev_stats["rank"] <= n_devs * 0.01, "tier"] = "top_1pct"

        # Calculate metrics by tier
        for tier in ["top_1pct", "top_10pct", "rest"]:
            tier_df = dev_stats[dev_stats["tier"] == tier]
            if len(tier_df) == 0:
                continue

            results.append({
                "year": year,
                "tier": tier,
                "n_developers": len(tier_df),
                "mean_commits": tier_df["total_commits"].mean(),
                "mean_repos": tier_df["n_repos"].mean(),
                "mean_authors_per_push": tier_df["avg_authors"].mean(),
                "solo_rate": tier_df["solo_rate"].mean(),
                "ai_usage_rate": tier_df["has_ai"].mean(),
                "commits_per_repo": tier_df["total_commits"].sum() / tier_df["n_repos"].sum(),
            })

    return pd.DataFrame(results)


def analyze_ai_and_collaboration(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compare collaboration patterns between AI users and non-AI users.
    """
    results = []

    for year in sorted(df["year"].unique()):
        year_df = df[df["year"] == year]

        # Aggregate by developer
        dev_stats = (
            year_df.groupby("actor_login")
            .agg({
                "commits": "sum",
                "repo_name": "nunique",
                "n_authors": "mean",
                "is_solo": "mean",
                "has_ai": "max",
            })
            .reset_index()
        )
        dev_stats.columns = ["actor_login", "total_commits", "n_repos", "avg_authors", "solo_rate", "has_ai"]

        # Filter for active developers (min commits threshold)
        dev_stats = dev_stats[dev_stats["total_commits"] >= MIN_COMMITS]

        # Split by AI usage
        ai_users = dev_stats[dev_stats["has_ai"] == True]
        non_ai_users = dev_stats[dev_stats["has_ai"] == False]

        if len(ai_users) > 0 and len(non_ai_users) > 0:
            results.append({
                "year": year,
                "n_ai_users": len(ai_users),
                "n_non_ai_users": len(non_ai_users),
                # AI users
                "ai_mean_commits": ai_users["total_commits"].mean(),
                "ai_mean_repos": ai_users["n_repos"].mean(),
                "ai_commits_per_repo": ai_users["total_commits"].sum() / ai_users["n_repos"].sum(),
                "ai_avg_authors": ai_users["avg_authors"].mean(),
                "ai_solo_rate": ai_users["solo_rate"].mean(),
                # Non-AI users
                "non_ai_mean_commits": non_ai_users["total_commits"].mean(),
                "non_ai_mean_repos": non_ai_users["n_repos"].mean(),
                "non_ai_commits_per_repo": non_ai_users["total_commits"].sum() / non_ai_users["n_repos"].sum(),
                "non_ai_avg_authors": non_ai_users["avg_authors"].mean(),
                "non_ai_solo_rate": non_ai_users["solo_rate"].mean(),
            })

    return pd.DataFrame(results)


def analyze_trends_over_time(df: pd.DataFrame) -> pd.DataFrame:
    """
    Track collaboration metrics over time (all developers).
    """
    results = []

    for year in sorted(df["year"].unique()):
        year_df = df[df["year"] == year]

        # Aggregate by developer
        dev_stats = (
            year_df.groupby("actor_login")
            .agg({
                "commits": "sum",
                "repo_name": "nunique",
                "n_authors": "mean",
                "is_solo": "mean",
            })
            .reset_index()
        )

        # Filter for active developers (min commits threshold)
        dev_stats = dev_stats[dev_stats["commits"] >= MIN_COMMITS]

        results.append({
            "year": year,
            "n_developers": len(dev_stats),
            "mean_repos_per_dev": dev_stats["repo_name"].mean(),
            "median_repos_per_dev": dev_stats["repo_name"].median(),
            "p90_repos_per_dev": dev_stats["repo_name"].quantile(0.90),
            "p99_repos_per_dev": dev_stats["repo_name"].quantile(0.99),
            "mean_commits_per_dev": dev_stats["commits"].mean(),
            "overall_solo_rate": dev_stats["is_solo"].mean(),
        })

    return pd.DataFrame(results)


def main():
    print("=" * 70)
    print("COLLABORATION ANALYSIS: Do Superstars Have More Collaborators?")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Extract collaboration data
    print("\nExtracting collaboration data from raw files...")
    df = extract_collaboration_data()

    print(f"\nTotal push events: {len(df):,}")
    print(f"Total commits: {df['commits'].sum():,}")
    print(f"Unique contributors: {df['actor_login'].nunique():,}")
    print(f"Unique repositories: {df['repo_name'].nunique():,}")

    # Analyze by tier
    print("\n" + "-" * 70)
    print("COLLABORATION BY PRODUCTIVITY TIER")
    print("-" * 70)

    tier_df = analyze_collaboration_by_tier(df)
    tier_df.to_csv(OUTPUT_DIR / "collaboration_by_tier.csv", index=False)

    print("\nCollaboration metrics by tier (2024):")
    print(tier_df[tier_df["year"] == 2024][["tier", "n_developers", "mean_commits", "mean_repos", "commits_per_repo", "solo_rate"]].to_string(index=False))

    # Key comparison: top 1% vs rest
    print("\n" + "-" * 70)
    print("TOP 1% vs REST: Key Comparisons")
    print("-" * 70)

    for year in [2019, 2022, 2024]:
        year_tier = tier_df[tier_df["year"] == year]
        top1 = year_tier[year_tier["tier"] == "top_1pct"].iloc[0] if len(year_tier[year_tier["tier"] == "top_1pct"]) > 0 else None
        rest = year_tier[year_tier["tier"] == "rest"].iloc[0] if len(year_tier[year_tier["tier"] == "rest"]) > 0 else None

        if top1 is not None and rest is not None:
            print(f"\n{year}:")
            print(f"  Repos per developer:     Top 1%: {top1['mean_repos']:.1f}   Rest: {rest['mean_repos']:.1f}   Ratio: {top1['mean_repos']/rest['mean_repos']:.1f}x")
            print(f"  Commits per repo:        Top 1%: {top1['commits_per_repo']:.1f}   Rest: {rest['commits_per_repo']:.1f}   Ratio: {top1['commits_per_repo']/rest['commits_per_repo']:.1f}x")
            print(f"  Solo work rate:          Top 1%: {top1['solo_rate']*100:.1f}%   Rest: {rest['solo_rate']*100:.1f}%")

    # AI users vs non-AI users
    print("\n" + "-" * 70)
    print("AI USERS vs NON-AI USERS: Collaboration Patterns")
    print("-" * 70)

    ai_df = analyze_ai_and_collaboration(df)
    ai_df.to_csv(OUTPUT_DIR / "ai_collaboration_comparison.csv", index=False)

    for year in [2022, 2023, 2024]:
        year_ai = ai_df[ai_df["year"] == year]
        if len(year_ai) > 0:
            row = year_ai.iloc[0]
            print(f"\n{year} (n_ai={int(row['n_ai_users'])}, n_non_ai={int(row['n_non_ai_users'])}):")
            print(f"  Mean commits:      AI users: {row['ai_mean_commits']:.1f}   Non-AI: {row['non_ai_mean_commits']:.1f}   Ratio: {row['ai_mean_commits']/row['non_ai_mean_commits']:.1f}x")
            print(f"  Mean repos:        AI users: {row['ai_mean_repos']:.1f}   Non-AI: {row['non_ai_mean_repos']:.1f}   Ratio: {row['ai_mean_repos']/row['non_ai_mean_repos']:.1f}x")
            print(f"  Commits per repo:  AI users: {row['ai_commits_per_repo']:.1f}   Non-AI: {row['non_ai_commits_per_repo']:.1f}   Ratio: {row['ai_commits_per_repo']/row['non_ai_commits_per_repo']:.1f}x")
            print(f"  Solo work rate:    AI users: {row['ai_solo_rate']*100:.1f}%   Non-AI: {row['non_ai_solo_rate']*100:.1f}%")

    # Trends over time
    print("\n" + "-" * 70)
    print("COLLABORATION TRENDS OVER TIME")
    print("-" * 70)

    trends_df = analyze_trends_over_time(df)
    trends_df.to_csv(OUTPUT_DIR / "collaboration_trends.csv", index=False)

    print("\nRepos per developer over time:")
    print(trends_df[["year", "mean_repos_per_dev", "median_repos_per_dev", "p99_repos_per_dev"]].to_string(index=False))

    # Statistical tests
    print("\n" + "=" * 70)
    print("STATISTICAL TESTS")
    print("=" * 70)

    # Test: Do top 1% work on more repos than rest?
    for year in [2019, 2024]:
        year_df_agg = df[df["year"] == year].groupby("actor_login").agg({
            "commits": "sum",
            "repo_name": "nunique",
        }).reset_index()

        year_df_agg["rank"] = year_df_agg["commits"].rank(ascending=False, method="min")
        n_devs = len(year_df_agg)

        top1_repos = year_df_agg[year_df_agg["rank"] <= n_devs * 0.01]["repo_name"]
        rest_repos = year_df_agg[year_df_agg["rank"] > n_devs * 0.01]["repo_name"]

        t_stat, p_val = stats.ttest_ind(top1_repos, rest_repos)
        print(f"\n{year}: Top 1% repos ({top1_repos.mean():.2f}) vs Rest ({rest_repos.mean():.2f})")
        print(f"  t-statistic: {t_stat:.2f}, p-value: {p_val:.4f}")

    print("\n" + "=" * 70)
    print("INTERPRETATION")
    print("=" * 70)
    print("""
KEY QUESTIONS ANSWERED:

1. Do top contributors work on MORE repositories?
   -> Look at mean_repos comparison between top 1% and rest
   -> If ratio > 1, superstars have broader reach

2. Do top contributors have MORE collaborators?
   -> Look at solo_rate: lower = more collaboration
   -> Look at avg_authors_per_push: higher = more team work

3. Do top contributors produce MORE commits per repo?
   -> Look at commits_per_repo ratio
   -> If higher, they're more productive within each repo

4. Do AI users show different patterns?
   -> Compare AI vs non-AI on same metrics
   -> If AI users have higher commits_per_repo, AI boosts individual productivity
   -> If AI users have more repos, AI enables broader reach

CAUSAL INTERPRETATION:
- If superstars have MORE repos but similar commits_per_repo -> breadth strategy
- If superstars have similar repos but HIGHER commits_per_repo -> depth/productivity strategy
- If superstars have BOTH -> they scale on multiple dimensions
""")


if __name__ == "__main__":
    main()
