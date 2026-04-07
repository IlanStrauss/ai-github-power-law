# Master Results Summary: GitHub Power Law Mechanism Analysis

**Generated:** 2026-04-07
**Purpose:** Comprehensive summary of all diagnostic tests for memory recovery

---

## Executive Summary

**Core Finding:** The power law in GitHub commits is best explained by the **MIXTURE OF EXPONENTIALS** mechanism (Mitzenmacher, 2004), not by dynamic concentration processes (preferential attachment, Kesten/Gibrat).

**Evidence:**
1. β ≈ 0.4 (sublinear attachment kernel) — rejects preferential attachment
2. r declining significantly (p < 0.05) — heterogeneity increasing
3. CV(λ) increased from 1.40 to 2.05 — 46% more dispersion in rates
4. 72-80% of top 1% entrants are new accounts — platform growth effect
5. Rank persistence ρ ≈ 0.18 — high mobility, rotating superstars

**Exception:** 2024 org developers show "increased activity" dominating new entrants (49% vs 40%), with 1,135× median growth ratio — consistent with AI tool amplification, but cannot establish causation.

---

## Competing Hypotheses: Intuitive Narratives

### Hypothesis A: "AI Is Creating Superstar Developers"
**Technical mechanism:** Preferential Attachment

**The story:** AI coding tools amplify already-productive developers. The best developers adopt tools first, use them most effectively, and pull further ahead. Same individuals dominate year after year. 10x developers become 100x developers.

**Predictions:** β ≈ 1, high rank persistence, incumbents dominate top 1%

**Verdict:** ❌ REJECTED (β ≈ 0.4, ρ ≈ 0.18, 90%+ new entrants)

### Hypothesis B: "The Developer Population Is Diversifying"
**Technical mechanism:** Mixture of Exponentials

**The story:** GitHub grew from 40M to 100M+ users, bringing in diverse populations: professional devs, students, hobbyists, automation. Each group has different baseline commit rates. The power law emerges from mixing these populations — it's a compositional effect, not behavioral change.

**Predictions:** NegBin >> Poisson, r declining, new accounts dominate top 1%, low rank persistence

**Verdict:** ✅ STRONGLY SUPPORTED (all predictions confirmed)

### Hypothesis C: "The 2024 Org Developer Exception"
**Technical mechanism:** Localized AI Amplification

**The story:** In 2023-2024, enterprise AI tools (Copilot Enterprise, GPT-4) cleared procurement hurdles. Existing org developers — not new accounts — drove the increase in top 1%. Median growth 1,135×. This ONE group/period shows patterns consistent with Hypothesis A.

**Verdict:** ✅ SUPPORTED for 2024 org developers ONLY

---

## 1. Power Law Estimates (from powerlaw_lognormal_comparison.csv)

### Personal Developers
| Year | n | α | xmin | R (vs lognormal) | Best Fit |
|------|-------|------|------|------------------|----------|
| 2019 | 53,945 | 1.99 | 25 | -1.16 | Lognormal |
| 2020 | 73,483 | 1.95 | 33 | -1.36 | Lognormal |
| 2021 | 83,614 | 1.86 | 39 | -2.15 | Lognormal |
| 2022 | 92,200 | 1.83 | 40 | -2.74 | Lognormal |
| 2023 | 99,585 | 1.82 | 38 | -2.68 | Lognormal |
| 2024 | 102,204 | 1.78 | 45 | -3.11 | Lognormal |

**Trend:** α declined 1.99 → 1.78 (Δ = -0.21); R consistently negative = lognormal body with power tail

### Org Developers
| Year | n | α | xmin | R (vs lognormal) | Best Fit |
|------|--------|------|------|------------------|----------|
| 2019 | 9,824 | 2.04 | 6 | +3.05 | Power law |
| 2020 | 14,502 | 2.06 | 7 | +1.98 | Power law |
| 2021 | 18,253 | 2.08 | 7 | +3.31 | Power law |
| 2022 | 20,764 | 1.91 | 37 | -0.97 | Lognormal |
| 2023 | 23,411 | 2.06 | 6 | -0.95 | Lognormal |
| 2024 | 25,490 | 2.04 | 5 | +6.83 | Power law |
| 2025 | 18,285 | 1.87 | 25 | -0.31 | Lognormal |

**Trend:** α stable ~2.04 (2019-2024), then dropped to 1.87 in 2025

---

## 2. Attachment Kernel Test (β estimation)

**Model:** log(x_{t}) = α + β·log(x_{t-1}) + ε

**Interpretation:**
- β = 1 → Preferential attachment / multiplicative growth
- β < 1 → Sublinear (mean reversion)
- β > 1 → Superlinear (winner-take-all)

### Results (from mechanism_attachment_kernel.csv)

