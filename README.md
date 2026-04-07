# Power Laws in GitHub Commits: Heterogeneity, Not Dynamics

## 1. Introduction

### Motivation

**Are AI coding tools creating a new class of "superstar" developers?**

Since 2022, AI-powered coding assistants — GitHub Copilot, ChatGPT, Cursor — have transformed software development. A natural hypothesis is that these tools amplify existing skill differences: the best developers adopt AI tools first, use them most effectively, and pull further ahead. If true, we should see increasing concentration in developer output, with the same top performers dominating year after year.

GitHub provides a natural laboratory to test this hypothesis. The platform hosts over 100 million developers and records every code contribution. A *commit* — a saved change to a repository — is the fundamental unit of developer output. We analyze how commits are distributed across developers, and whether this distribution is changing.

We find that commit distributions follow a power law, where a small number of developers account for a disproportionate share of total output. The *power law exponent* α measures concentration: lower α means heavier tails, with top contributors capturing more. Between 2019 and 2024, α declined from 2.0 to 1.8 — concentration increased.

But does this pattern reflect AI amplifying superstars? Or something else entirely? Two competing hypotheses offer different interpretations.

### Two Competing Hypotheses

**Hypothesis A: "AI Is Creating Superstar Developers"**

AI coding tools (Copilot, ChatGPT, Cursor) amplify the productivity of developers who are already highly skilled. The best developers adopt these tools first, learn to use them most effectively, and pull further ahead. Their output compounds: more commits lead to more visibility, which attracts collaborators and opportunities, generating still more commits. The same individuals dominate year after year, and the gap between top performers and everyone else widens. In this view, declining α signals dynamic concentration — a "rich-get-richer" process where productivity advantages compound over time.

**Hypothesis B: "The Developer Population Is Diversifying"**

GitHub's user base has become increasingly heterogeneous. In 2019, GitHub users were predominantly professional developers. By 2024, the platform hosts: full-time professional developers, open-source maintainers, students learning to code, hobbyists who contribute occasionally, researchers pushing code for papers, and automation pipelines that escaped bot detection. Each group has a different "natural rate" of committing. The power law emerges from *mixing* these different populations, not from individuals becoming more concentrated. In this view, declining α reflects compositional change — who joins the platform — not behavioral change among existing developers.

### Why It Matters

These hypotheses have different implications, connecting to foundational debates in labor economics about technology and inequality:

- **If Hypothesis A is correct:** There are policy implications about skill premiums, labor market polarization, and AI amplifying inequality. The same developers are pulling ahead, potentially creating a winner-take-all dynamic in software labor markets. This would align with Rosen's (1981) "superstar" economics, where small talent differences yield large reward differences when technology enables scale.

- **If Hypothesis B is correct:** The pattern reflects platform growth and demographic shifts, not changes in individual behavior. Declining α is consistent with GitHub becoming more heterogeneous — more casual users AND more heavy contributors — without any dynamic concentration process. This compositional explanation has different policy implications: the pattern may reverse as platform growth slows.

### This Paper

We run diagnostic tests to distinguish these hypotheses. Evidence strongly favors Hypothesis B (diversification), with one exception: organization developers in 2023-2024 show patterns consistent with Hypothesis A (AI amplification).

### Key Findings

| Diagnostic Test | Hypothesis A Predicts | Hypothesis B Predicts | Our Finding |
|-----------------|----------------------|----------------------|-------------|
| Attachment kernel (β) | β ≈ 1 (proportional growth) | β < 1 (mean reversion) | **β ≈ 0.4** → B |
| Rate heterogeneity (r) | r stable | r declining | **r: 0.51 → 0.24, p = 0.009** → B |
| Top 1% composition | Incumbents dominate | New accounts dominate | **72-80% new accounts** → B |
| Rank persistence (ρ) | High ρ | Low ρ | **ρ ≈ 0.18** → B |

**The exception:** Among organization developers in 2023-2024, "increased activity" overtook "new accounts" as the dominant source of top 1% entrants (49% vs 40%), with a median growth ratio of 1,135× — patterns consistent with genuine productivity amplification. This timing coincides with enterprise AI coding tools clearing procurement and security hurdles at large companies, though we cannot establish causation.

