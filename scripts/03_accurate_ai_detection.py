#!/usr/bin/env python3
"""
Accurate AI Co-Author Detection
================================
This script uses PRECISE patterns to detect genuine AI tool usage,
avoiding false positives from person names and company domains.

Key insight: Most "Claude", "Copilot", "GPT" mentions are NOISE:
- "Claude Juif" = person's name
- "copilot.llc" = company domain
- "@openai.com" = OpenAI employee, not GPT as author

TRUE AI signals require:
1. Specific email domains (e.g., @anthropic.com)
2. Specific commit message formats (e.g., "aider:" prefix)
3. Known AI tool signature patterns
"""

import gzip
import json
import re
import os
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path("/Users/ilanstrauss/github-analysis/data/raw")
OUTPUT_DIR = Path("/Users/ilanstrauss/github-analysis/output")

# =============================================================================
# PRECISE AI DETECTION PATTERNS
# =============================================================================
# These patterns are designed to minimize false positives

AI_PATTERNS = {
    # AIDER - Most reliable! Uses distinct commit message format
    "aider_commit_prefix": re.compile(r"^aider:", re.MULTILINE | re.IGNORECASE),
    "aider_chat_marker": re.compile(r"# Aider chat conversation:", re.IGNORECASE),

    # CLAUDE CODE / ANTHROPIC - Use email domain
    # Claude Code uses: Co-authored-by: Claude <noreply@anthropic.com>
    # or: Co-authored-by: Claude Sonnet 4 <noreply@anthropic.com>
    "claude_anthropic_email": re.compile(
        r"Co-authored-by:.*<[^>]*@anthropic\.com>", re.IGNORECASE
    ),
    # Also catch "noreply@anthropic.com" without Co-authored-by
    "anthropic_email_any": re.compile(r"@anthropic\.com", re.IGNORECASE),

    # GITHUB COPILOT - Check for specific Copilot signatures
    # Note: GitHub Copilot typically does NOT add co-author signatures
    # This pattern would catch if they do in the future
    "copilot_github_email": re.compile(
        r"Co-authored-by:.*[Cc]opilot.*<[^>]*@github\.com>", re.IGNORECASE
    ),

    # CURSOR - Check for Cursor-specific patterns
    "cursor_ai_marker": re.compile(r"cursor\.sh|cursor-ai|anysphere", re.IGNORECASE),

    # OPENAI/ChatGPT - Must be specific to AI, not employees
    # ChatGPT doesn't typically add signatures, but some wrappers do
    "chatgpt_ai_signature": re.compile(
        r"Co-authored-by:.*ChatGPT|generated.*by.*ChatGPT|ChatGPT.*generated",
        re.IGNORECASE
    ),

    # CODEIUM / OTHER AI TOOLS
    "codeium_marker": re.compile(r"codeium|codewhisperer", re.IGNORECASE),

    # Generic AI-generated markers
    "ai_generated_explicit": re.compile(
        r"(AI[- ]generated|generated[- ]by[- ]AI|AI[- ]assisted)", re.IGNORECASE
    ),
}

# Patterns that are LIKELY FALSE POSITIVES - for filtering
FALSE_POSITIVE_PATTERNS = {
    # Person names (Claude is a common first name)
    "claude_person": re.compile(
        r"Co-authored-by:\s*Claude\s+[A-Z][a-z]+\s*<", re.IGNORECASE
    ),
    # Company domains that aren't AI
    "copilot_company": re.compile(r"copilot\.llc|copilot\.com(?!puter)", re.IGNORECASE),
}


def extract_ai_commits(year: int, verbose: bool = True):
    """Extract all commits with potential AI co-author signatures."""

    year_files = sorted(DATA_DIR.glob(f"{year}-*.json.gz"))

    if not year_files:
        print(f"No files found for {year}")
        return {}

    # Store matches by pattern
    matches_by_pattern = defaultdict(list)

    # Also store false positive examples
    false_positives = defaultdict(list)

    for fpath in year_files:
        if verbose:
            print(f"Processing {fpath.name}...")

        try:
            with gzip.open(fpath, 'rt', encoding='utf-8', errors='replace') as f:
                for line in f:
                    try:
                        event = json.loads(line)
                        if event.get("type") != "PushEvent":
                            continue

                        commits = event.get("payload", {}).get("commits", [])
                        for commit in commits:
                            msg = commit.get("message", "")
                            if not msg:
                                continue

                            # Check each AI pattern
                            for pattern_name, pattern in AI_PATTERNS.items():
                                if pattern.search(msg):
                                    # Check if it's a false positive
                                    is_fp = False
                                    for fp_name, fp_pattern in FALSE_POSITIVE_PATTERNS.items():
                                        if fp_pattern.search(msg):
                                            is_fp = True
                                            if len(false_positives[fp_name]) < 5:
                                                false_positives[fp_name].append({
                                                    "file": fpath.name,
                                                    "actor": event.get("actor", {}).get("login", "unknown"),
                                                    "message": msg[:500],
                                                    "matched_pattern": pattern_name,
                                                })
                                            break

                                    if not is_fp and len(matches_by_pattern[pattern_name]) < 20:
                                        matches_by_pattern[pattern_name].append({
                                            "file": fpath.name,
                                            "actor": event.get("actor", {}).get("login", "unknown"),
                                            "repo": event.get("repo", {}).get("name", "unknown"),
                                            "message": msg[:500],
                                            "sha": commit.get("sha", "")[:8],
                                        })
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"Error processing {fpath}: {e}")
            continue

    return {
        "matches": dict(matches_by_pattern),
        "false_positives": dict(false_positives),
    }


