# Power Laws in GitHub Commits: A growing, competitive, and concentrated ecosystem 

## 1. Introduction

Concentration and inequality have risen across many domains — income, wealth, firm size, scientific citations, social media followers. A natural interpretation is that these patterns reflect *preferential attachment*: the "rich-get-richer" mechanism in which initial advantages compound over time (Barabási & Albert, 1999). The spread of AI coding assistants since 2022 — GitHub Copilot, ChatGPT, Cursor — has sharpened this concern for software development. If the best developers adopt AI first and use it most effectively, initial skill differences could compound into large and persistent gaps.

But rising inequality does not necessarily imply preferential attachment. As Strauss and Yang (2025) note, observationally identical concentration patterns can arise from simply mixing populations with different underlying rates — no dynamics required (Mitzenmacher, 2004). Distinguishing these mechanisms requires more than documenting a power law; it requires testing how individuals actually behave over time.

**This paper asks:** does rising concentration in GitHub commit activity reflect "rich-get-richer" dynamics — consistent with AI amplifying existing human capital — or is it a statistical artifact of an increasingly heterogeneous user base?

---

We frame the question around two competing hypotheses with distinct empirical implications.

**Hypothesis A — AI Amplifies Human Capital.** AI tools are complementary to existing expertise. Developers who already possess deep skill adopt tools earlier, prompt them better, and integrate outputs more effectively. The result is *dynamic concentration*: the same top performers pull further ahead each year. Under this hypothesis, we expect high rank persistence, incumbent developers driving output growth, and individual productivity compounding over time ($\beta \approx 1$ in the attachment kernel).

**Hypothesis B — Platform Growth Creates Statistical Concentration.** What looks like "superstar" concentration is a compositional artifact of who joins and leaves the platform. GitHub grew from 40 million to over 100 million users between 2019 and 2024, bringing in students, hobbyists, researchers, and automation pipelines alongside professional developers. Mixing these groups — each with different baseline commit rates — mechanically produces heavy-tailed distributions. Under this hypothesis, we expect low rank persistence, new accounts dominating the top, and individual productivity reverting toward the mean ($\beta < 1$).

---

GitHub provides a natural laboratory to test these hypotheses. The platform records every code contribution, and a *commit* — a saved change to a repository — is a direct, continuous measure of individual output unavailable in most labor markets. We track over 48,000 developers from 2019 to 2024 and run four diagnostic tests: attachment kernel estimation, rate heterogeneity trends, top-performer composition analysis, and rank persistence measurement.

Commit distributions follow a power law throughout, with the exponent $\alpha$ declining from 2.0 to 1.8 — concentration increased. But the diagnostics point clearly to Hypothesis B.

The attachment kernel coefficient $\beta \approx 0.4$ indicates mean reversion, not compounding advantage. The dispersion of underlying commit rates widened substantially, consistent with a more heterogeneous user base rather than individual productivity pulling away. Among personal developers, 72–80% of top 1% entrants each year are genuinely new accounts — superstars who arrive with high baseline rates rather than climb through cumulative advantage. And the five-year rank correlation between 2019 and 2024 is just $\rho \approx 0.18$: the superstars of 2019 are largely not the superstars of 2024.

There is one important exception. Among *organization* developers in 2023–2024, "increased activity" overtook "new accounts" as the dominant source of top 1% entrants, with a median year-on-year growth ratio of 1,135× — compared with 70–100× in prior years. This is the only pattern in our data consistent with Hypothesis A, and its timing coincides with enterprise AI tools clearing procurement and security hurdles at large firms. We cannot establish causation, but the signal is distinct.

---

These findings contribute to three bodies of work. We add to the power law and preferential attachment literature (Barabási & Albert, 1999; Gabaix, 2009) by providing the first systematic mechanism-diagnostic analysis of software productivity — moving beyond documenting concentration to identifying its source. We extend the emerging literature on AI and labor outcomes (Noy and Zhang, 2023; Peng et al., 2023) by examining distributional effects at platform scale using naturally occurring behavioral data across six years. And we speak to the skill-biased technological change literature (Acemoglu and Restrepo, 2018; Rosen, 1981): for most developers, the mechanism producing concentration is closer to Mitzenmacher's compositional account than to compounding advantage predicted by SBTC models.