---

## 2. Data

### 2.1 Source: GH Archive

We use [GH Archive](https://www.gharchive.org/), which records all public GitHub events in real-time since 2011. Each hourly file contains JSON records of every public event on GitHub, including PushEvents (commits), which are our focus.

**Data cutoff: October 31, 2025.** GitHub's Events API [removed commit details](https://github.blog/changelog/2025-08-08-upcoming-changes-to-github-events-api-payloads/) from PushEvent payloads on October 7, 2025. GH Archive inherited this change, so our 2025 data covers January 1 – October 31 only.

### 2.2 Sampling Strategy

Processing the full GH Archive is prohibitively expensive (~50TB uncompressed). We use a stratified sample:

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Time of day** | 4 samples (00:00, 06:00, 12:00, 18:00 UTC) | Captures global activity |
| **Day selection** | 1st of each month | Consistent sampling frame |
| **Years** | 2019-2025 | Pre-AI baseline through AI adoption |
| **Sample size** | 328 hourly files | ~25GB compressed |

**Total sample:** ~1.7 million developer-year observations and ~58 million commits across 2019-2025.

### 2.3 Data Quality Filters

Following best practices from the mining software repositories literature (Kalliamvakou et al., 2016; Dey et al., 2020):

1. **Bot exclusion:** 15+ patterns (dependabot, renovate, github-actions, etc.)
2. **Distinct commits only:** Using `distinct_size` to avoid merge double-counting
3. **Minimum activity:** ≥3 commits/year
4. **Behavioral ceiling:** ≤10,000 commits/year (catches automation)
5. **Multi-repo filter:** 2+ repositories/year (primary sample)

**Final sample:** 625,590 developer-year observations and 19.3 million commits (2019-2024).

### 2.4 Panel Structure

For mechanism diagnostic tests, we track developers across years:

| Metric | Value |
|--------|-------|
| Developers appearing in 2+ years | 48,234 |
| Developers appearing in all 6 years (2019-2024) | 2,643 |
| Org developers in 2+ years | 12,871 |
| Personal developers in 2+ years | 35,363 |

### 2.5 Organization vs. Personal Developers

We classify developers into two groups based on whether they contribute to organization-owned repositories:

- **Organization ("org") developers:** At least one commit to a repository owned by a known organization account. We identify org accounts via a curated list of 70+ major organizations (Google, Microsoft, Meta, Apache, Mozilla, etc.) plus heuristic patterns for org-like names. Org developers are more likely to be professional developers working on public open-source projects.

- **Personal-only developers:** Zero commits to any organization-owned repository — all commits go to personal or individual accounts. This group includes hobbyists, students, and developers working exclusively on their own projects.

This classification proxies for professional vs. non-professional developers, though with important caveats: many professional developers work only in private repos (which we cannot observe), and some personal-account projects are professionally maintained.

### 2.6 Descriptive Statistics

#### Sample Sizes by Year

| Year | Multi-Repo Accounts | Org Developers | Personal-Only |
|------|---------------------|----------------|---------------|
| 2019 | 64,406 | 9,824 | 53,945 |
| 2020 | 88,765 | 14,502 | 73,483 |
| 2021 | 102,867 | 18,253 | 83,614 |
| 2022 | 113,981 | 20,764 | 92,200 |
| 2023 | 124,041 | 23,411 | 99,585 |
| 2024 | 131,530 | 25,490 | 102,204 |
| 2025* | 89,456 | 18,285 | 71,171 |

*2025 data: January–October only (10 months).*

#### Commit Distribution

| Year | Total Commits | Mean | Median | P99 |
|------|---------------|------|--------|-----|
| 2019 | 1,384,035 | 21.5 | 6 | 268 |
| 2020 | 1,924,456 | 21.7 | 6 | 265 |
| 2021 | 2,525,459 | 24.6 | 6 | 306 |
| 2022 | 2,865,724 | 25.1 | 6 | 321 |
| 2023 | 3,132,816 | 25.3 | 6 | 339 |
| 2024 | 7,463,885 | 56.7 | 6 | 1,287 |

The median remains stable at 6 commits/year while P99 increases sharply, consistent with concentration in the upper tail.

---

## 3. Method

### 3.1 Power Law Estimation

We follow the Clauset-Shalizi-Newman (2009) methodology:

1. **Threshold selection:** Determine xmin where power law behavior begins using the Kolmogorov-Smirnov statistic
2. **MLE estimation:** Fit α for the tail above xmin:
   $$\hat{\alpha} = 1 + n \left[ \sum_{i=1}^{n} \ln \frac{x_i}{x_{\min}} \right]^{-1}$$
3. **Alternative comparison:** Compare power law to log-normal using likelihood ratio test (R statistic)

**Interpreting the R statistic:**
- R > 0: Power law fits better than log-normal (normalized likelihood ratio favors power law)
- R < 0: Log-normal fits better (common when the body of the distribution is log-normal with only the extreme tail following a power law)
- |R| > 2: Statistically significant difference at conventional levels

**Interpreting α:**
- α > 2: Finite variance; distribution is "well-behaved"
- α < 2: Infinite variance; sample mean dominated by outliers
- Lower α = heavier tail = more concentration

### 3.2 Mechanism Diagnostic Tests

Power law estimation tells us concentration is increasing, but not *why*. We implement four diagnostic tests to distinguish competing mechanisms.

#### 3.2.1 Attachment Kernel Test

**Purpose:** Does a developer's growth depend on their current size?

**Model:**
$$\log(x_{i,t}) = \alpha + \beta \cdot \log(x_{i,t-1}) + \varepsilon_{i,t}$$

where x_{i,t} is developer i's commits in year t.

**Interpretation:**
- **β ≈ 1:** Proportional growth — consistent with preferential attachment ("rich-get-richer")
- **β < 1:** Sublinear growth — consistent with mean reversion; advantages don't compound
- **β > 1:** Superlinear growth — winner-take-all dynamics accelerating

#### 3.2.2 Rate Heterogeneity Test

**Purpose:** Is the distribution better explained by mixing different types of developers?

**Model:** Compare Poisson (homogeneous rates) vs. Negative Binomial (heterogeneous rates):
- Poisson: All developers have the same underlying commit rate λ
- Negative Binomial: Rates λᵢ vary across developers, drawn from Gamma(r, β)

If commits | λᵢ ~ Poisson(λᵢ) and λᵢ ~ Gamma(r, β), then commits ~ NegBin(r, p).

**The mixture intuition:** Suppose GitHub hosts different "types" of developers — full-time professionals (high λ), hobbyists (medium λ), and students (low λ). Even if each type commits at a stable rate, mixing these populations together creates overdispersion. The Negative Binomial captures this mixture, and its dispersion parameter r measures how much the rates vary across types (Mitzenmacher, 2004).

**Key parameters:**
- **r** = dispersion parameter; lower r = more heterogeneity
- **CV(λ) = 1/√r** = coefficient of variation of underlying rates

**Interpretation:**
- NegBin >> Poisson (LR test): Confirms rate heterogeneity exists
- r declining over time: Heterogeneity is *increasing*
- Increasing CV(λ) mechanically produces heavier tails without any dynamic process

#### 3.2.3 Top 1% Composition Analysis

**Purpose:** Who enters the top 1% each year?

For each year-over-year transition, we classify new top-1% entrants:
- **Genuinely new accounts:** First appearance in the data
- **Increased activity:** Existed in prior year but below top 1%
- **Near-top promotion:** Were in top 5% (but not top 1%) in prior year

**Interpretation:**
- "New accounts" dominates → Platform growth effect; top performers are new arrivals with high rates
- "Increased activity" dominates → Existing developers being amplified (consistent with AI tools)

#### 3.2.4 Rank Persistence Test

**Purpose:** Do the same developers stay at the top?

**Metrics:**
- Spearman rank correlation (ρ) between years
- Top 10% → Top 10% persistence rate

**Interpretation:**
- High ρ, high persistence → Persistent superstars (consistent with preferential attachment)
- Low ρ, low persistence → Rotating superstars (consistent with heterogeneous rates)

---

## 4. Findings

### 4.1 Power Law Estimates: α Is Declining

Table 1 presents power law exponent estimates by developer type.

**Table 1: Power Law Estimates (2019-2025)**

| Year | Personal (n) | Personal α | R | Org (n) | Org α | R |
|:----:|:------------:|:----------:|:---:|:-------:|:-----:|:---:|
| 2019 | 53,945 | 1.99 | −1.16 | 9,824 | 2.04 | +3.05 |
| 2020 | 73,483 | 1.95 | −1.36 | 14,502 | 2.06 | +1.98 |
| 2021 | 83,614 | 1.86 | −2.15 | 18,253 | 2.08 | +3.31 |
| 2022 | 92,200 | 1.83 | −2.74 | 20,764 | 1.91 | −0.97 |
| 2023 | 99,585 | 1.82 | −2.68 | 23,411 | 2.06 | −0.95 |
| 2024 | 102,204 | 1.78 | −3.11 | 25,490 | 2.04 | +6.83 |
| 2025* | 71,171 | 1.80 | −2.00 | 18,285 | 1.87 | −0.31 |

*R = likelihood ratio vs. log-normal; R > 0 favors power law, R < 0 favors log-normal. 2025 covers Jan-Oct only.*

**Key patterns:**
- Personal developers: α declined steadily from 1.99 to 1.78 (Δ = −0.21). R consistently negative, indicating log-normal body with power-law tail.
- Org developers: α stable around 2.04 through 2024, then dropped sharply to 1.87 in 2025 (Δ = −0.17 in one year).

But declining α alone does not identify mechanism. We turn to diagnostic tests.

### 4.2 Attachment Kernel: β ≈ 0.4 (Sublinear)

**Table 2: Attachment Kernel Estimates**

| Group | Period | β | SE | R² | p-value |
|-------|--------|------|-------|-------|---------|
| All Developers | 2019-2020 | 0.377 | 0.011 | 0.095 | <0.001 |
| All Developers | 2020-2021 | 0.399 | 0.010 | 0.102 | <0.001 |
| All Developers | 2021-2022 | 0.392 | 0.009 | 0.103 | <0.001 |
| All Developers | 2022-2023 | 0.445 | 0.009 | 0.128 | <0.001 |
| All Developers | 2023-2024 | 0.473 | 0.010 | 0.108 | <0.001 |
| Org Developers | 2019-2020 | 0.316 | 0.023 | 0.072 | <0.001 |
| Org Developers | 2023-2024 | 0.447 | 0.022 | 0.091 | <0.001 |
| Personal Developers | 2019-2020 | 0.386 | 0.013 | 0.098 | <0.001 |
| Personal Developers | 2023-2024 | 0.472 | 0.011 | 0.111 | <0.001 |

**Interpretation:** The attachment kernel coefficient β ranges from 0.32 to 0.47 across all periods and groups, significantly below unity (p < 0.001 in all cases). A coefficient β = 0.4 implies that a developer with 10× the commits of another experiences only 10^0.4 ≈ 2.5× the growth rate, not 10× as preferential attachment would predict.

This sublinearity indicates **mean reversion**: high-commit developers in year t regress toward the mean in year t+1. Productivity advantages do not compound.

**Verdict:** β ≈ 0.4 **rejects Hypothesis A** (preferential attachment requires β ≈ 1).

### 4.3 Rate Heterogeneity: r Declining Significantly

**Table 3: Negative Binomial Dispersion Parameter (r)**

| Group | Year | r | CV(λ) | LR Statistic | p-value |
|-------|------|-------|-------|--------------|---------|
| Personal | 2019 | 0.509 | 1.40 | 4.7 × 10⁶ | <10⁻¹⁰⁰ |
| Personal | 2020 | 0.533 | 1.37 | 5.3 × 10⁶ | <10⁻¹⁰⁰ |
| Personal | 2021 | 0.467 | 1.46 | 9.9 × 10⁶ | <10⁻¹⁰⁰ |
| Personal | 2022 | 0.445 | 1.50 | 13.2 × 10⁶ | <10⁻¹⁰⁰ |
| Personal | 2023 | 0.367 | 1.65 | 24.4 × 10⁶ | <10⁻¹⁰⁰ |
| Personal | 2024 | 0.238 | 2.05 | 141.3 × 10⁶ | <10⁻¹⁰⁰ |
| Org | 2019 | 0.411 | 1.56 | 0.7 × 10⁶ | <10⁻¹⁰⁰ |
| Org | 2024 | 0.206 | 2.20 | 22.9 × 10⁶ | <10⁻¹⁰⁰ |

**Trend regression (r on year):**

| Group | Slope | SE | p-value | Interpretation |
|-------|-------|-----|---------|----------------|
| Personal Developers | −0.054 | 0.014 | **0.009** | Significant decline |
| Org Developers | −0.038 | 0.012 | **0.031** | Significant decline |
| All Developers | −0.050 | 0.013 | **0.011** | Significant decline |

**Interpretation:** The dispersion parameter r declined significantly for all groups. For personal developers, r fell from 0.509 to 0.238 — a 53% decline (p = 0.009). Since CV(λ) = 1/√r, this corresponds to the coefficient of variation of underlying commit rates increasing from 1.40 to 2.05 — a **46% increase in rate dispersion**.

The Negative Binomial vastly outperforms Poisson (likelihood ratio statistics in millions, p effectively zero), confirming substantial rate heterogeneity. The declining r indicates that heterogeneity in individual commit rates is **increasing over time**.

**Verdict:** This **supports Hypothesis B**. Increasing heterogeneity mechanically produces heavier tails (lower α) without any dynamic concentration process.

### 4.4 Top 1% Composition: New Accounts Dominate

**Table 4: Top 1% New Entrant Composition**

| Group | Period | n Entrants | % New Accounts | % Increased Activity | % Near-Top |
|-------|--------|------------|----------------|---------------------|------------|
| Personal | 2019-2020 | 1,881 | **79.6%** | 15.7% | 4.7% |
| Personal | 2020-2021 | 2,228 | **80.0%** | 14.0% | 6.0% |
| Personal | 2021-2022 | 2,485 | **78.1%** | 16.0% | 5.9% |
| Personal | 2022-2023 | 2,713 | **80.8%** | 13.7% | 5.5% |
| Personal | 2023-2024 | 3,023 | **77.6%** | 17.6% | 4.8% |
| Org | 2019-2020 | 128 | 57.8% | 30.5% | 11.7% |
| Org | 2020-2021 | 150 | 55.3% | 37.3% | 7.3% |
| Org | 2021-2022 | 162 | 51.9% | 40.1% | 8.0% |
| Org | 2022-2023 | 179 | 54.7% | 35.2% | 10.1% |
| **Org** | **2023-2024** | 197 | 40.1% | **48.7%** | 11.2% |

**Interpretation:** For personal developers, new accounts consistently comprise 77-80% of top 1% entrants across all periods. Top performers are predominantly **new arrivals to the platform**, not existing developers who increased their output.

For org developers, a notable shift occurs in 2023-2024: "increased activity" overtakes "new accounts" as the dominant source (48.7% vs 40.1%). This is the **only group/period** where existing developers increasing their output — rather than new arrivals — drive top-1% membership.

**Verdict:** Personal developers strongly **support Hypothesis B**. The 2023-2024 org developer pattern is **anomalous** and consistent with Hypothesis A (see Section 4.6).

### 4.5 Rank Persistence: Low (ρ ≈ 0.18)

**Table 5: Rank Persistence (2019 → 2024)**

| Group | n Matched | ρ (Spearman) | Top 10% Persistence |
|-------|-----------|--------------|---------------------|
| All Developers | 2,643 | 0.179 | 26.4% |
| Org Developers | 923 | 0.170 | 18.3% |
| Personal Developers | 1,720 | 0.175 | 27.3% |

**Year-over-year rank correlations:**

| Period | All | Org | Personal |
|--------|-----|-----|----------|
| 2019-2020 | 0.264 | 0.219 | 0.277 |
| 2020-2021 | 0.279 | 0.232 | 0.291 |
| 2021-2022 | 0.278 | 0.268 | 0.279 |
| 2022-2023 | 0.317 | 0.284 | 0.326 |
| 2023-2024 | 0.310 | 0.265 | 0.322 |

**Interpretation:** Rank correlation between 2019 and 2024 commit levels is low: ρ ≈ 0.18 for all groups. Only 18-27% of developers in the top 10% in 2019 remained in the top 10% in 2024. Year-over-year correlations range from 0.22 to 0.33.

This high mobility is inconsistent with "persistent superstars." Different developers dominate each year, consistent with the mixture mechanism where annual commit counts reflect draws from heterogeneous rate distributions.

**Verdict:** Low persistence **supports Hypothesis B** ("rotating superstars").

### 4.6 The Exception: 2024 Org Developers and AI Impact

One finding stands apart from the pattern supporting Hypothesis B.

**Table 6: Org Developer Top 1% Entrants — Growth Patterns**

| Period | Median Prior Commits | Median Current Commits | Median Growth Ratio |
|--------|---------------------|------------------------|---------------------|
| 2019-2020 | 9.5 | 581 | 73× |
| 2020-2021 | 8.0 | 682 | 97× |
| 2021-2022 | 9.0 | 751 | 80× |
| 2022-2023 | 8.0 | 575 | 80× |
| **2023-2024** | 6.0 | **8,137** | **1,135×** |

Among organization developers entering the top 1% in 2024:
- "Increased activity" (48.7%) overtook "new accounts" (40.1%) for the first time
- Median commits jumped from 575 to 8,137 — a 14× increase
- Median growth ratio was 1,135× compared to 73-97× in prior years
- This represents existing professional developers dramatically increasing output

**Timing:** This pattern coincides with enterprise AI coding tools reaching production-readiness and clearing procurement hurdles:
- GitHub Copilot launched for individuals (June 2022) and Copilot for Business (February 2023)
- Copilot Enterprise launched February 2024, offering organization-wide deployment with enhanced security
- ChatGPT (November 2022) and GPT-4 (March 2023) demonstrated AI coding capabilities
- By late 2023, these tools had cleared security and compliance requirements at many enterprises

**Interpretation:** The 2023-2024 org developer pattern is the **only evidence in our data consistent with Hypothesis A** (AI amplifying existing productive developers). The timing aligns with enterprise AI tool adoption. However, we cannot establish causation, and this represents one group in one period.

### 4.7 Summary: Mechanism Verdict

| Diagnostic | Hypothesis A Predicts | Hypothesis B Predicts | Our Finding | Verdict |
|------------|----------------------|----------------------|-------------|---------|
| Attachment kernel (β) | β ≈ 1 | β < 1 | β ≈ 0.4 | **B** |
| Rate heterogeneity (r) | r stable | r declining | r: 0.51 → 0.24 (p = 0.009) | **B** |
| Top 1% composition | Incumbents | New accounts | 72-80% new (personal) | **B** |
| Rank persistence (ρ) | High ρ | Low ρ | ρ ≈ 0.18 | **B** |
| Org 2024 composition | Incumbents | New accounts | 49% increased activity | **A** (exception) |

**Overall:** Evidence strongly supports **Hypothesis B** (diversification/heterogeneity), with one exception: org developers in 2023-2024 show patterns consistent with **Hypothesis A** (AI amplification).

---

## 5. Discussion

### 5.1 Main Interpretation: The Power Law Is a Mixture Artifact

The power law in GitHub commits arises primarily from **heterogeneity in developer types**, not from dynamic concentration. GitHub's growth from approximately 40 million to over 100 million users brought in a more diverse population: more casual learners, more hobbyists, more students — and simultaneously more heavy professional contributors and automation. The spread between these groups widened (CV(λ) increased by 46%), mechanically producing heavier tails (lower α).

This is a **compositional story** about who joins the platform, not a **behavioral story** about individuals becoming more productive. The declining α does not indicate that the same developers are "pulling ahead" — rank persistence is low (ρ ≈ 0.18), and 72-80% of top performers each year are new accounts.

### 5.2 What This Means for the AI Narrative

Our findings caution against inferring dynamic concentration from static distributions:

1. **Observing a power law is not evidence of "rich-get-richer."** Power laws can arise from pure heterogeneity without any dynamic process (Mitzenmacher, 2004).

2. **Declining α is not evidence of "AI amplifying superstars."** The decline is explained by increasing heterogeneity in commit rates, not by individual-level concentration.

3. **Mechanism tests are essential.** Descriptive statistics (Gini, top-k shares, α) do not identify mechanism. Our diagnostic tests distinguish compositional from behavioral explanations.

### 5.3 The Org Developer Exception: Potential AI Impact

The 2023-2024 org developer pattern is the exception that deserves attention:

- For the first time, "increased activity" (existing developers increasing output) dominated "new accounts" as the source of top 1% entrants
- Growth ratios were extreme: median 1,135× vs. 70-100× in prior years
- Timing coincides with enterprise AI tools (Copilot Enterprise, GPT-4) clearing procurement hurdles

This is **the only evidence in our data consistent with AI amplifying existing productive developers**. The pattern suggests that when enterprise AI coding tools became accessible to professional developers working in organizational contexts, some existing developers — not new arrivals — experienced dramatic productivity increases.

**Caveats:**
- This is one group (org developers) in one period (2023-2024)
- We cannot establish causation; correlation with AI tool timing is suggestive but not conclusive
- The pattern may reflect other factors (enterprise workflow changes, pandemic-era accumulation, sampling artifacts)

### 5.4 Implications

**For AI productivity research:** Studies claiming AI tools create "superstar" effects should demonstrate persistent individual-level advantages, not just cross-sectional concentration. Our finding that 72-80% of top performers are new each year challenges the "AI amplifies existing superstars" narrative for most of the population.

**For platform economics:** Concentration metrics (Gini, top-k shares) may reflect user base composition rather than behavioral changes. GitHub's growing heterogeneity — more casual users joining while professional contributor density also increases — can produce concentration patterns without any individual-level dynamics.

**For labor economics:** Classic superstar theory (Rosen, 1981) predicts that small differences in talent generate large differences in earnings when technology enables scale without replication. However, Rosen's framework assumes *persistent* individual advantages. Our finding of low rank persistence (ρ ≈ 0.18) and 72-80% annual turnover in top performers suggests a different dynamic: "superstars" may be a rotating cast rather than a stable elite. This has implications for skill-biased technical change debates (Autor et al., 2003; Acemoglu & Autor, 2011) — if AI tools create temporary productivity bursts rather than persistent advantages, the labor market implications differ substantially from models assuming cumulative skill advantages.

### 5.5 Limitations

- **Data ends October 2025** due to GitHub API schema change
- **Public repositories only** — private org repos (most enterprise development) not captured
- **Cannot observe AI tool usage directly** — timing correlations are suggestive but not causal
- **The 2024 org anomaly is one period** — may be noise rather than signal

---

## 6. References

### Power Law Theory and Methods
- Clauset, A., Shalizi, C. R., & Newman, M. E. J. (2009). "Power-law distributions in empirical data." *SIAM Review*, 51(4), 661-703.
- Mitzenmacher, M. (2004). "A brief history of generative models for power law and lognormal distributions." *Internet Mathematics*, 1(2), 226-251.
- Newman, M. E. J. (2005). "Power laws, Pareto distributions and Zipf's law." *Contemporary Physics*, 46(5), 323-351.

### Power Laws in Economics
- Gabaix, X. (1999). "Zipf's law for cities: An explanation." *Quarterly Journal of Economics*, 114(3), 739-767.
- Gabaix, X. (2009). "Power laws in economics and finance." *Annual Review of Economics*, 1, 255-294.

### Labor Economics and Superstars
- Rosen, S. (1981). "The economics of superstars." *American Economic Review*, 71(5), 845-858.
- Autor, D. H., Levy, F., & Murnane, R. J. (2003). "The skill content of recent technological change." *Quarterly Journal of Economics*, 118(4), 1279-1333.
- Acemoglu, D., & Autor, D. (2011). "Skills, tasks and technologies: Implications for employment and earnings." *Handbook of Labor Economics*, 4, 1043-1171.

### GitHub Data Mining
- Kalliamvakou, E., et al. (2016). "An in-depth study of the promises and perils of mining GitHub." *Empirical Software Engineering*, 21(5), 2035-2071.
- Dey, T., et al. (2020). "Detecting and characterizing bots that commit code." *MSR 2020*.

### Data
- GH Archive: https://www.gharchive.org/
- Python powerlaw package: https://github.com/jeffalstott/powerlaw

---

## Appendix A: Full Diagnostic Results

### A.1 Attachment Kernel Test (All Periods)

| Group | Period | β | SE | R² |
|-------|--------|------|-------|-------|
| All Developers | 2019-2020 | 0.377 | 0.011 | 0.095 |
| All Developers | 2020-2021 | 0.399 | 0.010 | 0.102 |
| All Developers | 2021-2022 | 0.392 | 0.009 | 0.103 |
| All Developers | 2022-2023 | 0.445 | 0.009 | 0.128 |
| All Developers | 2023-2024 | 0.473 | 0.010 | 0.108 |
| Org Developers | 2019-2020 | 0.316 | 0.023 | 0.072 |
| Org Developers | 2020-2021 | 0.325 | 0.021 | 0.071 |
| Org Developers | 2021-2022 | 0.330 | 0.018 | 0.076 |
| Org Developers | 2022-2023 | 0.393 | 0.018 | 0.102 |
| Org Developers | 2023-2024 | 0.447 | 0.022 | 0.091 |
| Personal Developers | 2019-2020 | 0.386 | 0.013 | 0.098 |
| Personal Developers | 2020-2021 | 0.415 | 0.012 | 0.109 |
| Personal Developers | 2021-2022 | 0.407 | 0.010 | 0.110 |
| Personal Developers | 2022-2023 | 0.456 | 0.010 | 0.134 |
| Personal Developers | 2023-2024 | 0.472 | 0.011 | 0.111 |

### A.2 Negative Binomial Dispersion (All Years)

| Group | Year | r | CV(λ) | LR Statistic |
|-------|------|-------|-------|--------------|
| All Developers | 2019 | 0.489 | 1.43 | 5.5M |
| All Developers | 2020 | 0.509 | 1.40 | 6.3M |
| All Developers | 2021 | 0.449 | 1.49 | 11.9M |
| All Developers | 2022 | 0.435 | 1.52 | 14.8M |
| All Developers | 2023 | 0.356 | 1.68 | 29.4M |
| All Developers | 2024 | 0.231 | 2.08 | 166.9M |
| Org Developers | 2019 | 0.411 | 1.56 | 0.7M |
| Org Developers | 2020 | 0.422 | 1.54 | 0.9M |
| Org Developers | 2021 | 0.384 | 1.61 | 1.9M |
| Org Developers | 2022 | 0.404 | 1.57 | 1.5M |
| Org Developers | 2023 | 0.314 | 1.78 | 4.5M |
| Org Developers | 2024 | 0.206 | 2.20 | 22.9M |
| Personal Developers | 2019 | 0.509 | 1.40 | 4.7M |
| Personal Developers | 2020 | 0.533 | 1.37 | 5.3M |
| Personal Developers | 2021 | 0.467 | 1.46 | 9.9M |
| Personal Developers | 2022 | 0.445 | 1.50 | 13.2M |
| Personal Developers | 2023 | 0.367 | 1.65 | 24.4M |
| Personal Developers | 2024 | 0.238 | 2.05 | 141.3M |

### A.3 Power Law Bootstrap Confidence Intervals

| Group | Year | α | 95% CI |
|-------|------|-------|-----------------|
| Personal | 2019 | 1.991 | [1.958, 2.031] |
| Personal | 2020 | 1.946 | [1.918, 1.978] |
| Personal | 2021 | 1.860 | [1.839, 2.168] |
| Personal | 2022 | 1.826 | [1.800, 2.163] |
| Personal | 2023 | 1.817 | [1.795, 2.183] |
| Personal | 2024 | 1.779 | [1.765, 2.168] |
| Org | 2019 | 2.037 | [1.955, 2.082] |
| Org | 2020 | 2.063 | [2.024, 2.097] |
| Org | 2021 | 2.075 | [1.960, 2.106] |
| Org | 2022 | 1.911 | [1.882, 2.092] |
| Org | 2023 | 2.055 | [1.827, 2.074] |
| Org | 2024 | 2.037 | [1.967, 2.073] |

*Note: Bootstrap CIs computed via 1,000 resamples following Clauset et al. (2009). Wide intervals for some years reflect uncertainty in xmin threshold selection; despite wide CIs, the overall declining trend in α for personal developers is consistent across all point estimates.*

---

## License

MIT
