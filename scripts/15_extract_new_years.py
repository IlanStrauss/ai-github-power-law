#!/usr/bin/env python3
"""
Extract and filter 2025 + 2026 data
Same filters as existing 2019-2024 analysis
"""

import gzip
import json
from pathlib import Path
from collections import defaultdict
import pandas as pd

RAW_DIR = Path("data/raw")
OUTPUT_DIR = Path("output")

# Same bot patterns as existing analysis
BOT_PATTERNS = [
    "[bot]", "-bot", "dependabot", "renovate", "github-actions",
    "codecov", "greenkeeper", "snyk", "imgbot", "allcontributors",
    "semantic-release", "pre-commit", "mergify", "stale", "coveralls"
]

# Same org detection as existing analysis
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

# Process each year
for year in [2025, 2026]:
    print(f"\n{'='*60}")
    print(f"PROCESSING {year}")
    print('='*60)
    
    year_files = sorted(RAW_DIR.glob(f"{year}-*.json.gz"))
    print(f"Files: {len(year_files)}")
    
    # Extract raw data
    developer_stats = defaultdict(lambda: {"commits": 0, "org_commits": 0, "repos": set()})
    total_events = 0
    push_events = 0
    
    for i, fpath in enumerate(year_files):
        if i % 10 == 0:
            print(f"  Processing {fpath.name}...")
        
        with gzip.open(fpath, "rt", encoding="utf-8", errors="replace") as f:
            for line in f:
                total_events += 1
                try:
                    event = json.loads(line)
                except:
                    continue
                
                if event.get("type") != "PushEvent":
                    continue
                push_events += 1
                
                actor = event.get("actor", {}).get("login", "")
                if not actor:
                    continue
                
                # Filter: bot exclusion
                if is_bot(actor):
                    continue
                
                repo = event.get("repo", {}).get("name", "")
                distinct_size = event.get("payload", {}).get("distinct_size", 0)
                
                if distinct_size > 0:
                    developer_stats[actor]["commits"] += distinct_size
                    developer_stats[actor]["repos"].add(repo)
                    if is_org_repo(repo):
                        developer_stats[actor]["org_commits"] += distinct_size
    
    print(f"\nRaw extraction:")
    print(f"  Total events: {total_events:,}")
    print(f"  Push events: {push_events:,}")
    print(f"  Unique developers (pre-filter): {len(developer_stats):,}")
    
    # Apply filters: 3-10000 commits, 2+ repos
    filtered_devs = []
    for actor, stats in developer_stats.items():
        if 3 <= stats["commits"] <= 10000 and len(stats["repos"]) >= 2:
            filtered_devs.append({
                "year": year,
                "actor": actor,
                "total_commits": stats["commits"],
                "org_commits": stats["org_commits"],
                "n_repos": len(stats["repos"]),
                "is_org": stats["org_commits"] > 0,
            })
    
    print(f"\nAfter filters (3-10000 commits, 2+ repos):")
    print(f"  Developers: {len(filtered_devs):,}")
    
    # Split org vs personal
    org_devs = [d for d in filtered_devs if d["is_org"]]
    personal_devs = [d for d in filtered_devs if not d["is_org"]]
    
    print(f"  Org developers: {len(org_devs):,}")
    print(f"  Personal-only: {len(personal_devs):,}")
    
    # Save to CSV
    df = pd.DataFrame(filtered_devs)
    output_file = OUTPUT_DIR / f"filtered_developers_{year}.csv"
    df.to_csv(output_file, index=False)
    print(f"\nSaved: {output_file}")
    
    # Summary stats
    if len(df) > 0:
        print(f"\nCommit distribution:")
        print(f"  Mean: {df['total_commits'].mean():.1f}")
        print(f"  Median: {df['total_commits'].median():.0f}")
        print(f"  P99: {df['total_commits'].quantile(0.99):.0f}")

print("\n" + "="*60)
print("DONE")
print("="*60)
