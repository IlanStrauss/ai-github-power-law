#!/usr/bin/env python3
"""
Data Extraction Module: Best Practices from Academic Literature

Implements filtering recommendations from:
- Kalliamvakou et al. (2014/2016) "Promises and Perils of Mining GitHub"
- MSR bot detection research (Dey et al. 2020)

Quality filters applied:
1. Bot accounts: [bot], dependabot, renovate, github-actions, etc.
2. Low-quality commits: "test", "wip", merge commits, empty messages
3. Distinct commits only: Filters merge commit inflation
4. Minimum activity threshold: MIN_COMMITS per year

This module is imported by analysis scripts for consistent data extraction.
"""

import gzip
import json
import re
from pathlib import Path
from typing import Optional

import pandas as pd

# =============================================================================
# CONFIGURATION
# =============================================================================

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Minimum commits to be considered "active" (Kalliamvakou: 50% have <10)
MIN_COMMITS = 3

# =============================================================================
# BOT DETECTION (from MSR literature)
# =============================================================================

BOT_PATTERNS = [
    "[bot]",           # GitHub Apps: dependabot[bot], renovate[bot]
    "-bot",            # Common suffix: my-ci-bot
    "dependabot",      # Dependency updates
    "renovate",        # Dependency updates
    "github-actions",  # CI/CD
    "codecov",         # Coverage bots
    "greenkeeper",     # Legacy dependency bot
    "snyk",            # Security scanning
    "imgbot",          # Image optimization
    "allcontributors", # Contributor recognition
    "semantic-release",# Release automation
    "pre-commit",      # Pre-commit CI
    "mergify",         # PR automation
    "stale",           # Stale issue bot
    "coveralls",       # Coverage
    "travis",          # CI
    "circleci",        # CI
]


def is_bot(username: str) -> bool:
    """Check if username matches known bot patterns."""
    username_lower = username.lower()
    return any(pattern in username_lower for pattern in BOT_PATTERNS)


# =============================================================================
# LOW-QUALITY COMMIT DETECTION
# =============================================================================

LOW_QUALITY_PATTERNS = [
    # Empty/placeholder
    re.compile(r"^\.+$"),                          # Just dots
    re.compile(r"^-+$"),                           # Just dashes
    re.compile(r"^[a-z]$", re.I),                  # Single letter
    re.compile(r"^(asdf|asd|foo|bar|baz|xxx)$", re.I),

    # Generic/meaningless
    re.compile(r"^(test|testing|wip|tmp|temp)\.?$", re.I),
    re.compile(r"^(fix|update|changes?)\.?$", re.I),
    re.compile(r"^(empty|blank|placeholder|todo)\.?\s*(commit)?$", re.I),
    re.compile(r"^(initial|first|start|new)\.?\s*(commit)?$", re.I),
    re.compile(r"^(minor|small|quick)\.?\s*(fix|change)?s?$", re.I),
    re.compile(r"^commit\s*\d*$", re.I),
    re.compile(r"^save\s*(work|progress|changes)?$", re.I),

    # Merge commits (inflation source)
    re.compile(r"^merge\s+(branch|pull|remote)", re.I),
    re.compile(r"^Merge pull request #\d+", re.I),
    re.compile(r"^Merge branch\s+['\"]", re.I),
]


def is_low_quality_message(message: str) -> bool:
    """
    Check if commit message indicates low-quality/noise commit.

    Returns True if message should be filtered out.
    """
    if not message:
        return True

    # Check first line only (commit title)
    first_line = message.strip().split("\n")[0].strip()

    if len(first_line) < 3:
        return True

    for pattern in LOW_QUALITY_PATTERNS:
        if pattern.match(first_line):
            return True

    return False


# =============================================================================
# ORG VS PERSONAL REPO DETECTION
# =============================================================================

# Known major organizations
MAJOR_ORGS = {
    # Tech giants
    "google", "microsoft", "facebook", "meta", "amazon", "aws", "apple",
    "netflix", "uber", "airbnb", "stripe", "shopify", "linkedin", "twitter",
    "oracle", "ibm", "intel", "nvidia", "adobe", "salesforce", "vmware",

    # Open source foundations/projects
    "apache", "kubernetes", "docker", "hashicorp", "elastic", "grafana",
    "prometheus", "istio", "envoyproxy", "cncf", "linux", "mozilla",

    # AI/ML
    "openai", "anthropic", "huggingface", "pytorch", "tensorflow",
    "langchain-ai", "deepmind", "stability-ai",

    # Languages/Frameworks
    "rust-lang", "golang", "python", "nodejs", "ruby", "php", "dotnet",
    "vuejs", "angular", "facebook",  # React
    "vercel", "remix-run", "sveltejs",

    # Dev tools
    "jetbrains", "github", "gitlab", "atlassian", "hashicorp",
}