The policy stakes depend on this distinction. If AI amplifies existing human capital through preferential attachment, the pattern should persist and intensify — a winner-take-all dynamic warranting concern about access and equity. If instead the pattern reflects compositional change, it may moderate as platform growth slows. The organization developer exception suggests that enterprise AI adoption may yet produce the compounding advantages that the broader data do not yet show.

The remainder of the paper is organized as follows. Section 2 develops the theoretical framework. Section 3 describes the data. Section 4 presents the power law estimates. Section 5 reports the diagnostic tests. Section 6 examines the organization developer exception. Section 7 concludes.


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

We estimate power law exponents following the Clauset-Shalizi-Newman (2009) methodology. This approach first determines the threshold $x_{\min}$ where power law behavior begins, using the Kolmogorov-Smirnov statistic to find the value that minimizes the distance between the empirical distribution and the fitted power law. For observations above this threshold, we estimate the exponent $\alpha$ via maximum likelihood:

$$\hat{\alpha} = 1 + n \left[ \sum_{i=1}^{n} \ln \frac{x_i}{x_{\min}} \right]^{-1}$$

We then compare the power law fit to an alternative log-normal distribution using a likelihood ratio test, yielding the $R$ statistic. When $R > 0$, the power law fits better; when $R < 0$, the log-normal fits better. Values of $|R| > 2$ indicate statistically significant differences at conventional levels.

The exponent $\alpha$ determines the tail behavior of the distribution. When $\alpha > 2$, the distribution has finite variance and the sample mean converges reliably. When $\alpha < 2$, the variance is infinite and the sample mean is dominated by extreme observations. Lower values of $\alpha$ indicate heavier tails and greater concentration of output among top contributors.

### 3.2 Mechanism Diagnostic Tests

Power law estimation tells us that concentration is increasing, but not why. Two mechanisms can produce identical power law exponents: dynamic concentration (where advantages compound over time) and static heterogeneity (where mixing different population types creates heavy tails). We implement four diagnostic tests to distinguish these mechanisms.

#### 3.2.1 Attachment Kernel Test

The attachment kernel test asks whether a developer's growth rate depends on their current size. We regress log commits in year $t$ on log commits in year $t-1$ for developers appearing in both years:

$$\log(x_{i,t}) = \alpha + \beta \cdot \log(x_{i,t-1}) + \varepsilon_{i,t}$$

where $x_{i,t}$ denotes developer $i$'s commits in year $t$. The coefficient $\beta$ reveals the nature of the growth process. When $\beta \approx 1$, growth is proportional to current size — the "rich-get-richer" pattern characteristic of preferential attachment (Barabási & Albert, 1999). When $\beta < 1$, growth is sublinear, indicating mean reversion: highly productive developers in one year tend to regress toward average productivity the next. When $\beta > 1$, growth is superlinear, implying accelerating winner-take-all dynamics.

#### 3.2.2 Rate Heterogeneity Test

The rate heterogeneity test asks whether the distribution is better explained by mixing developers with different underlying productivity rates. Under a homogeneous model, all developers share a common commit rate $\lambda$, and commits follow a Poisson distribution:

$$X_i \sim \text{Poisson}(\lambda)$$

Under a heterogeneous model, each developer $i$ has their own underlying rate $\lambda_i$, drawn from a Gamma distribution with shape parameter $r$ and rate parameter $\beta$:

$$\lambda_i \sim \text{Gamma}(r, \beta)$$
$$X_i \mid \lambda_i \sim \text{Poisson}(\lambda_i)$$

Marginalizing over the unobserved rates yields the Negative Binomial distribution:

$$X_i \sim \text{NegBin}(r, p) \quad \text{where } p = \frac{\beta}{1+\beta}$$

The dispersion parameter $r$ measures heterogeneity: lower values indicate greater variation in underlying rates across developers. The coefficient of variation of the underlying rates is $\text{CV}(\lambda) = 1/\sqrt{r}$. When $r$ declines over time, heterogeneity is increasing — the spread between high-rate and low-rate developers is widening. This increasing dispersion mechanically produces heavier tails without any dynamic concentration process (Mitzenmacher, 2004).

#### 3.2.3 Top 1% Composition Analysis

The composition analysis asks who enters the top 1% each year. For each year-over-year transition, we classify new top-1% entrants into three categories: genuinely new accounts appearing in the data for the first time, increased activity from developers who existed in the prior year but below the top 1% threshold, and near-top promotions from developers who were in the top 5% but not top 1% in the prior year.

