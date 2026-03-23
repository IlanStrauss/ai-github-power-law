#!/usr/bin/env python3
"""
Direct Download from GH Archive.

GH Archive provides hourly JSON files at:
    https://data.gharchive.org/YYYY-MM-DD-H.json.gz

This script downloads data directly — NO BigQuery needed, completely FREE.

Data format:
    - Each file is ~50-200 MB compressed
    - Contains all GitHub events for that hour
    - JSON lines format (one event per line)

Strategy:
    - Download a sample of hours per year (e.g., first day of each month)
    - This gives representative data while keeping download size manageable
    - Full year would be ~3TB; sampling makes it tractable

Usage:
    python 01a_download_gharchive_direct.py --years 2015-2025 --sample monthly
    python 01a_download_gharchive_direct.py --years 2022-2024 --sample weekly
    python 01a_download_gharchive_direct.py --date 2024-01-15  # Single day
"""

import argparse
import gzip
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import Generator, List, Tuple
from urllib.request import urlretrieve, Request, urlopen
from urllib.error import HTTPError
import subprocess

import pandas as pd

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"


def generate_sample_dates(
    start_year: int, end_year: int, sample_strategy: str
) -> Generator[datetime, None, None]:
    """
    Generate sample dates based on strategy.

    Strategies:
        - 'monthly': First day of each month (12 days/year)
        - 'weekly': Every Monday (52 days/year)
        - 'daily': Every day (365 days/year) - WARNING: Large download!
        - 'quarterly': First day of each quarter (4 days/year)
    """
    for year in range(start_year, end_year + 1):
        if sample_strategy == "monthly":
            for month in range(1, 13):
                yield datetime(year, month, 1)

        elif sample_strategy == "weekly":
            # Find first Monday of year
            date = datetime(year, 1, 1)
            while date.weekday() != 0:  # 0 = Monday
                date += timedelta(days=1)
            # Every Monday
            while date.year == year:
                yield date
                date += timedelta(days=7)

        elif sample_strategy == "quarterly":
            for month in [1, 4, 7, 10]:
                yield datetime(year, month, 1)

        elif sample_strategy == "daily":
            date = datetime(year, 1, 1)
            while date.year == year:
                yield date
                date += timedelta(days=1)


def download_hour(date: datetime, hour: int, output_dir: Path) -> Tuple[str, bool, str]:
    """
    Download a single hour's data from GH Archive.

    Returns: (filename, success, message)
    """
    filename = f"{date.strftime('%Y-%m-%d')}-{hour}.json.gz"
    url = f"https://data.gharchive.org/{filename}"
    output_path = output_dir / filename

    if output_path.exists():
        return filename, True, "Already exists"

    try:
        # Use curl for reliable downloads (handles headers properly)
        result = subprocess.run(
            ["curl", "-sL", "-o", str(output_path), url],
            capture_output=True,
            timeout=300
        )
        if result.returncode != 0:
            return filename, False, f"curl error: {result.stderr.decode()}"

        if not output_path.exists():
            return filename, False, "File not created"

        size_mb = output_path.stat().st_size / 1e6
        if size_mb < 0.1:  # Too small, probably an error page
            output_path.unlink()
            return filename, False, "File too small (likely error)"

        return filename, True, f"Downloaded ({size_mb:.1f} MB)"
    except subprocess.TimeoutExpired:
        return filename, False, "Download timeout"
    except Exception as e:
        return filename, False, str(e)


def download_day(date: datetime, output_dir: Path, hours: List[int] = None) -> List[Tuple]:
    """Download all specified hours for a given day."""
    if hours is None:
        hours = list(range(24))  # All 24 hours

    results = []
    for hour in hours:
        result = download_hour(date, hour, output_dir)
        results.append(result)
        print(f"  {result[0]}: {result[2]}")

    return results


def process_gharchive_file(filepath: Path) -> pd.DataFrame:
    """
    Process a single GH Archive file and extract relevant data.

    We extract:
        - PushEvents: For commit analysis
        - WatchEvents: For star analysis
        - CreateEvents: For repo creation
    """
    records = []

    with gzip.open(filepath, "rt", encoding="utf-8") as f:
        for line in f:
            try:
                event = json.loads(line)
                event_type = event.get("type")

                # Only process events we care about
                if event_type not in ("PushEvent", "WatchEvent", "CreateEvent"):
                    continue

                record = {
                    "type": event_type,
                    "created_at": event.get("created_at"),
                    "actor_login": event.get("actor", {}).get("login"),
                    "actor_id": event.get("actor", {}).get("id"),
                    "repo_name": event.get("repo", {}).get("name"),
                    "repo_id": event.get("repo", {}).get("id"),
                }

                # Extract payload details
                payload = event.get("payload", {})

                if event_type == "PushEvent":
                    record["commits_count"] = payload.get("size", 0)
                    record["distinct_commits"] = payload.get("distinct_size", 0)
                    # Check for AI co-author in first commit
                    commits = payload.get("commits", [])
                    if commits:
                        first_msg = commits[0].get("message", "")
                        record["has_ai_coauthor"] = bool(
                            any(
                                kw in first_msg.lower()
                                for kw in ["claude", "copilot", "anthropic", "openai", "gpt"]
                            )
                        )
                    else:
                        record["has_ai_coauthor"] = False

                elif event_type == "WatchEvent":
                    record["action"] = payload.get("action")  # "started" = star

                elif event_type == "CreateEvent":
                    record["ref_type"] = payload.get("ref_type")  # "repository", "branch", "tag"

                records.append(record)

            except json.JSONDecodeError:
                continue

    return pd.DataFrame(records)


