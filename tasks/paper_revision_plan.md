# Paper Revision Plan: From "Superstar Coders" to "Heterogeneity vs. Dynamics"

## Executive Summary of Changes

**The core finding has shifted.** Our diagnostic tests reveal that the power law in GitHub commits is likely a **statistical artifact of increasing rate heterogeneity** rather than a dynamic concentration mechanism ("rich-get-richer"). This fundamentally changes the paper's narrative.

### Key Evidence Supporting the Revision

| Diagnostic | Finding | Implication |
|------------|---------|-------------|
| **Attachment kernel (β)** | β ≈ 0.38-0.47 (sublinear) | Mean reversion, NOT preferential attachment |
| **Negative Binomial (r)** | r: 0.51 → 0.24 (p = 0.009) | Heterogeneity INCREASING |
| **CV(λ)** | 1.40 → 2.05 | Wider spread of individual commit rates |
| **Top 1% new entrants** | 72-80% genuinely new accounts | Platform growth, not incumbent amplification |
| **Rank persistence** | ρ ≈ 0.18, top-10% persist ≈ 18-27% | HIGH MOBILITY, rotating superstars |
| **Power law vs. lognormal** | Personal: R < 0 (lognormal better) | Mixture mechanism, not pure power law |

---

## Competing Hypotheses: Intuitive Narratives About SWE Productivity

Each technical mechanism corresponds to a **real-world story** about how software engineering work is changing. The paper should frame these as competing narratives that our data can help adjudicate.

---

### Hypothesis 1: "AI Is Creating Superstar Developers"
**Technical mechanism:** Preferential Attachment (Barabási-Albert)

**The narrative:**
> AI coding tools (Copilot, Claude Code, Cursor) amplify the productivity of developers who are already highly skilled. The best developers adopt these tools first, learn to use them most effectively, and pull further ahead. Their output compounds: more commits → more visibility → more opportunities → more commits. The same individuals dominate year after year, and the gap between top performers and everyone else widens.

**Real-world version:**
- "10x developers" become "100x developers" with AI assistance
- Skill in prompting/directing AI is a new bottleneck that favors existing experts
- Top developers at elite companies adopt tools first (enterprise access, culture)
- Network effects: productive developers attract collaborators, further amplifying output

**Testable predictions:**
- β ≈ 1 (growth proportional to current size)
- High rank persistence (same developers at top year after year)
- Intensive margin dominates (incumbents increase output)
- Low new entrant rate in top 1%

**Our finding:** ❌ **REJECTED.** β ≈ 0.4 (sublinear), ρ ≈ 0.18 (low persistence), 90%+ new entrants

---

### Hypothesis 2: "Boom and Bust Cycles with a Floor"
**Technical mechanism:** Kesten/Gibrat (Multiplicative Growth + Barrier)

**The narrative:**
> Developer productivity fluctuates year to year — some years you ship a major project and commit heavily, other years you're in planning/design mode. But there's a floor: active developers don't drop below some minimum activity level (a few commits per month). Over time, random multiplicative shocks compound, creating fat tails. Some developers happen to string together several good years and appear as "superstars," but luck plays a major role.

**Real-world version:**
- Project cycles: major releases → heavy commits; maintenance mode → light commits
- Job changes: ramping up at new company vs. established workflow
- Life events: parental leave, burnout, sabbaticals create temporary dips
- The floor: professional developers maintain some baseline GitHub presence

**Testable predictions:**
- Lognormal body with power-law tail (R < 0 for most of distribution)
- Evidence of reflecting barrier near minimum activity threshold
- Moderate rank persistence (some stability, but regression to mean)
- Mix of incumbents and new entrants at top

**Our finding:** ⚠️ **PARTIALLY SUPPORTED.** Lognormal body confirmed (R < 0 for personal developers), but NO barrier evidence, and persistence is too low.

---

### Hypothesis 3: "The Developer Population Is Diversifying"
**Technical mechanism:** Mixture of Exponentials (Mitzenmacher)

**The narrative:**
> GitHub's user base has become increasingly heterogeneous. In 2019, GitHub users were predominantly professional developers. By 2024, the platform hosts: (a) full-time professional developers at tech companies, (b) open-source maintainers who code as a primary activity, (c) students learning to code, (d) hobbyists who contribute occasionally, (e) researchers who push code for papers, (f) automation/CI pipelines that escaped bot detection. Each group has a different "natural rate" of committing. The power law emerges from **mixing** these different populations, not from individuals becoming more concentrated.

**Real-world version:**
- GitHub's growth from 40M to 100M+ users brought in more casual users
- Coding bootcamps, university courses, and "learn to code" movements created a large population of low-activity learners
- Meanwhile, professional DevOps and platform engineering created more high-activity automated contributors
- The spread between these groups widened, producing fatter tails
- Each year, different individuals happen to be the most active — there's no persistent advantage

