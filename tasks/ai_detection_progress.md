# AI Detection Progress - SAVE STATE

## Problem
Most AI tool mentions in commit messages are FALSE POSITIVES:
- "Claude Juif" = person's name, not Claude AI
- "copilot.llc" = company domain, not GitHub Copilot
- "@openai.com" = OpenAI employee, not GPT

## What We Found (2024 data, strict patterns)

| Pattern | Commits | Unique Actors |
|---------|---------|---------------|
| aider_commit_prefix | 75 | 10 |
| codeium_marker | 49 | 33 |
| ai_generated_explicit | 33 | 29 |
| chatgpt_ai_signature | 7 | 6 |
| claude_anthropic_email | 2 | 2 |
| cursor_ai_marker | 1 | 1 |
| **TOTAL** | **167** | |

## Key Insight
Most AI tools do NOT add co-author signatures:
- GitHub Copilot: Never adds signatures
- Cursor: Never adds signatures
- ChatGPT: Never adds signatures
- Only **Aider** reliably marks commits with `aider:` prefix

## Scripts Created

1. `scripts/03_accurate_ai_detection.py` - Strict pattern matching
2. `scripts/04_smart_ai_regex.py` - Word boundary + context patterns (running)

## Next Steps

1. Wait for `04_smart_ai_regex.py` to finish (background task bbbbdb3)
2. Manually review examples to validate patterns
3. Run across all years (2019-2024)
4. Link AI usage to concentration analysis

## Current Background Tasks
- bbbbdb3: Smart regex detection (running)
- bbd5be0: Search all years for AI signatures (completed)

## The Core Finding
**AI co-author detection is severely limited** - only ~167 attributable AI commits in 2024 sample.
This is a LOWER BOUND. Most AI-assisted code has NO attribution.