def aggregate_daily_stats(df: pd.DataFrame, date: datetime) -> dict:
    """Aggregate statistics for a single day's data."""
    stats = {"date": date.strftime("%Y-%m-%d")}

    # PushEvent stats
    push_df = df[df["type"] == "PushEvent"]
    if len(push_df) > 0:
        stats["total_push_events"] = len(push_df)
        stats["total_commits"] = push_df["commits_count"].sum()
        stats["unique_pushers"] = push_df["actor_login"].nunique()
        stats["unique_repos_pushed"] = push_df["repo_name"].nunique()
        stats["ai_coauthor_pushes"] = push_df["has_ai_coauthor"].sum()

        # Commit distribution per developer
        dev_commits = push_df.groupby("actor_login")["commits_count"].sum()
        stats["median_commits_per_dev"] = dev_commits.median()
        stats["p90_commits_per_dev"] = dev_commits.quantile(0.90)
        stats["p99_commits_per_dev"] = dev_commits.quantile(0.99)
        stats["max_commits_per_dev"] = dev_commits.max()
        stats["top_1pct_share"] = (
            dev_commits.nlargest(max(1, int(len(dev_commits) * 0.01))).sum() / dev_commits.sum()
        )

    # WatchEvent (stars) stats
    watch_df = df[(df["type"] == "WatchEvent") & (df.get("action") == "started")]
    if len(watch_df) > 0:
        stats["total_stars"] = len(watch_df)
        stats["unique_starred_repos"] = watch_df["repo_name"].nunique()

    # CreateEvent stats
    create_df = df[(df["type"] == "CreateEvent") & (df.get("ref_type") == "repository")]
    if len(create_df) > 0:
        stats["repos_created"] = len(create_df)

    return stats


def main():
    parser = argparse.ArgumentParser(description="Download GH Archive data directly")
    parser.add_argument(
        "--years",
        type=str,
        default="2020-2024",
        help="Year range (e.g., '2020-2024' or '2023')",
    )
    parser.add_argument(
        "--sample",
        type=str,
        choices=["monthly", "weekly", "quarterly", "daily"],
        default="monthly",
        help="Sampling strategy",
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Download a specific date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--hours",
        type=str,
        default="0,6,12,18",
        help="Hours to download per day (comma-separated, default: 0,6,12,18)",
    )
    parser.add_argument(
        "--process",
        action="store_true",
        help="Process downloaded files and aggregate stats",
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=4,
        help="Parallel downloads",
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompt",
    )
    args = parser.parse_args()

    # Parse hours
    hours = [int(h) for h in args.hours.split(",")]

    # Create directories
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if args.date:
        # Single date mode
        date = datetime.strptime(args.date, "%Y-%m-%d")
        dates = [date]
    else:
        # Parse year range
        if "-" in args.years:
            start_year, end_year = map(int, args.years.split("-"))
        else:
            start_year = end_year = int(args.years)

        dates = list(generate_sample_dates(start_year, end_year, args.sample))

    # Estimate download size
    n_files = len(dates) * len(hours)
    est_size_gb = n_files * 0.1  # ~100MB per hour on average

    print("=" * 60)
    print("GH Archive Direct Download")
    print("=" * 60)
    print(f"Dates to download: {len(dates)}")
    print(f"Hours per day: {hours}")
    print(f"Total files: {n_files}")
    print(f"Estimated download: ~{est_size_gb:.1f} GB")
    print(f"Output directory: {RAW_DIR}")
    print("=" * 60)

    # Confirm
    if not args.yes:
        response = input("\nProceed with download? [y/N] ")
        if response.lower() != "y":
            print("Aborted.")
            return

    # Download
    print("\nDownloading...")
    for date in dates:
        print(f"\n{date.strftime('%Y-%m-%d')}:")
        download_day(date, RAW_DIR, hours)

    print("\n" + "=" * 60)
    print("Download complete!")
    print("=" * 60)

    # Process if requested
    if args.process:
        print("\nProcessing downloaded files...")
        all_stats = []

        for date in dates:
            day_dfs = []
            for hour in hours:
                filename = f"{date.strftime('%Y-%m-%d')}-{hour}.json.gz"
                filepath = RAW_DIR / filename
                if filepath.exists():
                    print(f"  Processing {filename}...")
                    df = process_gharchive_file(filepath)
                    day_dfs.append(df)

            if day_dfs:
                day_df = pd.concat(day_dfs, ignore_index=True)
                stats = aggregate_daily_stats(day_df, date)
                all_stats.append(stats)

        # Save aggregated stats
        stats_df = pd.DataFrame(all_stats)
        stats_df["date"] = pd.to_datetime(stats_df["date"])
        stats_df["year"] = stats_df["date"].dt.year

        output_path = DATA_DIR / "daily_stats_sample.csv"
        stats_df.to_csv(output_path, index=False)
        print(f"\nSaved daily stats to: {output_path}")

        # Aggregate to yearly
        yearly = (
            stats_df.groupby("year")
            .agg(
                {
                    "total_commits": "sum",
                    "unique_pushers": "sum",  # Note: overcounts across days
                    "ai_coauthor_pushes": "sum",
                    "top_1pct_share": "mean",
                    "median_commits_per_dev": "mean",
                    "p99_commits_per_dev": "mean",
                }
            )
            .reset_index()
        )

        yearly_path = DATA_DIR / "yearly_stats_sample.csv"
        yearly.to_csv(yearly_path, index=False)
        print(f"Saved yearly stats to: {yearly_path}")


if __name__ == "__main__":
    main()