If "new accounts" dominates, top performance reflects platform growth — new arrivals with high baseline rates entering the sample. If "increased activity" dominates, existing developers are being amplified, consistent with AI tools boosting incumbent productivity.

#### 3.2.4 Rank Persistence Test

The rank persistence test asks whether the same developers stay at the top over time. We compute the Spearman rank correlation $\rho$ between developers' commit rankings across years, and the persistence rate — the fraction of developers in the top 10% in year $t$ who remain in the top 10% in year $t+k$.

High rank correlation and high persistence indicate persistent superstars, consistent with preferential attachment where early advantages compound. Low rank correlation and low persistence indicate rotating superstars, consistent with heterogeneous rates where different developers happen to be most productive each year based on idiosyncratic factors.

---

## 4. Findings

### 4.1 Power Law Estimates: α Is Declining

We begin by documenting the basic pattern: concentration in GitHub commits has increased over our sample period. Table 1 presents power law exponent estimates by developer type.

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

For personal developers, the power law exponent $\alpha$ declined steadily from 1.99 in 2019 to 1.78 in 2024 — a decrease of 0.21 over five years. This shift is economically meaningful: at $\alpha = 2.0$, the top 1% of developers account for roughly 25% of total commits; at $\alpha = 1.8$, this share rises to approximately 35%. The negative $R$ statistics throughout indicate that the body of the distribution is better described by a log-normal, with power law behavior emerging only in the extreme tail — a pattern consistent with multiplicative growth processes.

For organization developers, the pattern differs. The exponent remained stable around $\alpha = 2.04$ through 2024, then dropped sharply to 1.87 in 2025 — a decline of 0.17 in a single year. The positive $R$ values in early years indicate a purer power law fit, suggesting different underlying dynamics for professional developers contributing to organizational repositories.

These estimates establish that concentration increased, but they do not reveal why. A declining $\alpha$ is consistent with both Hypothesis A (AI amplifying superstars) and Hypothesis B (increasing heterogeneity in who participates). We now turn to diagnostic tests designed to distinguish these mechanisms.

### 4.2 Attachment Kernel: β ≈ 0.4 (Sublinear Growth)

The attachment kernel test directly examines whether productivity advantages compound over time. If AI tools create persistent superstars through a "rich-get-richer" mechanism, we should observe $\beta \approx 1$: developers who are twice as productive this year should be twice as productive next year. Table 2 reports the estimated coefficients.

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

The coefficient $\beta$ ranges from 0.32 to 0.47 across all periods and groups, significantly below unity in every case ($p < 0.001$). To interpret the magnitude: a coefficient of $\beta = 0.4$ implies that a developer with 10× the commits of another developer experiences only $10^{0.4} \approx 2.5\times$ the expected growth, not $10\times$ as preferential attachment would predict. The relationship between current position and future growth is sharply sublinear.

This pattern indicates mean reversion rather than cumulative advantage. Developers who are highly productive in year $t$ tend to regress toward average productivity in year $t+1$. A developer in the 99th percentile this year is more likely to fall than to maintain their position. Productivity advantages do not compound over time; if anything, they dissipate.

The finding has important implications for the "AI superstar" hypothesis. If AI tools were creating persistent advantages for top developers, we would expect $\beta$ to approach or exceed unity, with early adopters pulling further ahead each year. Instead, the consistently sublinear coefficients suggest that whatever drives a developer to the top of the distribution in one year — whether AI tools, a major project deadline, or simply having more time to code — does not persist into the following year. This is inconsistent with Hypothesis A and consistent with Hypothesis B, where different individuals happen to be most productive each year based on transient factors.

### 4.3 Rate Heterogeneity: Increasing Dispersion in Underlying Rates

The rate heterogeneity test examines whether the observed concentration reflects mixing different types of developers with different baseline productivity rates. If the Negative Binomial provides a substantially better fit than the Poisson, this confirms that developers are not homogeneous — they have genuinely different underlying commit rates. More importantly, if the dispersion parameter $r$ is declining over time, heterogeneity is increasing, which mechanically produces heavier tails without any dynamic "rich-get-richer" process.

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

| Group | Slope | SE | p-value |
|-------|-------|-----|---------|
| Personal Developers | −0.054 | 0.014 | 0.009 |
| Org Developers | −0.038 | 0.012 | 0.031 |
| All Developers | −0.050 | 0.013 | 0.011 |

