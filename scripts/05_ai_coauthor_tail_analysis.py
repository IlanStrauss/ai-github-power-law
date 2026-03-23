#!/usr/bin/env python3
"""
AI Co-Author Analysis: Correlation with Distribution Tail

This script examines whether developers in the productivity tail (top 1%, 10%)
are more likely to have AI co-author tags in their commits.

AI co-author patterns we search for:
- "Co-authored-by: Claude" (Claude Code)
- "Co-authored-by: GitHub Copilot"
- "(aider)" in author name
- Various AI tool mentions in commit messages

Usage:
    python 05_ai_coauthor_tail_analysis.py
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

# AI detection patterns
AI_PATTERNS = {
    "claude": re.compile(r"(?i)(co-authored-by:\s*claude|anthropic|claude\s*(code|sonnet|opus|haiku))"),
    "copilot": re.compile(r"(?i)(co-authored-by:\s*(github\s*)?copilot|copilot)"),
    "gpt": re.compile(r"(?i)(co-authored-by:\s*(openai|gpt|chatgpt)|openai|gpt-[34])"),
    "cursor": re.compile(r"(?i)cursor"),
    "aider": re.compile(r"(?i)\(aider\)|aider"),
    "codeium": re.compile(r"(?i)codeium"),
    "tabnine": re.compile(r"(?i)tabnine"),
    "ai_generic": re.compile(r"(?i)(generated\s*(by|with|using)\s*(ai|llm)|ai[- ]assisted|ai[- ]generated)"),
}


def extract_with_ai_tags() -> pd.DataFrame:
    """
    Extract commit data with AI co-author detection.

    Returns DataFrame with:
    - date, year
    - actor_login (developer)
    - commits (count)
    - has_ai_coauthor (bool)
    - ai_tool (which tool detected, if any)
    """
    records = []

    files = sorted(RAW_DIR.glob("*.json.gz"))
    if not files:
        raise FileNotFoundError(f"No data files in {RAW_DIR}")

    print(f"Processing {len(files)} files for AI co-author detection...")

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

                    payload = event.get("payload", {})
                    commits_list = payload.get("commits", [])
                    commit_count = payload.get("size", 0)

                    if commit_count == 0:
                        continue

                    # Check all commit messages for AI patterns
                    ai_detected = None
                    for commit in commits_list:
                        message = commit.get("message", "")
                        author_name = commit.get("author", {}).get("name", "")
                        full_text = f"{message} {author_name}"

                        for tool_name, pattern in AI_PATTERNS.items():
                            if pattern.search(full_text):
                                ai_detected = tool_name
                                break
                        if ai_detected:
                            break

                    records.append({
                        "date": date_str,
                        "actor_login": actor,
                        "commits": commit_count,
                        "has_ai": ai_detected is not None,
                        "ai_tool": ai_detected,
                    })

                except json.JSONDecodeError:
                    continue

        print(f"  {filepath.name}: {len(records):,} total records")

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year

    return df


def analyze_ai_by_productivity_tier(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze AI usage rates by productivity tier.

    For each year:
    - Rank developers by total commits
    - Group into tiers (top 1%, top 10%, rest)
    - Calculate AI usage rate in each tier
    """
    results = []

    for year in sorted(df["year"].unique()):
        year_df = df[df["year"] == year]

        # Aggregate by developer
        dev_stats = (
            year_df.groupby("actor_login")
            .agg({
                "commits": "sum",
                "has_ai": "max",  # Did they use AI at least once?
            })
            .reset_index()
        )

        # Rank by commits
        dev_stats["rank"] = dev_stats["commits"].rank(ascending=False, method="min")
        n_devs = len(dev_stats)

        # Define tiers
        dev_stats["tier"] = "rest"
        dev_stats.loc[dev_stats["rank"] <= n_devs * 0.10, "tier"] = "top_10pct"
        dev_stats.loc[dev_stats["rank"] <= n_devs * 0.01, "tier"] = "top_1pct"

        # AI usage by tier
        for tier in ["top_1pct", "top_10pct", "rest"]:
            tier_df = dev_stats[dev_stats["tier"] == tier]
            if len(tier_df) == 0:
                continue

            results.append({
                "year": year,
                "tier": tier,
                "n_developers": len(tier_df),
                "total_commits": tier_df["commits"].sum(),
                "n_with_ai": tier_df["has_ai"].sum(),
                "ai_usage_rate": tier_df["has_ai"].mean(),
                "mean_commits": tier_df["commits"].mean(),
            })

    return pd.DataFrame(results)


