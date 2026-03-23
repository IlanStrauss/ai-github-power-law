# GitHub Data Mining: Methodology Best Practices

This document summarizes best practices from academic literature for mining GitHub data, particularly from GH Archive.

## Primary References

1. **Kalliamvakou et al. (2014/2016)** - "The Promises and Perils of Mining GitHub"
   - MSR 2014, extended in Empirical Software Engineering 2016
   - https://link.springer.com/article/10.1007/s10664-015-9393-5
   - Key contribution: Identified 6 major perils in GitHub data mining

2. **Dey et al. (2020)** - "Detecting and Characterizing Bots that Commit Code"
   - MSR 2020
   - https://cmustrudel.github.io/papers/msr20bots.pdf
   - Key contribution: Bot detection patterns and prevalence estimates

3. **Golzadeh et al. (2021)** - "A ground-truth dataset and classification model for detecting bots"
   - Journal of Systems and Software
   - https://sciencedirect.com/science/article/pii/S016412122100008X
   - Key contribution: ~20% of PR comments are from bots

4. **Ziegler, Kalliamvakou et al. (2024)** - "Measuring GitHub Copilot's Impact on Productivity"
   - Communications of the ACM, March 2024
   - https://dl.acm.org/doi/10.1145/3633453
   - Key findings: 55% faster task completion with Copilot, 90%+ report productivity gains

---

## Key Perils (Kalliamvakou et al.)

### Peril 1: Repository != Project
- **Finding:** 44% of public repos are forks, not independent projects
- **Implication:** Counting repos overestimates project count
- **Mitigation:** Filter forks or analyze fork networks together

### Peril 2: Most Projects Have Few Commits
- **Finding:** 50% of users have <10 commits total; only 10% have >50
- **Implication:** Distribution is extremely skewed
- **Mitigation:** Apply minimum activity threshold (we use MIN_COMMITS=3)

### Peril 3: Most Projects Are Inactive
- **Finding:** Only 54% of projects were active in last 6 months
- **Implication:** Many repos are abandoned
- **Mitigation:** Focus on recent activity windows

### Peril 4: Not All Repos Are Software
- **Finding:** Many repos are for data storage, documentation, personal websites
- **Implication:** Mining "code" may include non-code
- **Mitigation:** Filter by file types or activity patterns

### Peril 5: Most Projects Are Personal
- **Finding:** 71.6% of repositories are personal (not organizational)
- **Implication:** Professional software development is minority
- **Mitigation:** Filter for org repos when studying professional practices

### Peril 6: Many Committers Are Not GitHub Users
- **Finding:** 23% of commit authors are not registered GitHub users
- **Implication:** Attribution can be inconsistent
- **Mitigation:** Use `actor.login` (pusher) rather than commit author

---

## Bot Filtering

### Two-Layer Bot Detection

**Layer 1: Username Pattern Matching**
From MSR literature, filter accounts matching these patterns:

```python
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
```