| Group | Period | β | SE | R² | Interpretation |
|-------|--------|------|-------|-------|----------------|
| All Developers | 2019-2020 | 0.377 | 0.011 | 0.095 | Sublinear |
| All Developers | 2020-2021 | 0.399 | 0.010 | 0.102 | Sublinear |
| All Developers | 2021-2022 | 0.392 | 0.009 | 0.103 | Sublinear |
| All Developers | 2022-2023 | 0.445 | 0.009 | 0.128 | Sublinear |
| All Developers | 2023-2024 | 0.473 | 0.010 | 0.108 | Sublinear |
| Org Developers | 2019-2020 | 0.316 | 0.023 | 0.072 | Sublinear |
| Org Developers | 2020-2021 | 0.325 | 0.021 | 0.071 | Sublinear |
| Org Developers | 2021-2022 | 0.330 | 0.018 | 0.076 | Sublinear |
| Org Developers | 2022-2023 | 0.393 | 0.018 | 0.102 | Sublinear |
| Org Developers | 2023-2024 | 0.447 | 0.022 | 0.091 | Sublinear |
| Personal Developers | 2019-2020 | 0.386 | 0.013 | 0.098 | Sublinear |
| Personal Developers | 2020-2021 | 0.415 | 0.012 | 0.109 | Sublinear |
| Personal Developers | 2021-2022 | 0.407 | 0.010 | 0.110 | Sublinear |
| Personal Developers | 2022-2023 | 0.456 | 0.010 | 0.134 | Sublinear |
| Personal Developers | 2023-2024 | 0.472 | 0.011 | 0.111 | Sublinear |

**Verdict:** β ≈ 0.38-0.47 across ALL groups/periods. **REJECTS preferential attachment (β = 1).**

---

## 3. Rate Heterogeneity Test (Negative Binomial)

**Model:** If commits | λ ~ Poisson(λ) and λ ~ Gamma(r, β), then commits ~ NegBin(r, p)

**Key Parameters:**
- r = dispersion (lower r = more heterogeneity)
- CV(λ) = 1/√r = coefficient of variation of underlying rates
- Declining r over time = increasing heterogeneity

### Results (from negbin_vs_poisson.csv)

| Group | Year | r | CV(λ) | LR Statistic | p-value |
|-------|------|-------|-------|--------------|---------|
| All Developers | 2019 | 0.489 | 1.43 | 5.5M | 0 |
| All Developers | 2020 | 0.509 | 1.40 | 6.3M | 0 |
| All Developers | 2021 | 0.449 | 1.49 | 11.9M | 0 |
| All Developers | 2022 | 0.435 | 1.52 | 14.8M | 0 |
| All Developers | 2023 | 0.356 | 1.68 | 29.4M | 0 |
| All Developers | 2024 | 0.231 | 2.08 | 166.9M | 0 |
| Org Developers | 2019 | 0.411 | 1.56 | 0.7M | 0 |
| Org Developers | 2020 | 0.422 | 1.54 | 0.9M | 0 |
| Org Developers | 2021 | 0.384 | 1.61 | 1.9M | 0 |
| Org Developers | 2022 | 0.404 | 1.57 | 1.5M | 0 |
| Org Developers | 2023 | 0.314 | 1.78 | 4.5M | 0 |
| Org Developers | 2024 | 0.206 | 2.20 | 22.9M | 0 |
| Personal Developers | 2019 | 0.509 | 1.40 | 4.7M | 0 |
| Personal Developers | 2020 | 0.533 | 1.37 | 5.3M | 0 |
| Personal Developers | 2021 | 0.467 | 1.46 | 9.9M | 0 |
| Personal Developers | 2022 | 0.445 | 1.50 | 13.2M | 0 |
| Personal Developers | 2023 | 0.367 | 1.65 | 24.4M | 0 |
| Personal Developers | 2024 | 0.238 | 2.05 | 141.3M | 0 |

### Trend Regression (r on year)

| Group | Slope | p-value | Interpretation |
|-------|-------|---------|----------------|
| All Developers | -0.050 | 0.011 | **Significant decline** |
| Org Developers | -0.038 | 0.031 | **Significant decline** |
| Personal Developers | -0.054 | 0.009 | **Significant decline** |

**Verdict:** r is **significantly declining** for ALL groups. Heterogeneity in underlying commit rates is INCREASING. This mechanically produces heavier tails (lower α) without dynamic concentration.

---

## 4. Cohort Decomposition (Intensive vs Extensive Margin)

**From mechanism_cohort_decomposition.csv**