def is_org_repo(repo_name: str) -> bool:
    """
    Determine if repo belongs to an organization vs personal account.

    Heuristics:
    - Known major orgs
    - Org-like name patterns (-team, -org, -io, etc.)
    - NOT matching username/username pattern
    """
    if "/" not in repo_name:
        return False

    org, repo = repo_name.split("/", 1)
    org_lower = org.lower()

    # Known orgs
    if org_lower in MAJOR_ORGS:
        return True

    # Org-like name patterns
    org_indicators = ["-team", "-org", "-io", "-dev", "-labs", "-inc", "-co",
                      "-foundation", "-project", "-community", "official"]
    if any(ind in org_lower for ind in org_indicators):
        return True

    # Personal pattern: username/username or username/username.github.io
    repo_clean = repo.lower().replace(".github.io", "").replace("-", "").replace("_", "")
    if org_lower == repo_clean:
        return False

    return False  # Default to personal (conservative)


# =============================================================================
# MAIN EXTRACTION FUNCTION
# =============================================================================

def extract_push_events(
    raw_dir: Path = RAW_DIR,
    file_pattern: str = "*.json.gz",
    filter_bots: bool = True,
    filter_low_quality: bool = True,
    use_distinct_only: bool = True,
    verbose: bool = True,
) -> pd.DataFrame:
    """
    Extract PushEvent data from GH Archive files with quality filters.

    Args:
        raw_dir: Directory containing .json.gz files
        file_pattern: Glob pattern for files
        filter_bots: Remove bot accounts
        filter_low_quality: Remove low-quality commit messages
        use_distinct_only: Use distinct_size instead of size (filters merges)
        verbose: Print progress

    Returns:
        DataFrame with columns:
        - date, year
        - actor_login
        - repo_name, is_org_repo
        - commits (total or distinct based on use_distinct_only)
        - high_quality_commits, low_quality_commits
    """
    records = []

    files = sorted(raw_dir.glob(file_pattern))
    if not files:
        raise FileNotFoundError(f"No files matching {file_pattern} in {raw_dir}")

    if verbose:
        print(f"Processing {len(files)} files...")
        print(f"  Filters: bots={filter_bots}, low_quality={filter_low_quality}, distinct_only={use_distinct_only}")

    stats = {"total_events": 0, "bot_filtered": 0, "low_quality_filtered": 0}

    for filepath in files:
        filename = filepath.stem.replace(".json", "")
        date_str = "-".join(filename.split("-")[:3])

        with gzip.open(filepath, "rt", encoding="utf-8") as f:
            for line in f:
                try:
                    event = json.loads(line)

                    if event.get("type") != "PushEvent":
                        continue

                    stats["total_events"] += 1

                    actor = event.get("actor", {}).get("login")
                    if not actor:
                        continue

                    # Bot filter
                    if filter_bots and is_bot(actor):
                        stats["bot_filtered"] += 1
                        continue

                    repo_name = event.get("repo", {}).get("name", "")
                    payload = event.get("payload", {})

                    total_size = payload.get("size", 0)
                    distinct_size = payload.get("distinct_size", 0)
                    commits_list = payload.get("commits", [])

                    if total_size == 0:
                        continue

                    # Count high/low quality commits
                    high_quality = 0
                    low_quality = 0

                    for commit in commits_list:
                        msg = commit.get("message", "")
                        if is_low_quality_message(msg):
                            low_quality += 1
                        else:
                            high_quality += 1

                    # Determine commit count based on settings
                    if use_distinct_only:
                        commit_count = distinct_size
                    elif filter_low_quality:
                        commit_count = high_quality
                        if commit_count == 0:
                            stats["low_quality_filtered"] += 1
                            continue
                    else:
                        commit_count = total_size

                    if commit_count == 0:
                        continue

                    records.append({
                        "date": date_str,
                        "actor_login": actor,
                        "repo_name": repo_name,
                        "is_org_repo": is_org_repo(repo_name),
                        "commits": commit_count,
                        "total_commits": total_size,
                        "distinct_commits": distinct_size,
                        "high_quality_commits": high_quality,
                        "low_quality_commits": low_quality,
                    })

                except json.JSONDecodeError:
                    continue

        if verbose:
            print(f"  {filepath.name}: {len(records):,} records")

    if verbose:
        print(f"\nExtraction stats:")
        print(f"  Total PushEvents: {stats['total_events']:,}")
        print(f"  Bot filtered: {stats['bot_filtered']:,}")
        print(f"  Low-quality filtered: {stats['low_quality_filtered']:,}")
        print(f"  Final records: {len(records):,}")

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year

    return df


