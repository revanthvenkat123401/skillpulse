# SkillPulse India: Effective Demand Index (EDI) Methodology
**Document Version:** 1.0.0  
**Methodology Classification:** Algorithmic Labour-Market Demand Normalization  
**Implementation Reference:** `backend/app/services/demand/edi_calculator.py`  
**Governing Standard:** SIH26246 Literal Requirements Compliance  

---

## 1. Executive Overview & Problem Formulation

Traditional workforce development policies rely on unweighted job portal aggregations or retrospective periodic employer surveys. In digital job exchanges, raw posting counts suffer from systemic distortions:
1. **Syndication and Reposting Duplication:** Up to 35% of listings represent multi-board scraping syndication or recurrent re-postings by recruitment agencies.
2. **Ghost Vacancies and Low Persistence:** Postings remaining open for under a week frequently represent speculative talent pipelining rather than executable job offers.
3. **Employer Monopsony Distortion:** A sudden hiring surge by a single large employer (e.g., a regional warehouse opening) creates an artificial deficit signal that does not represent broad, resilient market absorption.
4. **Low Information Quality:** Listings omitting salary bands, educational prerequisites, or verified corporate credentials carry low placement realization rates.

To address these distortions, **SkillPulse India** implements the **Effective Demand Index (EDI)**: a normalized, flow-consistent metric measuring **genuine, persistent, and diversified localized labor demand** in units of $[\text{openings / month}]$.

---

## 2. Mathematical Formulation

The Effective Demand Index for a given district $d$, canonical skill $s$, and monthly observation window $t$ is computed as:

$$\text{EDI}_{d,s,t} = V_{d,s,t} \times \delta_{\text{dedup}} \times M_{\text{persist}} \times M_{\text{div}} \times Q$$

Where:
* $V_{d,s,t} \in \mathbb{Z}_{\ge 0}$: Raw observed monthly posting volume $[\text{openings / month}]$.
* $\delta_{\text{dedup}} \in [0.70, 0.95]$: Scraper deduplication and syndication discount factor.
* $M_{\text{persist}} \in [0.50, 1.50]$: Vacancy tenure persistence multiplier.
* $M_{\text{div}} \in [0.60, 1.00]$: Employer diversity multiplier based on the Herfindahl-Hirschman Index (HHI).
* $Q \in [0.50, 1.00]$: Composite listing quality and transparency score.

---

## 3. Component Definitions & Parameter Bounds

### 3.1 Raw Posting Volume ($V$)
* **Definition:** The raw count of distinct job advertisements captured by input adapters for occupation $s$ within district $d$ during month $t$.
* **Dimension:** $[\text{openings / month}]$.
* **Boundary Guard:** If $V \le 0$, the engine immediately returns $\text{EDI} = 0.0$ and skips multiplier processing.

### 3.2 Deduplication Factor ($\delta_{\text{dedup}}$)
* **Definition:** Discounts duplicate job postings identified across syndication networks, staffing agency re-postings, and cross-portal scraping.
* **Mathematical Bound:** Clamped to $[0.70, 0.95]$.
* **Default Baseline:** $0.88$ (reflecting an empirical 12% cross-portal syndication rate).

### 3.3 Vacancy Persistence Multiplier ($M_{\text{persist}}$)
* **Rationale:** A vacancy that remains unfilled for 30+ days reflects structural talent scarcity, whereas vacancies that disappear in 5 days reflect transient or speculative postings.
* **Formulation:**
  $$M_{\text{persist}} = \min\left(1.50, \max\left(0.50, \frac{\bar{T}_{\text{tenure}}}{30.0}\right)\right)$$
  Where $\bar{T}_{\text{tenure}}$ is the average active tenure of vacancies in days.
* **Interpretation:**
  - $\bar{T}_{\text{tenure}} = 15 \text{ days} \implies M_{\text{persist}} = 0.50$ (50% penalty for ephemeral postings).
  - $\bar{T}_{\text{tenure}} = 30 \text{ days} \implies M_{\text{persist}} = 1.00$ (Neutral baseline).
  - $\bar{T}_{\text{tenure}} \ge 45 \text{ days} \implies M_{\text{persist}} = 1.50$ (50% boost for persistent structural shortages).

