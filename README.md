# The Rise of Superstar Coders on GitHub: An analysis of commit data*

## 1. Introduction

**What is a commit?** A *commit* is a saved change to a code repository — the fundamental unit of developer contribution on GitHub. Each commit represents work: fixing a bug, adding a feature, or updating documentation. Developers with more commits contribute more code.

### Research Question

*Is GitHub commit activity becoming more concentrated among fewer developers? Has this concentration accelerated with the rise of AI coding tools (Copilot, Claude Code, Cursor)?*

**Short answer: Yes, with different timing across groups.** Concentration among personal developers increased sharply during 2020-2022. Org developers saw slow concentration growth through 2024, then sharp acceleration in 2025. The timing patterns are *consistent with* differential adoption of productivity tools, though we cannot establish causation. We assess this using power law analysis of commit distributions across 2019-2025 (through October 31).

### Motivation

GitHub hosts over 100 million developers and serves as the primary platform for open-source software development. Understanding how commit activity is distributed — and whether this distribution is changing — has implications for:

- **AI impact measurement:** If AI tools amplify individual productivity, we should see concentration increasing
- **Labor economics:** Productivity concentration may reflect skill premiums or automation displacement
- **Institutional economics:** We can understand the role of institutions and work processes in mediating how AI is used and impacts worker productivity
- **Platform governance:** Concentration affects power dynamics in open-source communities

### Key Findings

**The rise of superstar coders happened in two waves — and these superstars are becoming *more* persistent over time, not less.**

We analyze GitHub commit concentration from 2019-2025 (through October 31) among multi-repo developers. The power law exponent α measures concentration: **lower α = more concentration** (see Section 3 for interpretation).

| Developer Type | α (2019) | α (2024) | α (2025*) | Δα (2019→2025) | Interpretation |
|:--------------:|:--------:|:--------:|:--------:|:--------------:|:--------------:|
| **Personal-only** | 1.99 | 1.78 | 1.80 | −0.19 | Rose early (COVID then AI), now stable |
| **Org developers** | 2.04 | 2.04 | 1.87 | −0.17 | Slow decline, then sharp 2025 acceleration |

*\*2025 data covers January–October only. GitHub's Events API removed commit details from PushEvent payloads on October 7, 2025; GH Archive data after this date lacks commit counts. See Data Caveats.*

*Notes: "Personal-only" = zero commits to org repos. "Org developers" = at least one commit to a public org repo (Google, Microsoft, Apache, etc.). α estimated via Clauset-Shalizi-Newman (2009). Source: `output/powerlaw_2025.csv`, `output/powerlaw_lognormal_comparison.csv`.*

**Two distinct phases:**

*Phase 1 (2020-2024): Concentration rises among personal developers — COVID, then AI.*
- Personal α dropped from 1.99 → 1.78 (crossed into "infinite variance" regime)
- Sharpest drop was 2020-2021 (α: 1.95 → 1.86), during COVID — *before* Copilot launched (June 2022)
- COVID created favorable conditions (increased free time, remote work, coding education boom)
- When AI tools arrived (Copilot, June 2022), personal developers adopted them quickly — **minimal adoption lag** among individuals who self-select into new tools
- Org developers saw slow concentration growth through this period

*Phase 2 (2025): Concentration sharply accelerates among org developers — AI clears enterprise hurdles.*
- Personal α stabilized at 1.80 (already heavily concentrated from Phase 1)
- **Org α dropped from 2.04 → 1.87** — slow decline through 2024, then sharp acceleration in 2025
- This coincides with enterprise AI coding tools reaching production-readiness: Claude Code (Feb 2025), Codex (May 2025)
- Professional settings experienced **longer adoption lag**: security reviews, procurement cycles, and code review processes delayed AI tool adoption by ~2-3 years compared to individuals

**What does this mean?**

Remember: **lower α = more concentration.** A declining α means extreme values (superstars) are becoming more common relative to typical developers.

- *Personal developers:* Concentration increased sharply 2020-2021, then continued through 2024. By 2024-2025, concentration had stabilized at high levels.

- *Org developers:* Concentration was flat through 2024, then sharply accelerated in 2025. This timing coincides with enterprise AI coding tools reaching production readiness.

**The adoption lag hypothesis:** The timing pattern — personal developers concentrating first (2020-2022), org developers later (2025) — is *consistent with* differential adoption speeds. Individuals face fewer barriers to new tool adoption than organizations, which must navigate procurement, security reviews, and workflow integration. The ~2-3 year gap aligns with typical enterprise technology adoption cycles, though we cannot rule out alternative explanations.

**Superstars are becoming more persistent:** Contrary to a "rotating superstars" hypothesis, top-1% persistence *increased* in the post-2022 period. Among org developers, persistence rose from 29.6% (pre-2022 average) to 37.3% (post-2022 average) — a +7.7 pp increase. Among personal developers, persistence rose from 27.1% to 30.4% (+3.3 pp). This pattern is *consistent with* the same developers pulling further ahead each year, though we cannot establish causation. One interpretation is that productivity tools amplify advantages for those who already excel.

