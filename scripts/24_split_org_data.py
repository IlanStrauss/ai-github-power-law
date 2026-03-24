#!/usr/bin/env python3
"""
Split developer data into org vs personal and save separately.
Run this after 23_extract_org_classification.py completes.
"""

import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path("output")

def main():
    print("=" * 70)
    print("SPLITTING AND SAVING ORG VS PERSONAL DEVELOPER DATA")
    print("=" * 70)

    # Load the combined file
    combined_file = OUTPUT_DIR / "all_developers_with_org.parquet"
    if not combined_file.exists():
        print(f"ERROR: {combined_file} not found. Run 23_extract_org_classification.py first.")
        return

    df = pd.read_parquet(combined_file)
    print(f"Loaded {len(df):,} developer-year records")

    # Split
    df_org = df[df["is_org_developer"] == True].copy()
    df_personal = df[df["is_org_developer"] == False].copy()

    print(f"\nOrg developers: {len(df_org):,}")
    print(f"Personal-only:  {len(df_personal):,}")

    # Save split files
    org_file = OUTPUT_DIR / "developers_org_filtered.parquet"
    personal_file = OUTPUT_DIR / "developers_personal_filtered.parquet"

    df_org.to_parquet(org_file, index=False)
    df_personal.to_parquet(personal_file, index=False)

    print(f"\nSaved: {org_file}")
    print(f"Saved: {personal_file}")

    # Also save CSV versions for easy inspection
    df_org.to_csv(OUTPUT_DIR / "developers_org_filtered.csv", index=False)
    df_personal.to_csv(OUTPUT_DIR / "developers_personal_filtered.csv", index=False)

    print(f"Saved: {OUTPUT_DIR / 'developers_org_filtered.csv'}")
    print(f"Saved: {OUTPUT_DIR / 'developers_personal_filtered.csv'}")

    # Summary by year
    print("\n" + "=" * 70)
    print("BREAKDOWN BY YEAR")
    print("=" * 70)

    summary = df.groupby(['year', 'is_org_developer']).size().unstack(fill_value=0)
    summary.columns = ['Personal', 'Org']
    print(summary)

    print("\n✓ Data split and saved successfully")


if __name__ == "__main__":
    main()