**Layer 2: Behavioral Filter**
Pattern matching alone can fail (e.g., 2024's 2.84M commit account survived patterns).
Apply behavioral ceiling:

```python
MAX_COMMITS_PER_YEAR = 10000  # Accounts exceeding this are excluded
```

Any account exceeding 10,000 commits/year should be manually inspected or excluded.
This catches automation/CI pipelines that escaped username pattern matching.

### Bot Prevalence
- ~20% of PR comments are from bots (Golzadeh et al.)
- Bots involved in 31% of all PRs
- Bots responsible for 25% of PR accept/reject decisions

---

## Commit Quality Filtering

### Low-Quality Commit Messages
Filter commits with these patterns:

```python
LOW_QUALITY_PATTERNS = [
    # Empty/placeholder
    r"^\.+$",                           # Just dots
    r"^-+$",                            # Just dashes
    r"^[a-z]$",                         # Single letter
    r"^(asdf|asd|foo|bar|baz)$",

    # Generic/meaningless
    r"^(test|testing|wip|tmp|temp)\.?$",
    r"^(fix|update|changes?)\.?$",
    r"^(empty|blank|placeholder|todo)\.?\s*(commit)?$",
    r"^(initial|first|start|new)\.?\s*(commit)?$",
    r"^commit\s*\d*$",
    r"^save\s*(work|progress)?$",

    # Merge commits (inflation source)
    r"^merge\s+(branch|pull|remote)",
    r"^Merge pull request #\d+",
]
```

### Distinct vs Total Commits
- GH Archive provides both `size` (total) and `distinct_size` (non-merge)
- Use `distinct_size` to filter merge commit inflation
- Merge commits can artificially inflate activity metrics

---

## Org vs Personal Repos

### Identifying Organizations
Known major organizations (partial list):

```python
MAJOR_ORGS = {
    # Tech giants
    "google", "microsoft", "facebook", "meta", "amazon", "aws", "apple",
    "netflix", "uber", "airbnb", "stripe", "shopify",

    # Open source foundations
    "apache", "kubernetes", "docker", "hashicorp", "cncf",

    # AI/ML
    "openai", "anthropic", "huggingface", "pytorch", "tensorflow",

    # Languages/Frameworks
    "rust-lang", "golang", "python", "nodejs", "vuejs", "angular",
}
```

### Heuristics for Org Detection
1. Match against known org list
2. Check for org-like name patterns: `-team`, `-org`, `-io`, `-labs`
3. Exclude `username/username` pattern (likely personal)

---

## Sample Selection Recommendations

### Minimum Activity Threshold
- **Recommendation:** Require >= 3 commits per year
- **Rationale:** Filters inactive/casual accounts (50% have <10 total)
- **Effect:** Removes "denominator inflation" from concentration metrics

### Stratified Sampling
- Use stratified sampling by year, activity level, or repo type
- Avoids bias toward certain project types or time periods

### Time Windows
- GH Archive available from 2011 (Timeline API) and 2015 (Events API)
- Data quality improved significantly after 2015
- Consider analyzing pre/post specific events (e.g., Copilot launch 2022)

---

## GH Archive Specifics

### Event Types Available
- PushEvent (commits)
- WatchEvent (stars)
- ForkEvent (forks)
- PullRequestEvent
- IssueEvent
- CreateEvent, DeleteEvent
- And more...

### Data Quality Notes
- BigQuery copy may have duplicated/missing rows
- **Snowflake copy appears more reliable** - available as Marketplace dataset, gives SQL access to full dataset
- Direct download from gharchive.org most reliable but requires sampling for tractability

### External Validation Sources
For sanity checking concentration metrics:
- **OSS Insight** (ossinsight.io) - Pre-processed GitHub analytics, may handle bot filtering differently
- **DevStats** (CNCF's tool) - CNCF project analytics
- Compare findings against these as robustness check

### Sampling Strategy
For cost-effective analysis:
- 4 hours per day (00:00, 06:00, 12:00, 18:00 UTC) captures global activity
- 1-2 days per month captures monthly variation
- This provides ~1/180th to ~1/90th sample of full data

---

## Our Implementation

### Filters Applied (data_extraction.py)
1. **Bot accounts:** Pattern matching on username
2. **Low-quality commits:** Pattern matching on commit messages
3. **Merge commits:** Use `distinct_size` instead of `size`
4. **Inactive accounts:** MIN_COMMITS = 3 per year

### Metrics Tracked
- Total commits vs distinct commits
- High-quality vs low-quality commit ratio
- Org repo vs personal repo
- Repo diversity (n_repos per developer)

### Robustness Checks
- Sensitivity to outlier removal (top K accounts)
- Sensitivity to activity threshold (min commits)
- Fixed-rank analysis (denominator-insensitive)
- Quality-filtered concentration metrics

### Monorepo Robustness Check
Flag contributors whose commits are overwhelmingly concentrated in a single repo:

```python
# Accounts with 95%+ commits in their top repo
monorepo_accounts = df[df["top_repo_share"] >= 0.95]
```

These are qualitatively different from productive developers spread across projects:
- May indicate monorepo automation
- CI pipelines that survived bot filtering
- Single-project focused work (legitimate but different phenomenon)

Analysis should report results both with and without monorepo accounts.

---

## Citation

If using these best practices, cite:

```bibtex
@article{kalliamvakou2016promises,
  title={An in-depth study of the promises and perils of mining GitHub},
  author={Kalliamvakou, Eirini and Gousios, Georgios and Blincoe, Kelly and Singer, Leif and German, Daniel M and Damian, Daniela},
  journal={Empirical Software Engineering},
  volume={21},
  pages={2035--2071},
  year={2016},
  publisher={Springer}
}

@inproceedings{dey2020detecting,
  title={Detecting and characterizing bots that commit code},
  author={Dey, Tapajit and Mousavi, Sara and Ponce, Eduardo and Fry, Tanner and Vasilescu, Bogdan and Filippova, Anna and Mockus, Audris},
  booktitle={Proceedings of the 17th International Conference on Mining Software Repositories},
  pages={209--219},
  year={2020}
}
```