**Concentration appears driven by extremes:** Counterfactual analysis shows only 7.7% of the α decline persists after excluding the top 5% of accounts. This is consistent with concentration reflecting a small number of developers with extreme output, rather than a broad distributional shift.

**Caveat:** GH Archive contains only **public repositories**. Private organization repos (where most enterprise development occurs) are not captured. Our "org developers" are those contributing to *public* org repos (open-source foundations, public company projects).

**Pooled sample:** Looking at all developers combined, α declined from 1.96 to 1.63, with Top 1% share rising from 45.3% to 63.9%. See Section 4 and Appendix for details.

---

## 2. Data

### 2.0 Unit of Analysis

Our data is aggregated at the **developer level**. Each observation represents one developer in one year, with their total commits summed across all repositories they contributed to. The core question is: *How are commits distributed across developers?*

- Most developers contribute few commits (median = 6/year)
- A small number of "superstar" developers contribute thousands
- The power law exponent α measures how extreme this concentration is

This aggregation is performed via `groupby("actor_login")` in our extraction code, summing all `distinct_size` commits per developer per year.

**Are commits a good measure of productivity?** No, but they're often the best available proxy. Commits are observable, objective (no self-reporting bias), universally available at scale, and temporally precise. However, commit counts have significant limitations: "commit early, commit often" culture inflates counts, squash merges collapse many commits into one, size variance is enormous (a typo fix and a 10,000-line refactor both count as one commit), invisible work (code review, mentoring) doesn't appear, and quality is absent entirely. For this research, we're not measuring individual productivity — we're measuring distributional shifts across millions of developers. Commits work for this purpose because systematic biases are consistent over time, so changes in the distribution likely reflect real behavioral changes. The unit of analysis is the population, not the person.

### 2.1 Source: GH Archive