def analyze_ai_trends_over_time(df: pd.DataFrame) -> pd.DataFrame:
    """
    Track overall AI co-author mentions over time.
    """
    results = []

    for year in sorted(df["year"].unique()):
        year_df = df[df["year"] == year]

        total_pushes = len(year_df)
        total_commits = year_df["commits"].sum()
        ai_pushes = year_df["has_ai"].sum()

        # By tool
        tool_counts = year_df[year_df["has_ai"]]["ai_tool"].value_counts().to_dict()

        results.append({
            "year": year,
            "total_pushes": total_pushes,
            "total_commits": int(total_commits),
            "ai_pushes": ai_pushes,
            "ai_rate_per_10k": ai_pushes / total_pushes * 10000 if total_pushes > 0 else 0,
            **{f"n_{tool}": tool_counts.get(tool, 0) for tool in AI_PATTERNS.keys()},
        })

    return pd.DataFrame(results)


def plot_ai_analysis(tier_df: pd.DataFrame, trend_df: pd.DataFrame, output_dir: Path):
    """Generate AI co-author analysis plots."""

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Panel A: AI usage rate by tier over time
    ax = axes[0, 0]
    for tier, color in [("top_1pct", "darkred"), ("top_10pct", "darkorange"), ("rest", "steelblue")]:
        tier_data = tier_df[tier_df["tier"] == tier]
        if len(tier_data) > 0:
            ax.plot(tier_data["year"], tier_data["ai_usage_rate"] * 100,
                    marker="o", linewidth=2, color=color, label=tier.replace("_", " ").title())
    ax.axvline(x=2022, color="red", linestyle="--", alpha=0.7)
    ax.set_xlabel("Year")
    ax.set_ylabel("% of Developers with AI Co-author Tags")
    ax.set_title("A. AI Usage Rate by Productivity Tier")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Panel B: Overall AI mentions over time
    ax = axes[0, 1]
    ax.plot(trend_df["year"], trend_df["ai_rate_per_10k"], marker="o", linewidth=2, color="purple")
    ax.axvline(x=2022, color="red", linestyle="--", alpha=0.7, label="Copilot GA")
    ax.set_xlabel("Year")
    ax.set_ylabel("AI Mentions per 10,000 Push Events")
    ax.set_title("B. Overall AI Co-Author Mentions")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Panel C: AI tool breakdown (recent years)
    ax = axes[1, 0]
    recent = trend_df[trend_df["year"] >= 2022]
    tools = ["claude", "copilot", "gpt", "cursor", "aider"]
    x = np.arange(len(recent))
    width = 0.15
    for i, tool in enumerate(tools):
        col = f"n_{tool}"
        if col in recent.columns:
            ax.bar(x + i * width, recent[col], width, label=tool.title())
    ax.set_xticks(x + width * 2)
    ax.set_xticklabels(recent["year"])
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of Pushes")
    ax.set_title("C. AI Tool Mentions by Year")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")

    # Panel D: Relative AI usage (top 1% vs rest)
    ax = axes[1, 1]
    top1 = tier_df[tier_df["tier"] == "top_1pct"].set_index("year")["ai_usage_rate"]
    rest = tier_df[tier_df["tier"] == "rest"].set_index("year")["ai_usage_rate"]
    common_years = sorted(set(top1.index) & set(rest.index))

    if len(common_years) > 0:
        ratio = [top1[y] / rest[y] if rest[y] > 0 else np.nan for y in common_years]
        ax.bar(common_years, ratio, color="darkgreen", alpha=0.7)
        ax.axhline(y=1, color="black", linestyle="--", linewidth=1)
        ax.axvline(x=2022, color="red", linestyle="--", alpha=0.7)
        ax.set_xlabel("Year")
        ax.set_ylabel("Ratio")
        ax.set_title("D. Top 1% vs Rest: AI Usage Rate Ratio\n(>1 = top devs use AI more)")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / "ai_coauthor_analysis.png", dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Saved AI co-author analysis plot")