### 3.4 Employer Diversity Multiplier ($M_{\text{div}}$)
* **Rationale:** Skilling quotas should not overreact to a single firm's hiring drive. The market should demonstrate broad-based recruitment across multiple employers.
* **Formulation:**
  1. Calculate the market share $s_i = v_i / V$ for each unique employer $i$.
  2. Compute the Herfindahl-Hirschman Index:
     $$\text{HHI} = \sum_{i=1}^{N} s_i^2 \in (0, 1.0]$$
  3. When individual employer shares are unobserved, HHI is approximated symmetrically:
     $$\text{HHI} \approx \min\left(1.0, \max\left(0.01, \frac{1.0}{N_{\text{employers}}}\right)\right)$$
  4. Compute the Diversity Multiplier:
     $$M_{\text{div}} = \min(1.00, \max(0.60, 1.0 - 0.4 \times \text{HHI}))$$
* **Interpretation:**
  - Highly diversified market ($N \ge 25 \implies \text{HHI} \le 0.04$): $M_{\text{div}} \approx 0.98 - 1.00$ (Near zero discount).
  - Monopoly buyer ($N = 1 \implies \text{HHI} = 1.00$): $M_{\text{div}} = 0.60$ (40% discount to protect against monopsony volatility).

### 3.5 Posting Quality Score ($Q$)
* **Rationale:** Evaluates listing rigor based on salary disclosure, employer verification, and explicit NSQF role level linkage.
* **Mathematical Bound:** Clamped to $[0.50, 1.00]$.
* **Default Baseline:** $0.85$.

---

## 4. End-to-End Worked Example

Consider a sample monthly observation for **AI & Computer Vision Data Annotator** in **Bengaluru Urban**:

| Parameter | Observed Input Value | Multiplier Derivation | Effective Component |
|---|---|---|---|
| **Raw Volume ($V$)** | $450 \text{ postings}$ | Direct count | $450$ |
| **Deduplication ($\delta$)** | Default $0.88$ | Clamped in $[0.70, 0.95]$ | $0.88$ |
| **Average Tenure ($\bar{T}$)** | $35.0 \text{ days}$ | $\min(1.50, \max(0.50, 35.0 / 30.0)) = 1.167$ | $1.167$ |
| **Unique Employers ($N$)** | $120 \text{ firms}$ | $\text{HHI} \approx 1 / 120 = 0.0083 \implies 1.0 - (0.4 \times 0.0083) = 0.997$ | $0.997$ |
| **Quality Score ($Q$)** | $0.89$ | Clamped in $[0.50, 1.00]$ | $0.89$ |

### Computation:
$$\text{EDI} = 450 \times 0.88 \times 1.167 \times 0.997 \times 0.89$$
$$\text{EDI} = 450 \times 0.9138 \approx \mathbf{410.8} \quad [\text{openings / month}]$$

*Interpretation:* The raw volume of 450 postings is discounted by syndication and quality factors, but bolstered by high persistence and strong employer diversity, yielding an effective demand flow of **410.8 qualified openings per month**.

---

## 5. Data Governance & Status Attribution

In accordance with SIH data governance standards, every EDI computation is tagged with its provenance status:
* `REAL`: Sourced directly from official authorized government exchanges (e.g., NCS API integration).
* `DERIVED`: Computed via the EDI formula from verified empirical signals.
* `SYNTHETIC`: Generated by seed-controlled deterministic scenario models during prototype simulation.

---

## 6. Missing-Data & Sparse Series Handling

When monthly observations are missing or sparse:
1. **Tenure Imputation:** If $\bar{T}_{\text{tenure}}$ is unavailable, it defaults to the sector-level historical average (typically 28.5 days).
2. **Employer Count Imputation:** If $N$ is omitted, it is approximated as $\max(1, \lfloor V / 3.5 \rfloor)$.
3. **Sparse Flagging:** If the 24-month observation density drops below 18 points, the downstream Confidence Engine automatically degrades the confidence score and sets `low_data_flag: true`.

