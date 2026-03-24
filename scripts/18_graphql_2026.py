#!/usr/bin/env python3
"""
GitHub GraphQL API: Get 2026 Q1 commit data for known developers
SIMPLIFIED QUERY (~1 point per request) - should complete in ~2 hours for 10k sample
"""

import requests
import time
import random
import sys
import os
import pandas as pd
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

TOKEN = os.environ.get("GITHUB_TOKEN", "")
if not TOKEN:
    raise ValueError("GITHUB_TOKEN environment variable not set")
HEADERS = {"Authorization": f"bearer {TOKEN}"}
GRAPHQL_URL = "https://api.github.com/graphql"

FROM_DATE = "2026-01-01T00:00:00Z"
TO_DATE = "2026-03-23T23:59:59Z"

SAMPLE_SIZE = 10000  # Enough for power law estimation

# ============================================================================
# SIMPLIFIED QUERY (~1 point per request instead of ~10)
# ============================================================================

QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      restrictedContributionsCount
    }
  }
}
"""

# ============================================================================
# FUNCTIONS
# ============================================================================

def get_commits(login, from_date, to_date):
    """Simple query - just get commit counts."""
    try:
        r = requests.post(
            GRAPHQL_URL,
            json={
                "query": QUERY,
                "variables": {"login": login, "from": from_date, "to": to_date}
            },
            headers=HEADERS,
            timeout=30
        )
        if r.status_code != 200:
            return None

        data = r.json()
        if "errors" in data:
            return None

        user = data.get("data", {}).get("user")
        if not user:
            return None

        col = user["contributionsCollection"]
        public_commits = col["totalCommitContributions"] - col["restrictedContributionsCount"]

        return {
            "actor": login,
            "public_commits": public_commits,
            "total_commits": col["totalCommitContributions"],
        }
    except Exception as e:
        return None


def main():
    output_dir = Path(__file__).parent.parent / "output"

    # Load 2025 developers with their is_org classification
    filepath = output_dir / "filtered_developers_2025.csv"
    df_2025 = pd.read_csv(filepath)
    print(f"Loaded {len(df_2025):,} developers from 2025 data", flush=True)

    # Sample for faster runtime
    random.seed(42)
    if len(df_2025) > SAMPLE_SIZE:
        df_2025 = df_2025.sample(n=SAMPLE_SIZE, random_state=42)
        print(f"Sampled to {len(df_2025):,} developers", flush=True)

    logins = df_2025["actor"].tolist()
    is_org_map = dict(zip(df_2025["actor"], df_2025["is_org"]))
    n_repos_map = dict(zip(df_2025["actor"], df_2025["n_repos"]))

    print(f"\nQuerying {len(logins):,} developers for 2026 Q1...", flush=True)
    print(f"Estimated time: ~{len(logins) / 5000 * 60:.0f} minutes\n", flush=True)

    results = []
    errors = 0

    for i, login in enumerate(logins):
        result = get_commits(login, FROM_DATE, TO_DATE)

        if result:
            # Carry forward is_org and n_repos from 2025 data
            result["is_org"] = is_org_map.get(login, False)
            result["n_repos_2025"] = n_repos_map.get(login, 0)
            results.append(result)
        else:
            errors += 1

        # Rate limiting: ~5000 points/hour = 83/min = 1.4/sec
        # Be conservative: 1 request per second
        time.sleep(0.75)

        # Progress every 100
        if (i + 1) % 100 == 0:
            print(f"  {i + 1:,}/{len(logins):,} — {len(results):,} valid, {errors:,} errors", flush=True)

        # Checkpoint every 1000
        if (i + 1) % 1000 == 0:
            pd.DataFrame(results).to_csv(output_dir / "graphql_2026_checkpoint.csv", index=False)

    print(f"\nDone! {len(results):,} developers with 2026 data", flush=True)

    # Save results
    df = pd.DataFrame(results)
    df.to_csv(output_dir / "graphql_2026_raw.csv", index=False)

    # Filter same as GH Archive (3+ commits, use 2025 n_repos for multi-repo check)
    df_filtered = df[
        (df["public_commits"] >= 3) &
        (df["public_commits"] <= 10000) &
        (df["n_repos_2025"] >= 2)
    ].copy()

    df_filtered.to_csv(output_dir / "graphql_2026_filtered.csv", index=False)

    # Summary
    print(f"\n{'='*60}", flush=True)
    print("2026 Q1 RESULTS", flush=True)
    print("="*60, flush=True)
    print(f"Developers queried: {len(logins):,}", flush=True)
    print(f"Valid responses: {len(df):,}", flush=True)
    print(f"After filters: {len(df_filtered):,}", flush=True)

    org_df = df_filtered[df_filtered["is_org"] == True]
    personal_df = df_filtered[df_filtered["is_org"] == False]
    print(f"\n  Org developers: {len(org_df):,}", flush=True)
    print(f"  Personal-only: {len(personal_df):,}", flush=True)

    if len(df_filtered) > 0:
        print(f"\nCommit distribution:", flush=True)
        print(f"  Mean: {df_filtered['public_commits'].mean():.1f}", flush=True)
        print(f"  Median: {df_filtered['public_commits'].median():.0f}", flush=True)


if __name__ == "__main__":
    main()