def aggregate_by_developer_year(
    df: pd.DataFrame,
    min_commits: int = MIN_COMMITS,
    commit_col: str = "commits",
) -> pd.DataFrame:
    """
    Aggregate commits per developer per year, with minimum activity filter.

    Args:
        df: DataFrame from extract_push_events
        min_commits: Minimum commits to be included
        commit_col: Which commit column to aggregate

    Returns:
        DataFrame with actor_login, year, total_commits, and quality metrics
    """
    agg = (
        df.groupby(["year", "actor_login"])
        .agg({
            commit_col: "sum",
            "repo_name": "nunique",
            "is_org_repo": "max",
            "high_quality_commits": "sum",
            "low_quality_commits": "sum",
        })
        .reset_index()
    )

    agg.columns = ["year", "actor_login", "total_commits", "n_repos",
                   "has_org_repo", "high_quality", "low_quality"]

    # Quality ratio
    agg["quality_ratio"] = agg["high_quality"] / (agg["high_quality"] + agg["low_quality"]).clip(lower=1)

    # Filter by minimum commits
    n_before = len(agg)
    agg = agg[agg["total_commits"] >= min_commits]
    n_after = len(agg)

    print(f"Filtered {n_before - n_after:,} low-activity accounts (min {min_commits} commits)")
    print(f"Final sample: {n_after:,} developer-years")

    return agg


# =============================================================================
# WATCHEVENT / FORKEVENT EXTRACTION (for stars/forks)
# =============================================================================

def extract_watch_events(
    raw_dir: Path = RAW_DIR,
    file_pattern: str = "*.json.gz",
    verbose: bool = True,
) -> pd.DataFrame:
    """
    Extract WatchEvents (stars) from GH Archive files.

    Note: WatchEvent in GitHub API = starring a repo

    Returns:
        DataFrame with repo_name, star_count (aggregated)
    """
    star_counts = {}

    files = sorted(raw_dir.glob(file_pattern))
    if not files:
        raise FileNotFoundError(f"No files in {raw_dir}")

    if verbose:
        print(f"Extracting WatchEvents from {len(files)} files...")

    for filepath in files:
        with gzip.open(filepath, "rt", encoding="utf-8") as f:
            for line in f:
                try:
                    event = json.loads(line)

                    if event.get("type") != "WatchEvent":
                        continue

                    repo_name = event.get("repo", {}).get("name", "")
                    if repo_name:
                        star_counts[repo_name] = star_counts.get(repo_name, 0) + 1

                except json.JSONDecodeError:
                    continue

        if verbose:
            print(f"  {filepath.name}: {len(star_counts):,} repos with stars")

    df = pd.DataFrame([
        {"repo_name": repo, "star_count": count}
        for repo, count in star_counts.items()
    ])

    return df


def extract_fork_events(
    raw_dir: Path = RAW_DIR,
    file_pattern: str = "*.json.gz",
    verbose: bool = True,
) -> pd.DataFrame:
    """
    Extract ForkEvents from GH Archive files.

    Returns:
        DataFrame with repo_name, fork_count (aggregated)
    """
    fork_counts = {}

    files = sorted(raw_dir.glob(file_pattern))
    if not files:
        raise FileNotFoundError(f"No files in {raw_dir}")

    if verbose:
        print(f"Extracting ForkEvents from {len(files)} files...")

    for filepath in files:
        with gzip.open(filepath, "rt", encoding="utf-8") as f:
            for line in f:
                try:
                    event = json.loads(line)

                    if event.get("type") != "ForkEvent":
                        continue

                    # The forked repo (source)
                    repo_name = event.get("repo", {}).get("name", "")
                    if repo_name:
                        fork_counts[repo_name] = fork_counts.get(repo_name, 0) + 1

                except json.JSONDecodeError:
                    continue

        if verbose:
            print(f"  {filepath.name}: {len(fork_counts):,} repos with forks")

    df = pd.DataFrame([
        {"repo_name": repo, "fork_count": count}
        for repo, count in fork_counts.items()
    ])

    return df


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def load_or_extract(
    cache_path: Optional[Path] = None,
    force_refresh: bool = False,
    **extract_kwargs,
) -> pd.DataFrame:
    """
    Load cached data or extract fresh.
    """
    if cache_path and cache_path.exists() and not force_refresh:
        print(f"Loading cached data from {cache_path}")
        return pd.read_parquet(cache_path)

    df = extract_push_events(**extract_kwargs)

    if cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(cache_path)
        print(f"Cached to {cache_path}")

    return df


if __name__ == "__main__":
    # Test extraction
    print("Testing data extraction module...")

    df = extract_push_events(verbose=True)
    print(f"\nSample of extracted data:")
    print(df.head())

    print(f"\nAggregating by developer-year...")
    dev_year = aggregate_by_developer_year(df)
    print(dev_year.head())