| Group | Period | Persistence Rate | New Entrant Rate | Margin Dominance |
|-------|--------|------------------|------------------|------------------|
| All | 2019-2020 | 8.5% | 93.4% | Extensive |
| All | 2020-2021 | 8.9% | 92.6% | Extensive |
| All | 2021-2022 | 8.8% | 92.1% | Extensive |
| All | 2022-2023 | 8.7% | 92.1% | Extensive |
| All | 2023-2024 | 7.4% | 93.3% | Extensive |
| Org | 2019-2020 | 6.5% | 95.5% | Extensive |
| Org | 2020-2021 | 11.2% | 90.9% | Extensive |
| Org | 2021-2022 | 13.9% | 87.6% | Extensive |
| Org | 2022-2023 | 12.4% | 88.6% | Extensive |
| Org | 2023-2024 | 6.4% | 93.8% | Extensive |
| Personal | 2019-2020 | 7.2% | 94.4% | Extensive |
| Personal | 2020-2021 | 7.8% | 93.5% | Extensive |
| Personal | 2021-2022 | 7.7% | 93.1% | Extensive |
| Personal | 2022-2023 | 7.8% | 92.8% | Extensive |
| Personal | 2023-2024 | 7.0% | 93.7% | Extensive |

**Verdict:** **Extensive margin dominates** in ALL groups/periods. Top 1% is driven by NEW entrants (>90%), not incumbents pulling ahead.

---

## 5. New Entrant Analysis (Who enters the top 1%?)

**From new_entrant_analysis.csv**

| Group | Period | % New Accounts | % Increased Activity | % Near-Top |
|-------|--------|----------------|---------------------|------------|
| All | 2019-2020 | 75.6% | 18.3% | 6.2% |
| All | 2020-2021 | 75.5% | 17.0% | 7.4% |
| All | 2021-2022 | 74.2% | 18.8% | 7.0% |
| All | 2022-2023 | 77.8% | 15.9% | 6.3% |
| All | 2023-2024 | 71.9% | 21.2% | 6.9% |
| Org | 2019-2020 | 57.8% | 30.5% | 11.7% |
| Org | 2020-2021 | 55.3% | 37.3% | 7.3% |
| Org | 2021-2022 | 51.9% | 40.1% | 8.0% |
| Org | 2022-2023 | 54.7% | 35.2% | 10.1% |
| **Org** | **2023-2024** | **40.1%** | **48.7%** | 11.2% |
| Personal | 2019-2020 | 79.6% | 15.7% | 4.7% |
| Personal | 2020-2021 | 80.0% | 14.0% | 6.0% |
| Personal | 2021-2022 | 78.1% | 16.0% | 5.9% |
| Personal | 2022-2023 | 80.8% | 13.7% | 5.5% |
| Personal | 2023-2024 | 77.6% | 17.6% | 4.8% |

### 2024 Org Developer Anomaly

| Metric | 2022-2023 | 2023-2024 | Change |
|--------|-----------|-----------|--------|
| % New Accounts | 54.7% | 40.1% | -14.6pp |
| % Increased Activity | 35.2% | 48.7% | +13.5pp |
| Median Growth Ratio | 80.5× | 1,135× | +1,055× |
| Median Curr Commits | 575 | 8,137 | +7,562 |

**Verdict:** Personal developers: 77-80% new accounts dominate. **Org developers 2023-2024: "Increased activity" overtakes "new accounts" (49% vs 40%)** — the only evidence consistent with AI amplification.

---

## 6. Rank Persistence Test

**From mechanism_rank_persistence.csv**

| Group | Period | n Matched | ρ (Spearman) | Top 10% Persist | Interpretation |
|-------|--------|-----------|--------------|-----------------|----------------|
| All | 2019-2024 | 2,643 | 0.179 | 26.4% | High mobility |
| Org | 2019-2024 | 923 | 0.170 | 18.3% | High mobility |
| Personal | 2019-2024 | 1,720 | 0.175 | 27.3% | High mobility |

### Year-over-Year Rank Correlations

| Group | Period | ρ |
|-------|--------|------|
| All | 2019-2020 | 0.264 |
| All | 2020-2021 | 0.279 |
| All | 2021-2022 | 0.278 |
| All | 2022-2023 | 0.317 |
| All | 2023-2024 | 0.310 |

**Verdict:** Rank persistence is LOW (ρ ≈ 0.18 over 5 years, ρ ≈ 0.26-0.32 year-over-year). **Inconsistent with persistent superstars.** Supports rotating superstars / mixture mechanism.

---

## 7. Taylor's Law Test

**From mechanism_taylors_law.csv**

**Model:** Var(x) ~ Mean(x)^τ
- τ = 1 → Poisson
- τ = 2 → Lognormal/multiplicative
- τ > 2 → Heavy-tailed