def count_ai_commits_strict(year: int):
    """Get strict counts of AI commits per pattern."""

    year_files = sorted(DATA_DIR.glob(f"{year}-*.json.gz"))

    if not year_files:
        print(f"No files found for {year}")
        return {}

    # Count by pattern (avoid double-counting same commit)
    pattern_counts = defaultdict(int)
    unique_actors = defaultdict(set)

    for fpath in year_files:
        print(f"Counting {fpath.name}...")

        try:
            with gzip.open(fpath, 'rt', encoding='utf-8', errors='replace') as f:
                for line in f:
                    try:
                        event = json.loads(line)
                        if event.get("type") != "PushEvent":
                            continue

                        actor = event.get("actor", {}).get("login", "unknown")
                        commits = event.get("payload", {}).get("commits", [])

                        for commit in commits:
                            if not commit.get("distinct", False):
                                continue

                            msg = commit.get("message", "")
                            if not msg:
                                continue

                            # Check each AI pattern
                            for pattern_name, pattern in AI_PATTERNS.items():
                                if pattern.search(msg):
                                    # Check for false positives
                                    is_fp = any(
                                        fp.search(msg)
                                        for fp in FALSE_POSITIVE_PATTERNS.values()
                                    )

                                    if not is_fp:
                                        pattern_counts[pattern_name] += 1
                                        unique_actors[pattern_name].add(actor)
                                        break  # Count each commit only once
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"Error: {e}")
            continue

    return {
        "counts": dict(pattern_counts),
        "unique_actors": {k: len(v) for k, v in unique_actors.items()},
    }


if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("ACCURATE AI CO-AUTHOR DETECTION")
    print("=" * 60)

    # First, extract examples from 2024 to verify patterns
    print("\n>>> Extracting examples from 2024 for manual verification...")

    results = extract_ai_commits(2024, verbose=True)

    print("\n" + "=" * 60)
    print("VERIFIED AI PATTERN MATCHES (not false positives)")
    print("=" * 60)

    for pattern_name, examples in results["matches"].items():
        print(f"\n--- {pattern_name}: {len(examples)} examples ---")
        for i, ex in enumerate(examples[:3]):
            print(f"\nExample {i+1}:")
            print(f"  Actor: {ex['actor']}")
            print(f"  Repo:  {ex['repo']}")
            print(f"  SHA:   {ex['sha']}")
            print(f"  Message (truncated):")
            # Print first 200 chars of message
            msg_preview = ex['message'][:200].replace('\n', ' | ')
            print(f"    {msg_preview}...")

    print("\n" + "=" * 60)
    print("FALSE POSITIVES FILTERED OUT")
    print("=" * 60)

    for fp_name, examples in results["false_positives"].items():
        print(f"\n--- {fp_name}: {len(examples)} examples ---")
        for i, ex in enumerate(examples[:2]):
            print(f"\nExample {i+1}:")
            print(f"  Actor: {ex['actor']}")
            msg_preview = ex['message'][:150].replace('\n', ' | ')
            print(f"  Message: {msg_preview}...")

    print("\n" + "=" * 60)
    print("GETTING STRICT COUNTS FOR 2024...")
    print("=" * 60)

    counts = count_ai_commits_strict(2024)

    print("\n>>> STRICT AI COMMIT COUNTS (2024) <<<")
    print("-" * 40)
    for pattern, count in sorted(counts["counts"].items(), key=lambda x: -x[1]):
        actors = counts["unique_actors"].get(pattern, 0)
        print(f"{pattern:30s}: {count:5d} commits, {actors:4d} unique actors")

    total = sum(counts["counts"].values())
    print("-" * 40)
    print(f"{'TOTAL':30s}: {total:5d} commits")
