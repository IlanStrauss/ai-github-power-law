# AI and the Rise of Superstar Coders on GitHub: An Analysis of Commit Data

## 1. Introduction

### Research Question

Is GitHub commit activity becoming more concentrated among fewer developers? Has this concentration accelerated with the rise of AI coding tools (Copilot, Claude Code, Cursor)?

### Motivation

GitHub hosts over 100 million developers and serves as the primary platform for open-source software development. Understanding how commit activity is distributed — and whether this distribution is changing — has implications for:

- **Labor economics:** Productivity concentration may reflect skill premiums or automation displacement
- **Platform governance:** Concentration affects power dynamics in open-source communities
- **AI impact measurement:** If AI tools amplify individual productivity, we should see concentration increasing

### Key Findings

We find a **dramatic increase in commit concentration** from 2019-2024 among multi-repo developers (n=64,406 in 2019; n=131,530 in 2024):

| Metric | 2019 (n=64,406) | 2024 (n=131,530) | Change |
|--------|-----------------|------------------|--------|
| Power Law α | 1.96 | 1.63 | -0.33 |
| Top 1% Share | 45.3% | 63.9% | +18.6pp |
| Gini Coefficient | 0.750 | 0.895 | +0.145 |
| P99/P50 Ratio | 45 | 215 | 4.8x |

**Power law interpretation:** The declining α exponent (1.96 → 1.63) indicates the commit distribution is becoming increasingly heavy-tailed — more activity is concentrated in fewer accounts. An α below 2 implies infinite variance, characteristic of extreme winner-take-all dynamics.

**Robustness:** This concentration increase holds even after filtering to multi-repo developers (those contributing to 2+ repositories), suggesting it reflects genuine behavioral change rather than bot activity.

---

## 2. Data

### 2.1 Source: GH Archive