---

## 7. Methodological Limitations

1. **Informal Sector Boundary:** EDI captures formalized, digitally accessible job openings. Unorganized day-wage construction or agricultural labor is not represented in digital postings.
2. **Syndication Variance:** The baseline deduplication factor ($0.88$) is uniform across sectors; in specialized IT niches, deduplication may reach $0.75$, while in local healthcare it may exceed $0.95$.
3. **No Direct Causal Inference:** EDI represents effective vacancy flow rate, not econometric causal proof of industry expansion.

---

## 8. Heterogeneous Demand Source Ingestion Architecture

In production environments, demand signals originate across heterogeneous public exchanges and employer reporting channels. The platform normalizes these streams into a common schema before computing the EDI:

```text
Source A: National Career Service (NCS) Feed [Public exchange, NCO coded]
Source B: Direct Industry Requisitions Feed [Private cluster requisitions]
                  ↓
       Common Normalized Schema
 (value, unit, period, data_status, source_or_method, persistence, employer_id)
                  ↓
    EDI-Compatible Aggregated Demand
   (Source provenance & contributing streams preserved)
                  ↓
     Effective Demand Index (EDI)
```

### Unsupported / Unavailable Sources Disclosure
1. **e-Shram:** e-Shram is a national registry of unorganized worker profiles (labour supply stock), not an active hiring exchange. It does not emit employer vacancy postings and cannot be treated as a demand source.
2. **Commercial Job Boards (LinkedIn, Naukri):** Commercial scraping without express platform authorization violates Terms of Service. In enterprise production, these streams must be connected via authorized enterprise APIs or government MoUs.

---

## 9. Two-Sided Severity Formulation & Regulatory Status Bands

To support actionable decision-making across both talent deficits and talent surpluses, SkillPulse India implements a signed, continuous mismatch severity metric:

$$\text{Severity} = \frac{\text{Demand} - \text{Supply}}{\max(\text{Demand}, \text{Supply}, 1.0)} \in [-1.0, +1.0]$$

### 9.1 Regulatory Status Classification Bands

| Status Band | Mathematical Condition | Regulatory Meaning & Prescriptive Action |
|---|---|---|
| **ACUTE_SHORTAGE** | $\text{Severity} \ge +0.40$ (or Net Gap $\ge +150$) | Severe talent deficit. Urgent seat sanction expansion & mobilization required. |
| **MODERATE_SHORTAGE** | $+0.12 \le \text{Severity} < +0.40$ | Emerging deficit. Targeted short-cycle upskilling and trainer augmentation advised. |
| **BALANCED** | $-0.12 \le \text{Severity} \le +0.12$ | Equilibrium. Maintain existing replacement capacity and curriculum standards. |
| **MODERATE_OVERSUPPLY** | $-0.40 < \text{Severity} \le -0.12$ | Mild surplus. Monitor placement rates and slow additional batch mobilization. |
| **ACUTE_OVERSUPPLY** | $\text{Severity} \le -0.40$ (or Net Gap $\le -50$) | Acute trainee saturation. Divert training capacity to adjacent shortage trades. |

### 9.2 Early-Warning Horizon & Lead-Time Definition
* **Lead-Time Definition:** *The first future month ($M+\tau$, where $\tau \ge 1$, or $\tau = 0$ for active) in which the signed monthly gap crosses the applicable warning threshold.*
* **Shortage Warning Trigger:** Projected gap $\ge +150.0 \text{ openings/month}$ or Severity $\ge +0.40$.
* **Saturation Warning Trigger:** Projected gap $\le -50.0 \text{ openings/month}$ or Severity $\le -0.40$.
* **Lead-Time $\tau = 0$:** Threshold already breached in current observation period (immediate policy intervention required).
* **Lead-Time $\tau = -1$:** Stable equilibrium maintained across the entire forecast projection horizon.