The likelihood ratio statistics are enormous — in the millions — with $p$-values effectively zero. The Negative Binomial provides a vastly better fit than the Poisson, confirming substantial heterogeneity in underlying commit rates. Developers are not drawing from a common distribution; they have fundamentally different baseline productivities.

More striking is the trend in $r$ over time. For personal developers, the dispersion parameter fell from 0.509 in 2019 to 0.238 in 2024 — a 53% decline that is statistically significant ($p = 0.009$). Since the coefficient of variation of underlying rates is $\text{CV}(\lambda) = 1/\sqrt{r}$, this corresponds to an increase from 1.40 to 2.05 — a 46% widening in the spread of individual productivity rates.

What does this mean substantively? In 2019, the typical deviation from mean productivity was about 1.4 times the mean itself. By 2024, it was 2.05 times the mean. The developer population became more heterogeneous: the gap between high-rate professionals and low-rate casual users widened. This widening dispersion mechanically produces heavier tails in the commit distribution — the power law exponent $\alpha$ declines — without requiring any dynamic concentration mechanism. The "superstars" we observe may simply be the high-rate tail of an increasingly dispersed mixture, not individuals who accumulated advantages over time.

This finding strongly supports Hypothesis B. The observed concentration is consistent with a compositional story: GitHub's user base became more diverse between 2019 and 2024, mixing more casual users (students, hobbyists, researchers) with more heavy professional contributors. The statistical signature of this mixing is declining $r$ and increasing $\text{CV}(\lambda)$ — exactly what we observe.

### 4.4 Top 1% Composition: Who Reaches the Top?

A critical question for distinguishing our hypotheses is: who enters the top 1% each year? Under Hypothesis A (AI amplifying superstars), we expect existing developers to increase their output and dominate the top tier — the "intensive margin." Under Hypothesis B (compositional change), we expect new arrivals with high baseline rates to dominate — the "extensive margin." Table 4 decomposes top 1% entrants by source.

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

For personal developers, the pattern is striking and consistent: genuinely new accounts comprise 77-80% of top 1% entrants in every period. Only 14-18% reach the top by increasing their activity from a prior year. This means that the "superstars" we observe at the top of the distribution are predominantly new arrivals to the platform who entered with high commit rates, not existing developers who climbed the ladder over time.

This finding is difficult to reconcile with Hypothesis A. If AI tools were amplifying incumbent developers, we would expect "increased activity" to dominate as existing developers boosted their productivity. Instead, the extensive margin dominates: platform growth brings in new high-rate contributors who immediately appear in the top tier. The superstars are not being created through cumulative advantage — they arrive fully formed.

For organization developers, the pattern is different. Across 2019-2023, new accounts comprised 52-58% of top 1% entrants, with increased activity accounting for 30-40% — a more balanced composition. But in 2023-2024, a notable shift occurs: "increased activity" overtakes "new accounts" for the first time, with 48.7% of top 1% entrants being existing developers who increased their output versus only 40.1% new accounts.

This is the only group/period combination where the intensive margin dominates. We examine this anomaly in detail in Section 4.6, as it may reflect genuine AI amplification effects among professional developers with access to enterprise coding tools.

### 4.5 Rank Persistence: The Rotating Cast of "Superstars"

The final diagnostic asks whether the same developers remain at the top over time. Under Hypothesis A, we expect high rank persistence: superstars who pull ahead should stay ahead, their advantages compounding year after year. Under Hypothesis B, we expect low persistence: different individuals should occupy top positions each year, reflecting idiosyncratic variation in commit rates rather than persistent individual advantages.

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

The five-year rank correlation between 2019 and 2024 commit levels is remarkably low: $\rho \approx 0.18$ for all groups. To interpret this magnitude: if rank positions were perfectly persistent, $\rho = 1$; if they were completely random, $\rho = 0$. A correlation of 0.18 indicates that knowing a developer's 2019 productivity tells you almost nothing about their 2024 productivity. Only 18-27% of developers in the top 10% in 2019 remained in the top 10% in 2024 — roughly what we would expect by chance.

Year-over-year correlations are somewhat higher, ranging from 0.22 to 0.33, but still indicate substantial churning. Even in the short run, top positions are not stable. The developers dominating GitHub output this year are mostly different from those who dominated last year.