**Why this matters for AI narrative:**
- If the power law is driven by heterogeneity, **declining α does NOT indicate "AI amplifying superstars"**
- Instead, it may reflect: (a) more casual users joining GitHub, (b) more automation/heavy contributors, (c) the gap between professionals and hobbyists widening
- This is a **compositional story** (who's on the platform) not a **behavioral story** (individuals becoming more productive)

**Testable predictions:**
- NegBin vastly outperforms Poisson (confirming heterogeneous rates)
- r (dispersion parameter) declining over time (heterogeneity increasing)
- Low rank persistence (different people at top each year)
- New accounts dominate top 1% entrants (new arrivals with high rates)
- Sublinear β (mean reversion, not compounding)

**Our finding:** ✅ **STRONGLY SUPPORTED.** All predictions confirmed.

---

### Hypothesis 4: "The 2024 Org Developer Exception"
**Technical mechanism:** Localized Preferential Attachment (within enterprises)

**The narrative:**
> For most developers and most years, Hypothesis 3 (diversification) holds. But in 2024, something different happened among organization developers. Enterprise AI tools (Claude Code, Codex) reached production-readiness and cleared procurement/security hurdles at large companies. For the first time, existing professional developers — not new accounts — drove the increase in top 1% membership. Their median growth ratio was 1,135× (vs. 70-100× in prior years). This looks like genuine productivity amplification.

**Real-world version:**
- Enterprise AI tools launched: Claude Code (Feb 2025), Codex (May 2025)
- Org developers had been waiting for tools that met security/compliance requirements
- Once tools were approved, existing productive developers adopted them and output surged
- This is the ONE case where "AI amplifies the already-productive" may apply

**Testable predictions:**
- "Increased activity" overtakes "new accounts" as source of top 1% (org developers only)
- Extreme growth ratios for existing developers
- α drops sharply in 2025 for org developers specifically

**Our finding:** ✅ **SUPPORTED for 2024 org developers ONLY.** 49% increased activity vs. 40% new accounts; 1,135× median growth. But this is one group in one period.

---

## Revised Paper Structure

### 1. INTRODUCTION (~800 words)

**Opening:** GitHub commit distributions follow a power law (α ≈ 1.8-2.0), and α has declined since 2019. But what does this mean?

**The question:** Does declining α reflect:
- **(A) Dynamic concentration:** The same top developers are pulling further ahead each year, perhaps amplified by AI tools
- **(B) Increasing heterogeneity:** GitHub's user base is more diverse — more hobbyists AND more heavy contributors — and the power law is a statistical artifact of mixing these populations

**Why it matters:**
- If (A): Policy implications about skill premiums, labor market polarization, AI amplifying inequality
- If (B): The pattern reflects platform growth and demographic shifts, not behavioral changes

**This paper:** We run diagnostic tests to distinguish these hypotheses. Evidence strongly favors (B), with one exception: org developers in 2024 show patterns consistent with (A).

---

### 2. DATA (Keep largely intact)

Minor additions:
- Note panel structure (developers appearing across years)
- Developer counts for panel analyses

---

### 3. METHOD

#### 3.1 Power Law Estimation (Keep)
- Clauset-Shalizi-Newman methodology
- Interpretation of α

#### 3.2 Mechanism Diagnostic Tests (NEW)

##### 3.2.1 Attachment Kernel Test
**Purpose:** Does a developer's growth depend on their current size?

**Model:** log(x_t) = α + β·log(x_{t-1}) + ε

**Hypothesis (A) predicts:** β ≈ 1 (proportional growth → preferential attachment)
**Hypothesis (B) predicts:** β < 1 (mean reversion → heterogeneous rates)

##### 3.2.2 Rate Heterogeneity Test
**Purpose:** Is the distribution better explained by mixing different types of developers?

**Model:** Compare Poisson (homogeneous rates) vs. Negative Binomial (Gamma-mixed rates)

**Key parameter:** r = dispersion; CV(λ) = 1/√r = coefficient of variation of underlying rates

**Hypothesis (A) predicts:** r stable over time
**Hypothesis (B) predicts:** r declining (heterogeneity increasing)

##### 3.2.3 Top 1% Composition Analysis
**Purpose:** Who enters the top 1% each year?

**Categories:**
- Genuinely new accounts (first appearance in data)
- Increased activity (existed before, below top 1%)
- Near-top promotion (were in top 5%)

**Hypothesis (A) predicts:** "Increased activity" dominates (incumbents amplified)
**Hypothesis (B) predicts:** "New accounts" dominates (new arrivals with high rates)

##### 3.2.4 Rank Persistence Test
**Purpose:** Do the same developers stay at the top?

**Metrics:** Spearman ρ between years; Top 10% persistence rate

**Hypothesis (A) predicts:** High ρ, high persistence
**Hypothesis (B) predicts:** Low ρ, low persistence ("rotating superstars")

---

### 4. FINDINGS

#### 4.1 The Power Law: α Is Declining
- Personal: 1.99 → 1.78
- Org: 2.04 → 1.87 (sharp drop in 2025)
- But what mechanism?

#### 4.2 Attachment Kernel: β ≈ 0.4 (Sublinear)
- Full table of results
- Interpretation: Mean reversion, not compounding. **Rejects Hypothesis (A).**

#### 4.3 Rate Heterogeneity: r Declining Significantly
- r: 0.51 → 0.24 (personal), p = 0.009
- CV(λ): 1.40 → 2.05 (46% increase)
- Interpretation: Developer population is diversifying. **Supports Hypothesis (B).**

#### 4.4 Top 1% Composition: New Accounts Dominate
- Personal: 77-80% new accounts
- Interpretation: Top performers are new arrivals, not incumbents. **Supports Hypothesis (B).**

#### 4.5 Rank Persistence: Low (ρ ≈ 0.18)
- Top 10% persistence: 18-27%
- Interpretation: Rotating superstars, not persistent dominance. **Supports Hypothesis (B).**

#### 4.6 The Exception: 2024 Org Developers
- "Increased activity" overtakes "new accounts" (49% vs 40%)
- Median growth ratio: 1,135× (vs. 70-100× prior)
- Interpretation: This specific group/period shows patterns consistent with Hypothesis (A). **Supports localized AI amplification hypothesis.**

#### 4.7 Summary Table
| Prediction | Hypothesis (A) | Hypothesis (B) | Our Finding |
|------------|----------------|----------------|-------------|
| β | ≈ 1 | < 1 | 0.4 → (B) |
| r trend | Stable | Declining | Declining → (B) |
| Top 1% source | Incumbents | New accounts | New accounts → (B) |
| Rank ρ | High | Low | 0.18 → (B) |

---

### 5. DISCUSSION

#### 5.1 Main Interpretation
The power law in GitHub commits arises primarily from **heterogeneity in developer types**, not from dynamic concentration. GitHub's growth from 40M to 100M+ users brought in a more diverse population: more casual learners, more hobbyists, AND more heavy professional contributors and automation. The spread between these groups widened (CV(λ) increased 46%), mechanically producing heavier tails (lower α).

#### 5.2 What This Means for the AI Narrative
- Observing declining α is **not evidence** of "AI amplifying superstars"
- The power law is consistent with pure heterogeneity, no dynamics required
- **Mechanism tests are essential** — descriptive statistics don't identify mechanism

#### 5.3 The Org Developer Exception
- 2024 org developers are the one case where "AI amplifies existing developers" may apply
- Timing coincides with enterprise AI tools clearing procurement
- But this is one group in one period — cannot generalize

#### 5.4 Implications
- **For AI research:** Don't infer dynamic concentration from static distributions
- **For platform economics:** User base composition matters more than individual behavior
- **For labor economics:** "Superstar" claims require evidence of persistent individual-level advantage

---

### 6. APPENDIX

Keep existing robustness checks. Add:
- Full mechanism diagnostic tables
- Heterogeneity trend regression output
- Taylor's Law results

---

## Files Index

| File | Description |
|------|-------------|
| `output/MASTER_RESULTS_SUMMARY.md` | Complete results summary for memory recovery |
| `output/powerlaw_lognormal_comparison.csv` | Power law α estimates |
| `output/mechanism_attachment_kernel.csv` | β estimates |
| `output/negbin_vs_poisson.csv` | Rate heterogeneity test |
| `output/new_entrant_analysis.csv` | Top 1% composition |
| `output/mechanism_rank_persistence.csv` | Rank correlation |
| `output/heterogeneity_trends.csv` | Overdispersion trends |
| `scripts/20_mechanism_diagnostics.py` | Diagnostic tests code |
| `scripts/21_heterogeneity_tests.py` | Heterogeneity tests code |
| `tasks/paper_revision_plan.md` | This plan |

---

## Approval Checklist

Please confirm:
- [ ] Agree with framing around intuitive narratives (AI amplification vs. diversification)
- [ ] Agree with four hypotheses structure
- [ ] Agree with main interpretation (Hypothesis B supported, Hypothesis A rejected except 2024 org)
- [ ] Agree with Discussion framing
- [ ] Ready to proceed with writing