We use [GH Archive](https://www.gharchive.org/), which records all public GitHub events in real-time since 2011. Each hourly file contains JSON records of every public event on GitHub, including:

- **PushEvents** (commits) — our focus
- WatchEvents (stars)
- ForkEvents
- PullRequestEvents
- IssueEvents

GH Archive is the canonical source for large-scale GitHub research, used by studies in MSR, ICSE, and Empirical Software Engineering.

#### GH Archive Data Caveats

Commit data is captured via **PushEvent** records in the payload:

**What you get:**
- An array of commit objects describing the pushed commits, including the SHA, commit message, git author name/email, and a URL to the commit API resource
- `push_size` and `push_distinct_size` fields on the PushEvent, giving you the total and distinct commit counts for the push

**The 20-commit cap:** The commits array includes a maximum of 20 commits per push. Any commits above this limit are missing from the dataset. Most PushEvents don't hit this limit (~99%), but initial pushes (e.g., a private repo moving to GitHub) can have very high commit counts that get truncated.

**Other caveats:**
- There are times when the GH Archive crawler goes offline or hits the API rate limit and misses events; backfilling these gaps is outside the project's scope
- Commit *dates* are not directly available — you only have the push date as a proxy

#### Schema Break: October 7, 2025 — Data Ends Here

GitHub [announced](https://github.blog/changelog/2025-08-08-upcoming-changes-to-github-events-api-payloads/) in August 2025 that the Activity Events API would trim push payloads by removing "commit summaries and counts," with rollout on **October 7, 2025**.

**What changed:**
- The Events API docs for `PushEvent` now list only `repository_id`, `push_id`, `ref`, `head`, and `before`
- `commits`, `size`, and `distinct_size` are **no longer part of the payload**
- GH Archive records GitHub's Events API verbatim, so GH Archive inherited this change

**Impact on this analysis:**
- **Our 2025 data covers January 1 – October 31 only** (10 months)
- All 2025 figures, sample sizes, and comparisons reflect this truncated year
- November 2025 onward cannot be analyzed using commit-based metrics from GH Archive

*Note: GitHub webhooks still include the full `commits` array — this is specifically an Events API / GH Archive limitation, not a universal GitHub change.*

For most use cases (counting commits per repo/user over time), the data is quite usable, but it's not a perfect 100% complete record of every commit ever made.

### 2.2 Sampling Strategy

Processing the full GH Archive is prohibitively expensive (~50TB uncompressed). We use a stratified sample:

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Time of day** | 4 samples (00:00, 06:00, 12:00, 18:00 UTC) | Captures global activity across US, Europe, Asia time zones |
| **Day selection** | 1st of each month | Consistent sampling frame; avoids weekend effects |
| **Years** | 2019-2025 | Pre-AI baseline (2019-2021) through AI adoption (2024-2025) |
| **Sample size** | 328 hourly files | ~25GB compressed |

This sampling provides approximately **1/180th** of total GitHub activity while preserving temporal and geographic variation.

**Total sample:** ~1.7 million developer-year observations and ~58 million commits across 2019-2025.

**Data cutoff: October 31, 2025.** GitHub's Events API [removed commit details](https://github.blog/changelog/2025-08-08-upcoming-changes-to-github-events-api-payloads/) from PushEvent payloads on October 7, 2025. GH Archive inherited this change, so **our 2025 data covers January 1 – October 31 only**. All 2025 figures in this analysis reflect 10 months of data.

### 2.3 Data Quality Filters

We apply filters following best practices from the mining software repositories (MSR) literature, particularly Kalliamvakou et al. (2016) "The Promises and Perils of Mining GitHub" and Dey et al. (2020) on bot detection.

*Filter 1: Event Type (PushEvents Only).* We analyze only PushEvents containing commit data. This excludes:
- Issue comments and PR discussions
- Stars and forks (popularity metrics)
- Administrative events

*Rationale:* Commits are the primary unit of code contribution. Other event types measure engagement, not productivity.

*Filter 2: Bot Account Exclusion.* We exclude accounts matching 15+ bot patterns from the MSR literature:

```
[bot], -bot, dependabot, renovate, github-actions, codecov,
greenkeeper, snyk, imgbot, allcontributors, semantic-release,
pre-commit, mergify, stale, coveralls, travis, circleci
```

*Evidence:* Dey et al. (2020) found bots involved in 31% of all PRs and responsible for 25% of PR accept/reject decisions.

*Note on AI coding bots:* The [Star History Coding AI Leaderboard](https://www.star-history.com/coding-ai-leaderboard) tracks AI-specific accounts (coderabbitai, copilot, cursor, claude, devin, gemini-code-assist). We do not filter these because: (a) they primarily operate via PRs, not direct pushes; (b) if AI tools drive concentration, filtering them would obscure the phenomenon we're measuring.

*Filter 3: Distinct Commits Only.* GH Archive provides two commit counts:
- `size`: Total commits in push (includes merges)
- `distinct_size`: Unique commits (excludes merges)

We use `distinct_size` to avoid merge commit double-counting, which can artificially inflate activity for accounts that frequently merge branches.

*Filter 4: Minimum Activity Threshold (≥3 commits/year).* We require at least 3 commits per year to be included in the sample.

*Rationale:* Kalliamvakou et al. found 50% of GitHub users have <10 commits total. Including minimally-active accounts inflates the denominator and understates true concentration.

*Filter 5: Behavioral Ceiling (≤10,000 commits/year).* Accounts exceeding 10,000 commits/year are excluded as likely automation.

*Rationale:* Pattern-matching alone fails for sophisticated automation. In 2024, one account had **2.84 million commits** while passing all bot pattern filters. The 10,000 ceiling catches CI pipelines and enterprise automation that escaped username detection.

*Filter 6: Multi-Repo Filter (2+ repositories).* Our primary sample restricts to accounts contributing to 2+ distinct repositories per year.

*Rationale:* Single-repo accounts (60-63% of all accounts) are predominantly:
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
| 2025 | 89,456 | — | — | — |

*2025 data: January–October only (10 months). Single-repo breakdown not available for 2025 extraction.*

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
| 2025 | 2,180,740 | 24.4 | 5 | 18 | 295 |

*2025 data: January–October only (10 months).*

*Source: GH Archive PushEvents (distinct_size only). Multi-repo sample: accounts contributing to 2+ repositories per year.*

The median remains stable at 6 commits/year, while the P99 increases sharply from 268 to 1,287. This pattern is consistent with the concentration increase being driven by the upper tail, not a general productivity shift. For detailed concentration measures (Gini, Top 1% share, etc.), see Appendix.

#### Organization vs Personal Developers

We classify developers into two groups based on whether they contribute to organization-owned repositories:

**Classification criteria:**
- **Org developers:** At least one commit to a repository owned by a known organization account. We identify org accounts via: (1) a curated list of 70+ major organizations (Google, Microsoft, Meta, Apache, Mozilla, etc.); (2) heuristic patterns for org-like names (e.g., suffixes like `-inc`, `-io`, `-labs`, `-foundation`).
- **Personal-only developers:** Zero commits to any organization-owned repository — all commits go to personal/individual accounts.

This classification proxies for professional developers (who often contribute to public org repos) vs hobbyists/individuals (who work only on personal projects).

| Year | Org Developers | Personal-Only | Org % of Sample |
|------|----------------|---------------|-----------------|
| 2019 | 9,824 | 53,945 | 15.4% |
| 2020 | 14,502 | 73,483 | 16.5% |
| 2021 | 18,253 | 83,614 | 17.9% |
| 2022 | 20,764 | 92,200 | 18.4% |
| 2023 | 23,411 | 99,585 | 19.0% |
| 2024 | 25,490 | 102,204 | 20.0% |
| 2025 | 18,285 | 71,171 | 20.4% |

*2025 data: January–October only (10 months). Lower absolute counts reflect truncated year.*

*Source: `output/org_developer_analysis.csv`, `output/filtered_developers_2025.csv`.*

**Caveat:** GH Archive contains only **public repositories**. Private organization repos (where most enterprise development occurs) are not captured. Our "org developers" are those contributing to *public* organization repos (open-source foundations, public company projects like tensorflow, kubernetes, etc.).

These descriptive measures show increasing concentration, but do not reveal the underlying distributional form. For that, we turn to power law analysis in Section 4.

---

## 3. Method: Power Law Estimation

### 3.1 The Power Law Distribution

A power law distribution describes the probability of observing a value x:

$$P(x) \propto x^{-\alpha}$$

where α (alpha) is the **power law exponent**. This equation says the probability of observing x decreases as x increases, but the rate of decrease is controlled by α.

**Why power laws matter for understanding system dynamics:**

Power laws emerge from specific generative processes — most commonly **preferential attachment** ("rich-get-richer"). When success breeds more success (popular repos attract more contributors, productive developers get more visibility), the resulting distribution follows a power law. The exponent α tells us *how strong* this compounding effect is:

- **Lower α → stronger compounding.** Extreme values (superstars) become increasingly likely. Early advantages snowball into massive gaps.
- **Higher α → weaker compounding.** The distribution is more compressed. Success still begets success, but advantages don't compound as dramatically.

A *declining* α over time signals that the system's dynamics are becoming more winner-take-all. This is why tracking α year-over-year reveals whether concentration is increasing.

**Contrast with normal distributions:** In a normal (Gaussian) distribution, extreme values are exponentially rare — 6-sigma events are essentially impossible. In a power law, extreme values are merely *polynomially* rare — they're uncommon but not impossible. This is why GitHub can have developers with 10,000+ commits while the median is 6.

### 3.2 Estimation Method

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

### 3.3 Interpreting α

- **High α (e.g., 2.5-3.0):** The tail falls off quickly. Top performers exist but don't dominate.
- **Low α (e.g., 1.5-1.8):** The tail is "fat" — extreme values are common. A small number of superstars capture most of the activity.
- **α declining over time:** The system is becoming more winner-take-all.

In our data, personal developers' α fell from 1.99 (2019) to 1.78 (2024) — extreme commit counts became more common.

**Statistical properties (Newman, 2005; Clauset et al., 2009):**
- **α ≤ 2:** Infinite variance — the distribution has no stable mean; dominated by extreme values
- **2 < α ≤ 3:** Finite variance but infinite higher moments
- **α > 3:** All moments finite; distribution approaches "normal" behavior

*Empirical benchmarks.* Power law exponents vary systematically across domains. Wealth and income distributions in the top tail typically exhibit α between 1.5 and 2.0 (Pareto, 1896; Gabaix, 2009). City sizes and firm sizes cluster around α ≈ 2.0 (Zipf, 1949; Gabaix, 1999; Axtell, 2001). Scientific citations show α between 2.5 and 3.0 (Redner, 1998), while web page visits fall in the 2.0–2.5 range (Adamic & Huberman, 2000). The mechanism generating these power laws is typically *preferential attachment* (Simon, 1955; Barabási & Albert, 1999): success begets success, creating "rich-get-richer" dynamics where early advantages compound over time. A declining α indicates heavier tails — more probability mass concentrated among top performers.

---

## 4. Power Law Results

### 4.1 Power Law Analysis: Organization vs Personal Developers

Table 1 presents power law exponent estimates for org and personal developers separately. Recall that lower α indicates greater concentration: when α falls, extreme values (superstar developers) become more probable relative to typical developers. The threshold α = 2 marks a critical boundary — below this value, the distribution has infinite variance, meaning the sample mean becomes unstable and dominated by outliers.

| Year | Org (n) | α | xmin | R | Personal (n) | α | xmin | R |
|:----:|:-------:|:----:|:----:|:----:|:------------:|:----:|:----:|:----:|
| 2019 | 9,824 | 2.04 | 6 | +3.05 | 53,945 | 1.99 | 25 | −1.16 |
| 2020 | 14,502 | 2.06 | 7 | +1.98 | 73,483 | 1.95 | 33 | −1.36 |
| 2021 | 18,253 | 2.08 | 7 | +3.31 | 83,614 | 1.86 | 39 | −2.15 |
| 2022 | 20,764 | 1.91 | 37 | −0.97 | 92,200 | 1.83 | 40 | −2.74 |
| 2023 | 23,411 | 2.06 | 6 | −0.95 | 99,585 | 1.82 | 38 | −2.68 |
| 2024 | 25,490 | 2.04 | 5 | +6.83 | 102,204 | 1.78 | 45 | −3.11 |
| 2025 | 18,285 | 1.87 | 25 | −0.31 | 71,171 | 1.80 | 33 | −2.00 |

*Table 1: Power law estimates by developer type, 2019-2025. α = power law exponent (Clauset-Shalizi-Newman MLE); lower values indicate heavier tails. xmin = minimum threshold where power law behavior begins. R = likelihood ratio test vs. log-normal alternative (R > 0 favors power law). 2025 covers January–October only. Source: `output/powerlaw_lognormal_comparison.csv`, `output/powerlaw_2025.csv`.*

![Power Law α: Org vs Personal Developers (2019-2025)](output/powerlaw_alpha_comparison.png)

*Figure 1: Power law exponent α over time. Lower α = more concentration. Personal developers (red) show steady decline 2019-2024, then stabilize. Org developers (blue) remain flat through 2024, then drop sharply in 2025. The dashed line at α = 2 marks the infinite-variance threshold.*

The results reveal two distinct concentration waves affecting different developer populations at different times.

**Personal developers concentrated first (2019-2024).** Among personal-only developers, α declined steadily from 1.99 in 2019 to 1.78 in 2024 — a cumulative decline of 0.21 points. To interpret this magnitude: an α of 1.99 implies the probability of observing a developer with 10× the median commits is roughly 1/100; at α = 1.78, this probability approximately doubles. The distribution crossed into the infinite-variance regime (α < 2) by 2020 and continued deepening. The sharpest single-year decline occurred between 2020 and 2021 (α: 1.95 → 1.86), coinciding with COVID-era conditions — increased free time, remote work, and a coding education boom — rather than AI tool adoption (Copilot launched June 2022). By 2024-2025, personal developers' α stabilized near 1.80, suggesting this population had already reached high concentration levels.

**Org developers concentrated later, but sharply (2025).** Organization developers followed a different trajectory. From 2019 through 2024, α fluctuated narrowly between 2.04 and 2.08, showing no clear trend — concentration was essentially flat. Then in 2025, α dropped abruptly to 1.87, a decline of 0.17 points in a single year (and this covers only January–October). This timing coincides with enterprise AI coding tools reaching production readiness: Claude Code launched February 2025, Codex in May 2025 — though we cannot establish that these tools *caused* the shift. The xmin parameter also shifted notably for org developers, jumping from 5-7 commits (2019-2024) to 25 commits (2025), consistent with the power law now applying only to the heavy tail rather than most of the distribution.

**Interpreting the lag.** Why might org developers have concentrated later? One hypothesis is differential adoption barriers. Personal developers face no institutional barriers to tool adoption: an individual who wants to use Copilot simply installs it. Org developers operate within enterprise constraints — procurement cycles, security reviews, legal approval, and code review processes that must accommodate AI-generated contributions. If these organizational frictions delayed adoption by approximately 2-3 years, this would be consistent with typical enterprise technology diffusion cycles. The 2025 acceleration is *consistent with* these barriers being cleared, though alternative explanations cannot be ruled out. Both populations appear to be converging toward similar α values (~1.8).

**Statistical notes.** The R statistic (likelihood ratio vs. log-normal) is mixed: positive values for org developers in most years indicate power law is preferred, while negative values for personal developers suggest the body of the distribution is better characterized as log-normal with a power-law tail. This is consistent with Gabaix (2016) on productivity distributions. The pattern does not affect our core finding — both the power law tail and the log-normal body show increasing concentration over time.

As a robustness check, we also estimate α on the pooled sample (org + personal combined). The pooled α declined from 1.96 to 1.63 over 2019-2024, confirming the concentration trend. However, pooling obscures the different timing patterns documented above. Detailed pooled analysis and additional robustness checks appear in Appendix A.

### 4.2 Transition Matrix: Developer Persistence

Power law analysis tells us concentration is increasing — but it doesn't tell us *who* is concentrating. Are the same developers dominating year after year ("persistent superstars"), or do different developers have exceptional years and then fade ("rotating superstars")? The transition matrix answers this by tracking individual developers across consecutive years.

We classify developers into quantiles (Top 1%, Top 10%, Middle, Bottom 50%) based on each year's commit distribution, then measure what fraction of developers in each quantile remain there the following year. Our key metric is **Top 1% → Top 1% persistence**: the probability that a top-1% developer in year T remains in the top 1% in year T+1. High persistence (e.g., 40%+) indicates the same developers dominate year after year — classic "rich-get-richer" dynamics. Low persistence (e.g., <20%) suggests rotating superstars, where different developers have exceptional years then fade.

Table 2 presents transition probabilities for org developers; Table 3 for personal developers.

| Transition | n (common devs) | Top 1% → Top 1% | Top 1% → Top 10% |
|:----------:|:---------------:|:---------------:|:----------------:|
| 2019→2020 | 1,839 | 36.8% | 57.9% |
| 2020→2021 | 2,564 | 23.1% | 61.5% |
| 2021→2022 | 3,037 | 29.0% | 51.6% |
| 2022→2023 | 3,377 | 47.1% | 67.6% |
| 2023→2024 | 3,719 | 31.6% | 68.4% |
| 2024→2025 | 2,920 | 33.3% | 56.7% |

*Table 2: Transition probabilities for org developers. n = developers appearing in both years.*

| Transition | n (common devs) | Top 1% → Top 1% | Top 1% → Top 10% |
|:----------:|:---------------:|:---------------:|:----------------:|
| 2019→2020 | 8,673 | 27.6% | 57.5% |
| 2020→2021 | 11,162 | 28.6% | 71.4% |
| 2021→2022 | 11,902 | 25.0% | 52.5% |
| 2022→2023 | 12,744 | 27.3% | 60.9% |
| 2023→2024 | 13,527 | 28.7% | 64.7% |
| 2024→2025 | 10,195 | 35.3% | 61.8% |

*Table 3: Transition probabilities for personal developers. 2025 covers January–October only. Source: `output/transition_matrix_org_split.csv`*

The results are striking. Among org developers, the average Top 1% → Top 1% persistence was 29.6% in the pre-AI period (2019-2021 transitions) and rose to 37.3% post-AI (2022-2024 transitions) — an increase of 7.7 percentage points. Among personal developers, persistence rose from 27.1% to 30.4%, a gain of 3.3 percentage points. Both groups show the same directional pattern: **superstars are becoming more persistent over time, not less.**

| Group | Pre-AI Avg (2019-2021) | Post-AI Avg (2022-2024) | Change |
|-------|:----------------------:|:-----------------------:|:------:|
| Org Developers | 29.6% | 37.3% | +7.7 pp |
| Personal Developers | 27.1% | 30.4% | +3.3 pp |

*Table 4: Summary of persistence changes pre- vs post-AI.*

![Top 1% Persistence: Org vs Personal Developers](output/transition_matrix_org_split.png)

*Figure 2: Top-1% year-over-year persistence by developer type. Both groups show increased persistence post-AI, with org developers showing larger gains.*

These findings are inconsistent with a simple "rotating superstars" hypothesis. If new productivity tools democratized exceptional output — enabling different developers to have breakthrough years — we would expect persistence to *decline*. Instead, the same developers appear more likely to remain at the top from year to year. This pattern is *consistent with* a "rich-get-richer" interpretation, though we cannot establish causation: productivity tools may amplify advantages for those who already excel, but alternative explanations (selection effects, changing developer composition) cannot be ruled out.

Why do org developers show larger persistence gains (+7.7 pp vs +3.3 pp)? One possibility is that enterprise AI tools, once integrated into established workflows, provide consistent productivity gains that compound over time. Organizational structures that initially slowed adoption may now lock in advantages once tools are deployed. Code review and collaboration patterns in team settings may also favor persistent high performers who build institutional knowledge alongside technical output.

---

## 5. Discussion

### What's Driving Concentration? The Adoption Lag Story

The key pattern — that concentration increased among personal developers first (2020-2022) and org developers later (2025) — is *consistent with* adoption lag as a potentially important factor. Both groups eventually concentrate; the difference appears to be *when*, not *whether*.

**Phase 1 (2020-2024): Concentration rises among personal developers first.**

Personal developers faced no organizational barriers to adopting new tools or work patterns. COVID may have created favorable conditions (more free time, remote work normalization, coding education surge), and when AI tools arrived (Copilot, June 2022), they were immediately accessible to individuals. Concentration increased as α dropped from 1.99 → 1.78.

**Phase 2 (2025): Org developers concentrate later.**

Org developers operate within institutional constraints that may have *delayed* adoption of new productivity tools. By 2025, enterprise AI coding tools launched with enterprise-grade features: Claude Code (Feb 2025) and Codex (May 2025). Org developers' α dropped from 2.04 → 1.87 — though we cannot establish that tool adoption caused this change.

**The updated institutional hypothesis.** If the adoption lag interpretation is correct, institutions don't *prevent* concentration; they *delay* it. The ~2-3 year gap between personal concentration (2020-2022) and org concentration (2025) would be consistent with typical enterprise technology adoption cycles. Both groups appear to be converging toward similar α values (~1.8), which is consistent with — though does not prove — productivity amplification effects being universal across developer types.

**Potential implications beyond GitHub:** If the adoption lag pattern generalizes, markets requiring institutional adoption of new technologies may show lagged concentration effects compared to markets where individuals can adopt tools directly. This hypothesis warrants investigation in other contexts.

### Limitations

Our analysis has several important limitations that should inform interpretation.

*Data cutoff: October 31, 2025.* GitHub's Events API removed commit details from PushEvent payloads on October 7, 2025. Our 2025 data covers only January–October (10 months vs. 12 months for other years). This may affect year-over-year comparisons, though the direction of the 2025 findings (org concentration) is clear.

*Correlation, not causation.* Concentration increases correlate with AI adoption timelines, but we cannot establish causation. The personal developer inflection point (2020-2021) preceded mass AI adoption, suggesting COVID-related factors (remote work, coding education) also contributed. The org developer inflection point (2025) aligns with enterprise AI tool launches but could reflect other factors.

*AI detection is a floor, not a ceiling.* Only 0.001% of commits have explicit AI markers. Industry surveys suggest 30-50% of developers use AI coding tools. The gap exists because: (a) most tools don't auto-tag commits; (b) there's no incentive for disclosure; (c) AI suggestions are typically edited before committing. Our explicit AI detection captures almost none of actual AI-assisted coding.

*Sampling limitations.* Our stratified sample (1st of each month, 4 time slots) may miss weekly or seasonal patterns. However, our sample size (625,590 developer-years, 19.3 million commits through 2024, plus 89,456 developers in 2025) is large enough that sampling variance is unlikely to affect main conclusions.

*Ceiling effects bias 2024 estimates downward.* Our 10,000 commits/year ceiling excludes automated accounts that passed bot pattern filters. In 2024, 1,155 accounts exceeded this threshold (vs. 175 in 2023) and 180 hit the ceiling — their true counts could be 50k, 100k, or higher. This creates a conservative bias: if we included these accounts at their true commit counts, concentration would be even higher.

*Ceiling effects bias 2024 estimates downward.* The 10,000 commit/year ceiling excludes accounts whose true counts could be 50k, 100k, or higher. With 180 accounts hitting this cap in 2024 (vs. 1 in 2023), our concentration estimates for 2024 are likely understated.

*Public repositories only.* GH Archive captures only public GitHub activity. Most enterprise development occurs in private repositories, which we cannot observe. Our "org developers" are those contributing to *public* org repos — open-source foundations, public company projects — not private corporate codebases. The 2025 org concentration finding may understate enterprise effects if private repo adoption lags public repos.

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

## Appendix A: Pooled Sample Analysis and Robustness

### A.1 Pooled Power Law Estimates

Combining all multi-repo developers (org + personal):

| Year | α (exponent) | xmin | R (vs. log-normal) | Best Fit |
|------|--------------|------|--------------------|----------|
| 2019 | 1.96 | 25 | -3.16 | Log-normal |
| 2020 | 1.93 | 34 | -5.64 | Log-normal |
| 2021 | 2.09 | 5 | +6.33 | Power law |
| 2022 | 1.85 | 36 | -6.47 | Log-normal |
| 2023 | 1.82 | 40 | -14.32 | Log-normal |
| 2024 | 1.63 | 30 | -31.58 | Log-normal |
| 2025 | 1.81 | 35 | -2.49 | Log-normal |

*2025 data: January–October only (10 months).*

*Interpretation: α declined from 1.96 to 1.63 (2019-2024), then rose to 1.81 in 2025. The 2025 increase may reflect: (a) 10-month truncation reducing extreme outliers, or (b) sampling differences. Source: `output/multi_repo_analysis.csv`, `output/filtered_developers_2025.csv`*

**xmin interpretation:** The xmin parameter (25-40 commits/year) identifies where power law behavior begins — roughly 2-4 commits/month. Developers above this threshold are in the heavy tail.

**Log-normal vs power law:** Negative R values indicate log-normal body with power-law tail — consistent with Gabaix (2016) on productivity distributions.

### A.2 Robustness: Full Sample vs. Multi-Repo

| Year | Full Sample Top 1% | Multi-Repo Top 1% | Difference |
|------|--------------------|--------------------|------------|
| 2019 | 49.5% | 45.3% | -4.2pp |
| 2020 | 51.3% | 47.8% | -3.5pp |
| 2021 | 54.8% | 52.2% | -2.6pp |
| 2022 | 56.4% | 53.7% | -2.7pp |
| 2023 | 60.2% | 54.6% | -5.6pp |
| 2024 | 68.9% | 63.9% | -5.0pp |
| 2025 | — | 57.7% | — |

*2025 data: January–October only. Full sample comparison not available for 2025 extraction.*

*Finding:* Both samples show the same upward trend. Multi-repo filter reduces concentration by 3-5pp but trend is robust.

### A.3 Power Law α Robustness Across Developer Filters

| Year | Multi-Repo (n≥2 repos) | Strict (n≥3 repos, ≥10 commits) | Very Strict (n≥4 repos, ≥20 commits) |
|------|------------------------|----------------------------------|---------------------------------------|
| 2019 | 1.96 | 1.96 | 1.93 |
| 2020 | 1.93 | 1.94 | 1.91 |
| 2021 | 2.09 | 1.87 | 1.87 |
| 2022 | 1.85 | 1.81 | 1.80 |
| 2023 | 1.82 | 1.81 | 1.80 |
| 2024 | 1.63 | 1.64 | 1.64 |
| 2025 | 1.81 | — | — |

*2025 data: January–October only. Stricter filter variants not computed for 2025.*

*Source: `output/developer_powerlaw_analysis.csv`*

*Finding:* The α decline is robust across all developer definitions.

### A.4 Counterfactual α: Sensitivity to Tail Exclusion

To test whether concentration is driven by a few extreme accounts or a broad distributional shift, we re-estimate α after dropping the top 0.1%, 1%, and 5% of accounts.

| Year | α (baseline) | α (drop 0.1%) | α (drop 1%) | α (drop 5%) |
|:----:|:------------:|:-------------:|:-----------:|:-----------:|
| 2019 | 1.96 | 2.02 | 2.23 | 2.68 |
| 2020 | 1.93 | 2.00 | 2.29 | 2.76 |
| 2021 | 2.10 | 2.14 | 2.28 | 2.83 |
| 2022 | 1.85 | 2.11 | 2.30 | 2.79 |
| 2023 | 1.82 | 2.13 | 2.29 | 2.71 |
| 2024 | 1.63 | 1.97 | 2.03 | 2.66 |
| 2025 | 1.81 | 2.14 | 2.32 | 2.95 |

*2025 data: January–October only (10 months).*

**Sensitivity analysis:**

| Comparison | Baseline Δα | Drop 5% Δα | % Persisting |
|------------|:-----------:|:----------:|:------------:|
| 2019 → 2024 | −0.33 | −0.03 | 7.7% |
| 2019 → 2025 | −0.16 | +0.27 | — |

*Source: `output/counterfactual_alpha.csv`*

**Interpretation:** Only 7.7% of the α decline (2019→2024) persists after excluding the top 5% of accounts. This is consistent with concentration being driven by **extreme accounts** rather than a broad distributional shift.

This pattern is consistent with a "superstar coder" hypothesis: concentration may reflect a small number of developers pulling dramatically ahead, rather than a general rightward shift in the distribution. If AI coding tools amplify productivity, this effect appears concentrated among the most productive developers.

### A.5 Zipf Rank-Size Plots

The Zipf plot ranks developers from highest commits (rank 1) to lowest on log-log axes. A line sitting *higher* means developers at each rank contribute more commits. If lines diverge over time, concentration is increasing.

<img src="output/zipf_org_developers.png" width="500">

*Org developers: Lines cluster tightly 2019-2024, then 2025 shifts upward at low ranks — top performers pulled ahead sharply in 2025.*

<img src="output/zipf_personal_developers.png" width="500">

*Personal developers: Lines diverge earlier (2020-2021 onward), with 2024 sitting notably higher at low ranks. Concentration increased steadily, then stabilized.*

### A.6 Concentration Measures (Multi-Repo Sample)

| Year | Accounts | Top 1% Share | Top 10% Share | Gini | P99/P50 |
|:----:|:--------:|:------------:|:-------------:|:----:|:-------:|
| 2019 | 64,406 | 45.3% | 71.9% | 0.750 | 45 |
| 2020 | 88,765 | 47.8% | 72.2% | 0.753 | 44 |
| 2021 | 102,867 | 52.2% | 75.2% | 0.779 | 51 |
| 2022 | 113,981 | 53.7% | 76.1% | 0.787 | 54 |
| 2023 | 124,041 | 54.6% | 76.9% | 0.792 | 56 |
| 2024 | 131,530 | 63.9% | 89.2% | 0.895 | 215 |
| 2025 | 89,456 | 57.7% | 78.3% | 0.797 | 59 |

*2025 data: January–October only. Source: `output/multi_repo_analysis.csv`, `output/descriptive_stats_2025.csv`*

### A.7 AI Detection in Commit Messages

| Year | Total Commits | AI-Attributed | Rate |
|:----:|:-------------:|:-------------:|:----:|
| 2019 | 1,936,241 | 0 | 0.000% |
| 2020 | 2,803,770 | 0 | 0.000% |
| 2021 | 3,716,022 | 0 | 0.000% |
| 2022 | 4,615,220 | 0 | 0.000% |
| 2023 | 6,259,638 | 50 | 0.001% |
| 2024 | 7,882,625 | 115 | 0.001% |
| 2025 | 2,180,740 | — | — |

*Detection patterns: `aider:` prefix (72 commits in 2024), `Co-authored-by: Copilot` (23), `generated by GPT/Claude/Copilot` (18). Only 0.001% of commits have explicit AI markers, despite surveys suggesting 30-50% of developers use AI tools.*

### A.8 Bootstrap Confidence Intervals

We estimate bootstrap confidence intervals (500 iterations) for the power law exponent α.

**Org Developers:**

| Year | n | α | 95% CI |
|:----:|:---:|:-----:|:----------------:|
| 2019 | 9,824 | 2.037 | [1.955, 2.082] |
| 2020 | 14,502 | 2.063 | [2.024, 2.097] |
| 2021 | 18,253 | 2.075 | [1.960, 2.106] |
| 2022 | 20,764 | 1.911 | [1.882, 2.092] |
| 2023 | 23,411 | 2.055 | [1.827, 2.074] |
| 2024 | 25,490 | 2.037 | [1.967, 2.073] |
| 2025 | 18,285 | 1.866 | [1.816, 2.130] |

*Source: `output/bootstrap_org_developers.csv`*

**Personal-Only Developers:**

| Year | n | α | 95% CI |
|:----:|:-------:|:-----:|:------------------:|
| 2019 | 53,945 | 1.991 | [1.958, 2.031] |
| 2020 | 73,483 | 1.946 | [1.918, 1.978] |
| 2021 | 83,614 | 1.860 | [1.839, 2.168] |
| 2022 | 92,200 | 1.826 | [1.800, 2.163] |
| 2023 | 99,585 | 1.817 | [1.795, 2.183] |
| 2024 | 102,204 | 1.779 | [1.765, 2.168] |
| 2025 | 71,171 | 1.798 | [1.768, 2.156] |

*Source: `output/bootstrap_personal_developers.csv`. 2025 data: January–October only.*

The point estimates show a declining trend in α for personal developers (1.991 → 1.779). The wide confidence intervals in later years reflect increased variance as the tail gets heavier.

---

\* Thank you to Sruly Rosenblat for helpful comments.

## License

MIT