This finding is inconsistent with the "persistent superstars" narrative. If AI tools were creating durable advantages for top developers — allowing them to pull further ahead each year — we would expect high rank persistence. Instead, we observe a rotating cast of top performers. The superstars of 2019 are largely not the superstars of 2024. This pattern is precisely what we would expect under Hypothesis B: each year, developers' commit counts reflect draws from their underlying rate distributions, with substantial idiosyncratic variation. A developer with a high underlying rate may have a productive year (major project, deadline pressure, more time to code) and appear in the top tier, then regress toward their mean the following year.

### 4.6 The Exception: Organization Developers in 2023-2024

One finding stands apart from the pattern supporting Hypothesis B, and it deserves careful attention as potential evidence of AI-driven productivity amplification.

**Table 6: Org Developer Top 1% Entrants — Growth Patterns**

| Period | Median Prior Commits | Median Current Commits | Median Growth Ratio |
|--------|---------------------|------------------------|---------------------|
| 2019-2020 | 9.5 | 581 | 73× |
| 2020-2021 | 8.0 | 682 | 97× |
| 2021-2022 | 9.0 | 751 | 80× |
| 2022-2023 | 8.0 | 575 | 80× |
| **2023-2024** | 6.0 | **8,137** | **1,135×** |

The numbers are striking. Among organization developers entering the top 1% in 2023-2024, the pattern breaks sharply from all prior years. For the first time, "increased activity" (48.7%) overtook "new accounts" (40.1%) as the dominant source of top 1% entrants. The median commit count among top 1% entrants jumped from 575 to 8,137 — a 14-fold increase in a single year. And the median growth ratio — how much these developers increased their output compared to the prior year — was 1,135×, versus 73-97× in all prior periods.

To be concrete about what this means: in prior years, a typical organization developer entering the top 1% had committed about 8 times the previous year, going from roughly 80 commits to roughly 650. In 2023-2024, the typical top 1% entrant had committed over 1,100 times what they committed the prior year, going from roughly 6 commits to over 8,000. This is not a modest increase — it is a transformation.

The timing is suggestive. GitHub Copilot launched for individuals in June 2022 and Copilot for Business in February 2023, but enterprise adoption was initially limited by security and compliance concerns. Copilot Enterprise launched in February 2024, offering organization-wide deployment with enhanced security features, code referencing controls, and enterprise SSO integration. ChatGPT (November 2022) and GPT-4 (March 2023) had already demonstrated powerful coding capabilities, and by late 2023, many enterprises had completed the procurement and security review processes necessary for deployment.

Organization developers — those contributing to repositories owned by major companies and foundations — are precisely the group we would expect to adopt enterprise AI tools first. They work in professional contexts with IT departments, procurement processes, and security requirements. When these barriers cleared in late 2023 and early 2024, this group gained access to AI coding assistants that individual and personal developers had been using for over a year.

The 2023-2024 org developer pattern is the only evidence in our data consistent with Hypothesis A — existing productive developers being amplified by technology rather than new arrivals dominating the top tier. The timing aligns with enterprise AI tool adoption. The magnitude of the growth ratios (1,135× vs. 73-97×) suggests something qualitatively different occurred in this period.

However, we emphasize important caveats. This is one group (organization developers) in one period (2023-2024). We cannot observe AI tool usage directly, only timing correlations. The pattern could reflect other factors: enterprise workflow changes, pandemic-era project accumulation being released, or sampling artifacts. Establishing causation would require individual-level data on tool adoption, which we do not have. We present this finding as suggestive evidence that warrants further investigation, not as proof that AI tools amplified incumbent superstars.

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
- Barabási, A.-L., & Albert, R. (1999). "Emergence of scaling in random networks." *Science*, 286(5439), 509-512.
- Clauset, A., Shalizi, C. R., & Newman, M. E. J. (2009). "Power-law distributions in empirical data." *SIAM Review*, 51(4), 661-703.
- Mitzenmacher, M. (2004). "A brief history of generative models for power law and lognormal distributions." *Internet Mathematics*, 1(2), 226-251.
- Newman, M. E. J. (2005). "Power laws, Pareto distributions and Zipf's law." *Contemporary Physics*, 46(5), 323-351.
- Strauss, I., & Yang, J. (2025). "Distinguishing preferential attachment from heterogeneity in heavy-tailed distributions." Working paper.

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
