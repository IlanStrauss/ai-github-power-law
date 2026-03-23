#!/usr/bin/env python3
"""
Fetch GitHub Archive data from BigQuery.

This script runs the SQL queries against GH Archive on BigQuery and saves
the results locally for analysis.

Prerequisites:
    1. Install google-cloud-bigquery: pip install google-cloud-bigquery
    2. Authenticate: gcloud auth application-default login
    3. Set project: gcloud config set project YOUR_PROJECT_ID

Usage:
    python 01_fetch_from_bigquery.py [--sample RATE] [--query QUERY_NAME]

Examples:
    python 01_fetch_from_bigquery.py --sample 0.01  # 1% sample for testing
    python 01_fetch_from_bigquery.py --query yearly_distribution_stats
    python 01_fetch_from_bigquery.py  # Run all queries, full data
"""

import argparse
import os
from pathlib import Path
from datetime import datetime

from google.cloud import bigquery
import pandas as pd


# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
SQL_DIR = PROJECT_ROOT / "sql"
DATA_DIR = PROJECT_ROOT / "data"


# Query configurations
QUERIES = {
    "commits_per_developer": {
        "file": "01_commits_per_developer_yearly.sql",
        "description": "Commits per developer per year (full distribution)",
        "output": "commits_per_developer_yearly.parquet",
    },
    "yearly_distribution_stats": {
        "file": "02_yearly_distribution_stats.sql",
        "description": "Summary statistics by year",
        "output": "yearly_distribution_stats.csv",
    },
    "commits_per_repo": {
        "file": "03_commits_per_repo_yearly.sql",
        "description": "Commits per repository per year",
        "output": "commits_per_repo_yearly.parquet",
    },
    "top_developer_persistence": {
        "file": "04_top_developer_persistence.sql",
        "description": "Year-over-year overlap in top developers",
        "output": "top_developer_persistence.csv",
    },
    "velocity_change": {
        "file": "05_velocity_change_pre_post_copilot.sql",
        "description": "Pre/post Copilot velocity comparison",
        "output": "velocity_change_pre_post.csv",
    },
    "ai_coauthor": {
        "file": "06_ai_coauthor_detection.sql",
        "description": "AI co-author mentions over time",
        "output": "ai_coauthor_trends.csv",
    },
    "repo_concentration": {
        "file": "07_repo_concentration_hhi.sql",
        "description": "Repository concentration (HHI)",
        "output": "repo_concentration_hhi.csv",
    },
}


def add_sampling_to_query(sql: str, sample_rate: float) -> str:
    """Add sampling clause to reduce costs during testing."""
    if sample_rate >= 1.0:
        return sql

    # Insert sampling after the FROM clause
    # This is a simple approach; complex queries may need manual adjustment
    sampling_clause = f"AND RAND() < {sample_rate}"

    # Add before GROUP BY if present
    if "GROUP BY" in sql.upper():
        parts = sql.upper().split("GROUP BY")
        idx = sql.upper().find("GROUP BY")
        return sql[:idx] + f"\n  {sampling_clause}\n" + sql[idx:]
    else:
        return sql + f"\n{sampling_clause}"


def run_query(
    client: bigquery.Client,
    query_name: str,
    sample_rate: float = 1.0,
    dry_run: bool = False,
) -> pd.DataFrame:
    """Run a single query and return results as DataFrame."""
    config = QUERIES[query_name]
    sql_path = SQL_DIR / config["file"]

    print(f"\n{'='*60}")
    print(f"Running: {query_name}")
    print(f"Description: {config['description']}")
    print(f"SQL file: {sql_path}")

    with open(sql_path) as f:
        sql = f.read()

    if sample_rate < 1.0:
        sql = add_sampling_to_query(sql, sample_rate)
        print(f"Sampling rate: {sample_rate*100:.1f}%")

    # Estimate query cost
    job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    dry_run_job = client.query(sql, job_config=job_config)
    bytes_processed = dry_run_job.total_bytes_processed
    estimated_cost = (bytes_processed / 1e12) * 5  # $5 per TB

    print(f"Estimated data: {bytes_processed/1e9:.2f} GB")
    print(f"Estimated cost: ${estimated_cost:.2f}")

    if dry_run:
        print("Dry run - skipping execution")
        return None

    # Execute query
    print("Executing query...")
    start_time = datetime.now()
    df = client.query(sql).to_dataframe()
    elapsed = (datetime.now() - start_time).total_seconds()

    print(f"Completed in {elapsed:.1f}s")
    print(f"Rows returned: {len(df):,}")

    return df


def save_results(df: pd.DataFrame, output_file: str):
    """Save results to appropriate format."""
    output_path = DATA_DIR / output_file

    if output_file.endswith(".parquet"):
        df.to_parquet(output_path, index=False)
    elif output_file.endswith(".csv"):
        df.to_csv(output_path, index=False)
    else:
        raise ValueError(f"Unknown format: {output_file}")

    print(f"Saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Fetch GH Archive data from BigQuery")
    parser.add_argument(
        "--sample",
        type=float,
        default=1.0,
        help="Sampling rate (0.01 = 1%%, 1.0 = full data)",
    )
    parser.add_argument(
        "--query",
        type=str,
        choices=list(QUERIES.keys()) + ["all"],
        default="all",
        help="Which query to run",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Estimate costs without running queries",
    )
    parser.add_argument(
        "--project",
        type=str,
        help="Google Cloud project ID",
    )
    args = parser.parse_args()

    # Initialize BigQuery client
    client_kwargs = {}
    if args.project:
        client_kwargs["project"] = args.project
    client = bigquery.Client(**client_kwargs)

    print(f"BigQuery project: {client.project}")
    print(f"Sample rate: {args.sample*100:.1f}%")
    print(f"Dry run: {args.dry_run}")

    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Run queries
    queries_to_run = list(QUERIES.keys()) if args.query == "all" else [args.query]

    for query_name in queries_to_run:
        try:
            df = run_query(
                client,
                query_name,
                sample_rate=args.sample,
                dry_run=args.dry_run,
            )
            if df is not None:
                save_results(df, QUERIES[query_name]["output"])
        except Exception as e:
            print(f"ERROR running {query_name}: {e}")
            continue

    print("\n" + "=" * 60)
    print("All queries complete!")


if __name__ == "__main__":
    main()