We use [GH Archive](https://www.gharchive.org/), which records all public GitHub events in real-time since 2011. Each hourly file contains JSON records of every public event on GitHub, including:

- **PushEvents** (commits) — our focus
- WatchEvents (stars)
- ForkEvents
- PullRequestEvents
- IssueEvents

GH Archive is the canonical source for large-scale GitHub research, used by studies in MSR, ICSE, and Empirical Software Engineering.

### 2.2 Sampling Strategy

Processing the full GH Archive is prohibitively expensive (~50TB uncompressed). We use a stratified sample:

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Time of day** | 4 samples (00:00, 06:00, 12:00, 18:00 UTC) | Captures global activity across US, Europe, Asia time zones |
| **Day selection** | 1st of each month | Consistent sampling frame; avoids weekend effects |
| **Years** | 2019-2024 | Pre-AI baseline (2019-2021) through peak AI adoption (2024) |
| **Sample size** | 288 hourly files | ~21GB compressed |

This sampling provides approximately **1/180th** of total GitHub activity while preserving temporal and geographic variation.

**Total sample:** 1,623,706 developer-year observations and 44.1 million commits across 2019-2024.

### 2.3 Data Quality Filters

We apply filters following best practices from the mining software repositories (MSR) literature, particularly Kalliamvakou et al. (2016) "The Promises and Perils of Mining GitHub" and Dey et al. (2020) on bot detection.

#### Filter 1: Event Type (PushEvents Only)

We analyze only PushEvents containing commit data. This excludes:
- Issue comments and PR discussions
- Stars and forks (popularity metrics)
- Administrative events

**Rationale:** Commits are the primary unit of code contribution. Other event types measure engagement, not productivity.

#### Filter 2: Bot Account Exclusion

We exclude accounts matching 15+ bot patterns from the MSR literature:

```
[bot], -bot, dependabot, renovate, github-actions, codecov,
greenkeeper, snyk, imgbot, allcontributors, semantic-release,
pre-commit, mergify, stale, coveralls, travis, circleci
```

**Evidence:** Dey et al. (2020) found bots involved in 31% of all PRs and responsible for 25% of PR accept/reject decisions.

**Note on AI coding bots:** The [Star History Coding AI Leaderboard](https://www.star-history.com/coding-ai-leaderboard) tracks AI-specific accounts (coderabbitai, copilot, cursor, claude, devin, gemini-code-assist). We do not filter these because: (a) they primarily operate via PRs, not direct pushes; (b) if AI tools drive concentration, filtering them would obscure the phenomenon we're measuring.

#### Filter 3: Distinct Commits Only

GH Archive provides two commit counts:
- `size`: Total commits in push (includes merges)
- `distinct_size`: Unique commits (excludes merges)

We use `distinct_size` to avoid merge commit double-counting, which can artificially inflate activity for accounts that frequently merge branches.

#### Filter 4: Minimum Activity Threshold (≥3 commits/year)

We require at least 3 commits per year to be included in the sample.

**Rationale:** Kalliamvakou et al. found 50% of GitHub users have <10 commits total. Including minimally-active accounts inflates the denominator and understates true concentration.

#### Filter 5: Behavioral Ceiling (≤10,000 commits/year)

Accounts exceeding 10,000 commits/year are excluded as likely automation.

**Rationale:** Pattern-matching alone fails for sophisticated automation. In 2024, one account had **2.84 million commits** while passing all bot pattern filters. The 10,000 ceiling catches CI pipelines and enterprise automation that escaped username detection.

#### Filter 6: Multi-Repo Filter (2+ repositories)

Our **primary sample** restricts to accounts contributing to 2+ distinct repositories per year.

**Rationale:** Single-repo accounts (60-63% of all accounts) are predominantly:
- CI/CD automation scripts
- Personal project forks with minimal activity
- Sync bots and auto-update tools
- Enterprise monorepo automation

Multi-repo contributors are more likely to represent human developers working across projects.

**Final analysis sample:** After applying all filters, our primary multi-repo sample contains **625,590 developer-year observations** and **19.3 million commits** across 2019-2024.

### Descriptive Statistics

#### Sample Sizes by Year

| Year | Multi-Repo Accounts | Single-Repo Accounts | Total Accounts | Single-Repo % |
|------|---------------------|----------------------|----------------|---------------|
| 2019 | 64,406 | 102,523 | 166,929 | 61.4% |
| 2020 | 88,765 | 134,000 | 222,765 | 60.2% |
| 2021 | 102,867 | 157,557 | 260,424 | 60.5% |
| 2022 | 113,981 | 180,882 | 294,863 | 61.3% |
| 2023 | 124,041 | 198,435 | 322,476 | 61.5% |
| 2024 | 131,530 | 224,719 | 356,249 | 63.1% |

*Source: GH Archive PushEvents, sampled 1st of each month at 00:00, 06:00, 12:00, 18:00 UTC. Filters applied: bot exclusion, ≥3 commits/year, ≤10,000 commits/year.*

#### Commit Distribution (Multi-Repo Sample)

| Year | Total Commits | Mean | Median | P90 | P99 |
|------|---------------|------|--------|-----|-----|
| 2019 | 1,384,035 | 21.5 | 6 | 23 | 268 |
| 2020 | 1,924,456 | 21.7 | 6 | 22 | 265 |
| 2021 | 2,525,459 | 24.6 | 6 | 22 | 306 |
| 2022 | 2,865,724 | 25.1 | 6 | 22 | 321 |
| 2023 | 3,132,816 | 25.3 | 6 | 21 | 339 |
| 2024 | 7,463,885 | 56.7 | 6 | 25 | 1,287 |

*Source: GH Archive PushEvents (distinct_size only). Multi-repo sample: accounts contributing to 2+ repositories per year.*

**Observation:** The median remains stable at 6 commits/year, while the P99 explodes from 268 to 1,287. This indicates the concentration increase is driven by the upper tail, not a general productivity shift.

#### Concentration Measures (Multi-Repo Sample)

| Year | Accounts | Top 1% Share | Top 10% Share | Gini | P99/P50 |
|------|----------|--------------|---------------|------|---------|
| 2019 | 64,406 | 45.3% | 71.9% | 0.750 | 45 |
| 2020 | 88,765 | 47.8% | 72.2% | 0.753 | 44 |
| 2021 | 102,867 | 52.2% | 75.2% | 0.779 | 51 |
| 2022 | 113,981 | 53.7% | 76.1% | 0.787 | 54 |
| 2023 | 124,041 | 54.6% | 76.9% | 0.792 | 56 |
| 2024 | 131,530 | 63.9% | 89.2% | 0.895 | 215 |

*Source: GH Archive PushEvents. Multi-repo sample (n_repos ≥ 2). Output file: `output/multi_repo_analysis.csv`*

These descriptive measures show increasing concentration, but do not reveal the underlying distributional form. For that, we turn to power law analysis in Section 4.

---

## 3. Methodology

### 3.0 Unit of Analysis

**Our data is aggregated at the developer level.** Each observation represents one developer in one year, with their total commits summed across all repositories they contributed to.

The core question is: **How are commits distributed across developers?**

- Most developers contribute few commits (median = 6/year)
- A small number of "superstar" developers contribute thousands
- The power law exponent α measures how extreme this concentration is

This aggregation is performed via `groupby("actor_login")` in our extraction code, summing all `distinct_size` commits per developer per year.

### 3.1 Power Law Estimation

We follow the Clauset-Shalizi-Newman (2009) methodology, as applied by Strauss, Yang & Mazzucato (2025) to platform earnings distributions:

**Step 1: Threshold Selection**

Determine the minimum value xmin where power law behavior begins using the Kolmogorov-Smirnov (KS) statistic. Below xmin, the distribution may follow a different form (typically log-normal).

**Step 2: Maximum Likelihood Estimation**

Fit the power law exponent α using MLE for the tail above xmin:

$$\hat{\alpha} = 1 + n \left[ \sum_{i=1}^{n} \ln \frac{x_i}{x_{\min}} \right]^{-1}$$

**Step 3: Alternative Distribution Comparison**

Compare power law to log-normal using likelihood ratio test (R statistic):
- R > 0: Power law fits better
- R < 0: Log-normal fits better

This comparison is crucial because many productivity distributions exhibit log-normal bodies with power-law tails (Gabaix, 2016).

### 3.2 Interpreting the α Exponent

The power law exponent α has well-established statistical and economic interpretations:

**Statistical properties (Newman, 2005; Clauset et al., 2009):**
- **α ≤ 2:** Infinite variance — the distribution has no stable mean; dominated by extreme values
- **2 < α ≤ 3:** Finite variance but infinite higher moments
- **α > 3:** All moments finite; distribution approaches "normal" behavior

**Empirical benchmarks from the literature:**

| Domain | Typical α | Source |
|--------|-----------|--------|
| Wealth/Income (top tail) | 1.5–2.0 | Pareto (1896); Gabaix (2009) |
| City sizes | 2.0 | Zipf (1949); Gabaix (1999) |
| Firm sizes | 2.0 | Axtell (2001) |
| Scientific citations | 2.5–3.0 | Redner (1998) |
| Web page visits | 2.0–2.5 | Adamic & Huberman (2000) |

The mechanism generating power laws is typically **preferential attachment** (Simon, 1955; Barabási & Albert, 1999): success begets success, creating "rich-get-richer" dynamics where early advantages compound over time.

A declining α indicates heavier tails — more probability mass concentrated among top performers.

### 3.3 Robustness Checks

1. **Full sample vs. multi-repo:** Compare results with and without single-repo filter
2. **Ceiling sensitivity:** Examine accounts hitting the 10,000-commit cap
3. **AI detection:** Search for explicit AI markers in commit messages

---

## 4. Results

### 4.1 Power Law Estimates

We estimate the power law exponent α for each year using the methodology described in Section 3.1:

| Year | α (exponent) | xmin | R (vs. log-normal) | Best Fit |
|------|--------------|------|--------------------|----------|
| 2019 | 1.96 | 25 | -3.16 | Log-normal |
| 2020 | 1.93 | 34 | -5.64 | Log-normal |
| 2021 | 2.09 | 5 | +6.33 | Power law |
| 2022 | 1.85 | 36 | -6.47 | Log-normal |
| 2023 | 1.82 | 40 | -14.32 | Log-normal |
| **2024** | **1.63** | **30** | **-31.58** | **Log-normal** |

#### Interpretation

**1. Declining α indicates increasing concentration**

The power law exponent dropped from **1.96 (2019) to 1.63 (2024)**. This shift has clear statistical and economic significance:

- In 2019, α ≈ 2 placed GitHub commits in line with classic power law phenomena: city sizes (Gabaix, 1999), firm sizes (Axtell, 2001), and the upper tail of income distributions (Pareto, 1896)
- By 2024, α = 1.63 indicates commit activity has become **more concentrated than typical economic distributions** — comparable to extreme wealth concentration
- An α below 2 implies **infinite variance** (Newman, 2005): the distribution has no stable mean, and is dominated by a few extreme values. This is the statistical signature of winner-take-all dynamics

**2. Log-normal body, power-law tail**

The negative R values indicate log-normal provides a better overall fit than pure power law. This is consistent with Gabaix (2016): productivity distributions typically exhibit log-normal bodies with power-law upper tails. The relevant question is not "is this a power law?" but "how heavy is the tail?" — and the declining α shows the tail is getting heavier.

**3. xmin marks the "superstar threshold"**

The xmin parameter identifies where power law behavior begins — the threshold separating typical developers from the heavy tail. In 2019-2023, xmin ranged from 25-40 commits/year, meaning the power law describes developers with roughly 2-4 commits/month or more. In 2024, xmin = 30 commits/year. Developers above this threshold exhibit the extreme concentration characteristic of power law distributions.

**4. 2024 structural break**

The 2024 α (1.63) represents a **discontinuous shift** from the 2019-2023 range (1.82-2.09). The R value (-31.58) is the most negative, indicating the 2024 distribution deviates significantly from both power law and log-normal — likely due to the explosion in high-volume automated accounts hitting our 10,000-commit ceiling.

### 4.2 Organization vs Personal Developers

We classify developers by whether they contribute to **organization-owned repositories** (Google, Microsoft, Meta, Apache, etc.) — a proxy for professional developers vs hobbyists.

| Year | Org Developers (n) | α | Personal-Only (n) | α |
|------|--------------------|----|-------------------|-----|
| 2019 | 9,824 | 2.04 | 53,945 | 1.99 |
| 2020 | 14,502 | 2.06 | 73,483 | 1.95 |
| 2021 | 18,253 | 2.08 | 83,614 | 1.86 |
| 2022 | 20,764 | 1.91 | 92,200 | 1.83 |
| 2023 | 23,411 | 2.06 | 99,585 | 1.82 |
| 2024 | 25,490 | 2.04 | 102,204 | 1.78 |

*Source: `output/org_developer_analysis.csv`. Org developers = at least 1 commit to an organization repo.*

**Key finding:** The concentration increase is driven by **personal/hobbyist developers**, not professionals:

- **Org developers:** α remains stable at ~2.0 (finite variance, moderate concentration)
- **Personal-only developers:** α declined from 1.99 to 1.78 (infinite variance, extreme concentration)

This suggests the "superstar coder" phenomenon is emerging among individual developers — potentially aided by AI tools that amplify individual productivity — rather than within professional organizations where team structures may distribute work more evenly.

### 4.3 Robustness: Full Sample vs. Multi-Repo

Does the multi-repo filter create the concentration trend artificially?

| Year | Full Sample Top 1% | Multi-Repo Top 1% | Difference |
|------|--------------------|--------------------|------------|
| 2019 | 49.5% | 45.3% | -4.2pp |
| 2020 | 51.3% | 47.8% | -3.5pp |
| 2021 | 54.8% | 52.2% | -2.6pp |
| 2022 | 56.4% | 53.7% | -2.7pp |
| 2023 | 60.2% | 54.6% | -5.6pp |
| 2024 | 68.9% | 63.9% | -5.0pp |

**Finding:** Both samples show the same upward trend. The multi-repo filter reduces concentration by 3-5pp (as expected — single-repo automation inflates the upper tail), but the **trend direction and magnitude are robust**.

#### Power Law α Robustness Across Developer Filters

To ensure our findings reflect human developers rather than automation, we test stricter filters:

| Year | Multi-Repo (n≥2 repos) | Strict (n≥3 repos, ≥10 commits) | Very Strict (n≥4 repos, ≥20 commits) |
|------|------------------------|----------------------------------|---------------------------------------|
| 2019 | 1.96 | 1.96 | 1.93 |
| 2020 | 1.93 | 1.94 | 1.91 |
| 2021 | 2.09 | 1.87 | 1.87 |
| 2022 | 1.85 | 1.81 | 1.80 |
| 2023 | 1.82 | 1.81 | 1.80 |
| 2024 | 1.63 | 1.64 | 1.64 |

*Source: `output/developer_powerlaw_analysis.csv`. Sample sizes: multi-repo n=625,590; strict n=93,964; very strict n=26,606 developer-years.*

**Finding:** The **α decline from ~1.95 to ~1.64 is robust across all developer definitions**. Even among the most active, clearly-human developers (≥4 repos, ≥20 commits/year), concentration is increasing at the same rate.

### 4.4 Automation and Ceiling Effects

#### Extreme Outliers (>10,000 commits/year)

| Year | Accounts >10k | YoY Change |
|------|---------------|------------|
| 2019 | 46 | — |
| 2020 | 73 | +59% |
| 2021 | 79 | +8% |
| 2022 | 131 | +66% |
| 2023 | 175 | +34% |
| **2024** | **1,155** | **+560%** |

**Finding:** The 6.6x explosion in 2024 (175 → 1,155 accounts) indicates a **fundamental shift** in automated commit activity — likely enterprise-scale CI/CD, AI-assisted bulk operations, or new automation patterns.

#### Accounts Hitting the 10,000-Commit Cap

| Year | Accounts at Cap | Accounts ≥9k |
|------|-----------------|--------------|
| 2019 | 0 | 1 |
| 2020 | 0 | 7 |
| 2021 | 0 | 13 |
| 2022 | 0 | 19 |
| 2023 | 1 | 24 |
| **2024** | **180** | **262** |

**Finding:** In 2024, 180 accounts are **capped at 10,000** — their true commit counts could be 50k, 100k, or higher. One account had **2.84 million commits** before filtering. Our concentration metrics for 2024 are therefore **understated**.

### 4.5 AI Detection

#### Explicit AI Markers in Commit Messages

| Year | Total Commits | AI-Attributed | Rate |
|------|---------------|---------------|------|
| 2019 | 1,936,241 | 0 | 0.000% |
| 2020 | 2,803,770 | 0 | 0.000% |
| 2021 | 3,716,022 | 0 | 0.000% |
| 2022 | 4,615,220 | 0 | 0.000% |
| 2023 | 6,259,638 | 50 | 0.001% |
| 2024 | 7,882,625 | 115 | 0.001% |

**Detection patterns used:**
- `aider:` prefix (72 commits in 2024) — Aider tool marker
- `Co-authored-by: Copilot` (23 commits) — GitHub autofix
- `generated by GPT/Claude/Copilot` (18 commits) — explicit attribution
- `AI-generated code` (2 commits) — explicit marker

**Finding:** Only **0.001%** of commits have explicit AI markers, despite industry surveys suggesting 30-50% of developers use AI tools. Reasons include:
- No incentive for disclosure
- Most AI tools don't auto-tag commits
- AI suggestions are edited before commit

**AI and Top Developers:** Only 1 of 1,315 top 1% developers (0.08%) had AI-attributed commits. We **cannot directly measure** AI's contribution to concentration using commit message attribution.

---

## 5. Discussion

### What's Driving Concentration?

The data suggests multiple forces:

1. **Automation scale-up:** The 6.6x explosion in >10k-commit accounts indicates enterprise-scale automation
2. **AI-assisted velocity:** Developers using AI tools may commit more frequently, though explicit markers are rare
3. **Platform effects:** GitHub's network effects may concentrate activity toward established projects
4. **Winner-take-all dynamics:** Top developers may be capturing an increasing share of high-value open-source work

### The Human-AI Measurement Problem

When a developer uses Copilot to write 50% of their code, whose productivity are we measuring? The distinction between "human productivity" and "AI-assisted productivity" is increasingly blurred. This creates fundamental challenges for:

- Labor productivity statistics
- Individual performance evaluation
- Attribution of open-source contributions

Independent analysis by [Star History (2026)](https://www.star-history.com/blog/state-of-coding-ai-on-github) using the same GH Archive data finds AI coding tools now account for **60% of bot PR reviews** (up from 20% at start of 2025) and **9-10% of bot-created PRs**. However, they note these statistics "only capture PRs authored by bot accounts, not AI-written code submitted under human developer names" — confirming that explicit AI attribution is a floor, not a ceiling.

### Limitations

1. **Correlation ≠ causation:** Concentration increases alongside AI adoption, but we cannot establish causality
2. **AI detection:** Most AI usage leaves no trace (<0.002% explicit attribution)
3. **Sampling:** Monthly first-day samples may miss weekly/seasonal patterns
4. **Ceiling effects:** The 10,000-commit cap understates 2024 concentration
5. **Bot detection:** Some automation evades our pattern filters

---

## 6. Project Structure

```
├── scripts/
│   ├── 01a_download_gharchive_direct.py   # Data download
│   ├── 02a_power_law_from_sample.py       # Concentration analysis
│   ├── 03_accurate_ai_detection.py        # AI commit detection
│   ├── 07_robustness_analysis.py          # Multi-repo analysis
│   └── data_extraction.py                 # Quality filters
├── output/
│   ├── multi_repo_analysis.csv            # Main results
│   ├── full_sample_analysis.csv           # Robustness comparison
│   ├── ai_detection_results.csv           # AI commit counts
│   └── outlier_trend.csv                  # Automation trends
└── data/raw/                              # GH Archive files (~21GB)
```

### Replication

```bash
# Install dependencies
pip install pandas numpy matplotlib powerlaw pyarrow

# Download data (~21GB)
python scripts/01a_download_gharchive_direct.py \
    --years 2019-2024 --sample monthly --hours 0,6,12,18

# Run analysis
python scripts/02a_power_law_from_sample.py
```

---

## References

### Power Law Theory and Methods
- Pareto, V. (1896). *Cours d'économie politique*. Lausanne: Rouge.
- Zipf, G. K. (1949). *Human Behavior and the Principle of Least Effort*. Addison-Wesley.
- Simon, H. A. (1955). "On a class of skew distribution functions." *Biometrika*, 42(3/4), 425-440.
- Barabási, A. L., & Albert, R. (1999). "Emergence of scaling in random networks." *Science*, 286(5439), 509-512.
- Newman, M. E. J. (2005). "Power laws, Pareto distributions and Zipf's law." *Contemporary Physics*, 46(5), 323-351.
- Clauset, A., Shalizi, C. R., & Newman, M. E. J. (2009). "Power-law distributions in empirical data." *SIAM Review*, 51(4), 661-703.

### Power Laws in Economics
- Gabaix, X. (1999). "Zipf's law for cities: An explanation." *Quarterly Journal of Economics*, 114(3), 739-767.
- Axtell, R. L. (2001). "Zipf distribution of U.S. firm sizes." *Science*, 293(5536), 1818-1820.
- Gabaix, X. (2009). "Power laws in economics and finance." *Annual Review of Economics*, 1, 255-294.
- Gabaix, X. (2016). "Power laws in economics: An introduction." *Journal of Economic Perspectives*, 30(1), 185-206.

### Web and Citation Networks
- Redner, S. (1998). "How popular is your paper? An empirical study of the citation distribution." *European Physical Journal B*, 4(2), 131-134.
- Adamic, L. A., & Huberman, B. A. (2000). "Power-law distribution of the World Wide Web." *Science*, 287(5461), 2115.

### Platform Economics
- Strauss, I., Yang, J., & Mazzucato, M. (2025). ["'Rich-Get-Richer'? Analyzing Content Creator Earnings Across Large Social Media Platforms."](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5253032) UCL Institute for Innovation and Public Purpose, Working Paper IIPP WP 2025-16.

### GitHub Data Mining
- Kalliamvakou, E., et al. (2016). "An in-depth study of the promises and perils of mining GitHub." *Empirical Software Engineering*, 21(5), 2035-2071.
- Dey, T., et al. (2020). "Detecting and characterizing bots that commit code." *MSR 2020*.

### AI and Productivity
- Ziegler, A., Kalliamvakou, E., et al. (2024). "Measuring GitHub Copilot's Impact on Productivity." *Communications of the ACM*, 67(3).

### Data
- GH Archive: https://www.gharchive.org/
- Python powerlaw package: https://github.com/jeffalstott/powerlaw

---

## License

MIT