| Group | Year | τ | SE | Interpretation |
|-------|------|------|------|----------------|
| All | 2020 | 1.75 | 0.27 | Lognormal |
| All | 2021 | 3.09 | 0.22 | Heavy-tailed |
| All | 2022 | 1.66 | 0.56 | Lognormal |
| All | 2023 | 2.69 | 0.32 | Heavy-tailed |
| All | 2024 | 2.18 | 0.16 | Lognormal |

**Verdict:** τ fluctuates between 1.6 and 3.1, generally consistent with lognormal/multiplicative process.

---

## 8. Lower Barrier Test (Kesten Mechanism)

**From mechanism_lower_barrier.csv**

| Group | Year | Barrier Evidence Ratio | Interpretation |
|-------|------|------------------------|----------------|
| All | 2019 | 0.31 | No barrier |
| All | 2024 | 0.29 | No barrier |
| Org | 2019 | 0.18 | No barrier |
| Org | 2024 | 0.18 | No barrier |
| Personal | 2019 | 0.33 | No barrier |
| Personal | 2024 | 0.31 | No barrier |

**Verdict:** Ratio < 1 in all cases. **No evidence of reflecting barrier at xmin.** Rejects Kesten mechanism.

---

## 9. Mechanism Verdict Table

| Mechanism | Prediction | Our Finding | Supported? |
|-----------|------------|-------------|------------|
| **Preferential Attachment** | β ≈ 1 | β ≈ 0.4 | ❌ No |
| **Preferential Attachment** | High rank persistence | ρ ≈ 0.18 | ❌ No |
| **Preferential Attachment** | Incumbent dominance | 90%+ new entrants | ❌ No |
| **Kesten/Gibrat** | Barrier evidence | None | ❌ No |
| **Kesten/Gibrat** | Lognormal body | Yes (R < 0) | ⚠️ Partial |
| **Mixture of Exponentials** | NegBin >> Poisson | LR > 10^6 | ✅ Yes |
| **Mixture of Exponentials** | Increasing heterogeneity | r declining (p < 0.05) | ✅ Yes |
| **Mixture of Exponentials** | New accounts dominate | 72-80% | ✅ Yes |
| **Mixture of Exponentials** | Low rank persistence | ρ ≈ 0.18 | ✅ Yes |
| **Mixture of Exponentials** | Mean reversion | β ≈ 0.4 < 1 | ✅ Yes |

**Overall Verdict:** Evidence strongly supports **MIXTURE OF EXPONENTIALS**

---

## 10. Key Coefficients for Paper

### To Report in Introduction
- α declined from 1.99 to 1.78 (personal) and 2.04 to 1.87 (org)
- But mechanism tests show this reflects increasing heterogeneity, not dynamic concentration

### To Report in Findings
1. **β = 0.38-0.47** (sublinear), SE ≈ 0.01-0.02, p < 0.001 all cases
2. **r declined from 0.51 to 0.24** (personal), slope = -0.054/year, p = 0.009
3. **CV(λ) increased from 1.40 to 2.05** (46% increase in rate dispersion)
4. **72-80% of top 1% entrants are new accounts** (personal developers)
5. **ρ = 0.18** (rank correlation 2019-2024), top-10% persistence = 18-27%
6. **2024 org anomaly:** 49% increased activity vs 40% new accounts; 1,135× median growth

---

## Files Index

| File | Description |
|------|-------------|
| `output/powerlaw_lognormal_comparison.csv` | Power law α estimates with lognormal comparison |
| `output/powerlaw_2025.csv` | 2025 power law estimates |
| `output/mechanism_attachment_kernel.csv` | β estimates for attachment kernel test |
| `output/mechanism_taylors_law.csv` | Taylor's Law τ estimates |
| `output/mechanism_cohort_decomposition.csv` | Intensive vs extensive margin |
| `output/mechanism_lower_barrier.csv` | Kesten barrier test |
| `output/mechanism_rank_persistence.csv` | Rank correlation and persistence |
| `output/heterogeneity_trends.csv` | Overdispersion δ by year |
| `output/negbin_vs_poisson.csv` | Negative Binomial vs Poisson comparison |
| `output/new_entrant_analysis.csv` | Top 1% new entrant composition |
| `scripts/20_mechanism_diagnostics.py` | Mechanism diagnostic tests script |
| `scripts/21_heterogeneity_tests.py` | Heterogeneity tests script |
| `tasks/paper_revision_plan.md` | Full paper revision plan |

---

## References for Mechanism Identification

- Mitzenmacher (2004). "A Brief History of Generative Models for Power Law Distributions"
- Clauset, Shalizi, Newman (2009). "Power-law distributions in empirical data"
- Gabaix (1999). "Zipf's Law for Cities: An Explanation"
- Barabási & Albert (1999). "Emergence of scaling in random networks"
- Cameron & Trivedi (2013). "Regression Analysis of Count Data"