def main():
    print("=" * 70)
    print("AI CO-AUTHOR ANALYSIS: Correlation with Distribution Tail")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Extract data with AI detection
    print("\nExtracting data with AI co-author detection...")
    df = extract_with_ai_tags()

    print(f"\nTotal push events: {len(df):,}")
    print(f"Events with AI tags: {df['has_ai'].sum():,} ({df['has_ai'].mean()*100:.3f}%)")

    # AI usage by productivity tier
    print("\n" + "-" * 70)
    print("Analyzing AI usage by productivity tier...")
    print("-" * 70)

    tier_df = analyze_ai_by_productivity_tier(df)
    tier_df.to_csv(OUTPUT_DIR / "ai_usage_by_tier.csv", index=False)

    print("\nAI Usage Rate by Tier:")
    pivot = tier_df.pivot(index="year", columns="tier", values="ai_usage_rate")
    if not pivot.empty:
        print((pivot * 100).to_string(float_format=lambda x: f"{x:.3f}%"))

    # AI trends over time
    print("\n" + "-" * 70)
    print("AI co-author trends over time...")
    print("-" * 70)

    trend_df = analyze_ai_trends_over_time(df)
    trend_df.to_csv(OUTPUT_DIR / "ai_coauthor_trends.csv", index=False)

    print("\nAI Mentions by Year:")
    print(trend_df[["year", "total_pushes", "ai_pushes", "ai_rate_per_10k"]].to_string(index=False))

    # Generate plots
    print("\nGenerating plots...")
    plot_ai_analysis(tier_df, trend_df, OUTPUT_DIR)

    # Statistical test: Is AI usage higher in top 1% vs rest?
    print("\n" + "=" * 70)
    print("STATISTICAL TEST: Is AI usage higher in the tail?")
    print("=" * 70)

    for year in sorted(df["year"].unique()):
        if year < 2022:  # AI tools not prevalent before 2022
            continue

        year_tier = tier_df[tier_df["year"] == year]
        top1_row = year_tier[year_tier["tier"] == "top_1pct"]
        rest_row = year_tier[year_tier["tier"] == "rest"]

        if len(top1_row) == 0 or len(rest_row) == 0:
            continue

        top1_n = int(top1_row["n_developers"].values[0])
        top1_ai = int(top1_row["n_with_ai"].values[0])
        rest_n = int(rest_row["n_developers"].values[0])
        rest_ai = int(rest_row["n_with_ai"].values[0])

        # Fisher's exact test
        contingency = [[top1_ai, top1_n - top1_ai], [rest_ai, rest_n - rest_ai]]
        odds_ratio, p_value = stats.fisher_exact(contingency)

        top1_rate = top1_ai / top1_n * 100 if top1_n > 0 else 0
        rest_rate = rest_ai / rest_n * 100 if rest_n > 0 else 0

        print(f"\n{year}:")
        print(f"  Top 1% AI usage:  {top1_ai}/{top1_n} = {top1_rate:.2f}%")
        print(f"  Rest AI usage:    {rest_ai}/{rest_n} = {rest_rate:.3f}%")
        print(f"  Odds ratio:       {odds_ratio:.2f}")
        print(f"  p-value:          {p_value:.4f}")
        if p_value < 0.05:
            print(f"  → Significant difference (p < 0.05)")

    print("\n" + "=" * 70)
    print("INTERPRETATION")
    print("=" * 70)
    print("""
CAVEAT: AI co-author tags massively undercount actual AI usage!
- Most AI-assisted code has NO explicit attribution
- Only Claude Code (and a few tools) add Co-authored-by automatically
- GitHub Copilot does NOT add any attribution
- This analysis captures EXPLICIT mentions only

What we CAN say:
- If top 1% has HIGHER explicit AI usage → they're more likely to use
  tools that add attribution (like Claude Code)
- If rates are similar → no evidence of differential adoption
- If top 1% has LOWER usage → maybe they use Copilot (no attribution)

The trend over time is more interpretable than cross-sectional comparison.
""")


if __name__ == "__main__":
    main()
