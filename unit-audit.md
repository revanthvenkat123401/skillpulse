# SkillPulse India: Unit & Dimensional Audit Report
**Document Version:** 1.0.0  
**Audit Gate:** Milestone 8.1 — Unit & Dimensional Integrity  
**Scope:** Complete verification of dimensions, accounting periods, and stock-flow consistency across the pipeline:  
$$\text{EDI} \longrightarrow \text{Active Supply} \longrightarrow \text{Funnel Lag} \longrightarrow \text{Net Gap} \longrightarrow \text{Forecast} \longrightarrow \text{Optimizer}$$

---

## 1. Executive Summary

This audit establishes whether the mathematical and computational quantities in **SkillPulse India** are dimensionally sound, temporally aligned, and stock/flow consistent.

### Core Audit Verdict: **DIMENSIONALLY SOUND**
1. **Demand Metric (EDI):** Is a **monthly demand flow** ($\text{openings / month}$).
2. **Supply Metric (Effective Active Supply):** Is a **monthly supply flow** ($\text{job-ready entrants / month}$) representing retained cohort graduates entering the local labor pool.
3. **Workforce Stock Indicator (`total_workforce_est`):** Is preserved as a **static stock indicator** ($\text{workers}$) and is **never** directly subtracted from monthly vacancy flows.
4. **Net Gap:** Computes the net monthly flow imbalance:  
   $$\text{Net Gap} = \text{EDI} - \text{Effective Active Supply} \quad [\text{openings / month}]$$
5. **Cohort Activation Lag ($T + \tau$):** Strictly models pipeline delay in discrete monthly intervals ($\tau \in \mathbb{Z}_{\ge 1}$), ensuring decisions at month $t$ do not create immediate supply at month $t$.
6. **CP-SAT Optimizer:** Operates on consistent integer-scaled units ($\text{INR} / 1000$ and yield scaling factor $1000$), maintaining integer-exact decision variables without fractional trainees.
7. **Type-Safe Domain Abstraction Introduced:** Added `DataPoint` and safe gap validator in `backend/app/core/units.py` to prevent future stock/flow or periodic regressions.

---

## 2. Complete Dimensional and Accounting Unit Table

| Quantity Name | Dimensional Type | Standard Unit | Accounting Period | Mathematical Definition / Source | Primary Consumers | Dimensional Compatibility Status |
|---|---|---|---|---|---|---|
| **Raw Job Volume ($V$)** | Demand Flow | openings / month | Monthly | Aggregated monthly employer postings from NCS/portal adapters | EDI Calculator | **VALID** |
| **Deduplication Factor ($\delta_{\text{dedup}}$)** | Dimensionless | ratio $[0.70, 0.95]$ | Dimensionless | Scraper syndication & cross-portal deduplication multiplier | EDI Calculator | **VALID** |
| **Vacancy Persistence Multiplier** | Dimensionless | ratio $[0.50, 1.50]$ | Dimensionless | Clamped ratio: $\min(1.5, \max(0.5, \bar{T}_{\text{tenure}} / 30.0))$ | EDI Calculator | **VALID** |
| **Employer Diversity Multiplier** | Dimensionless | ratio $[0.60, 1.00]$ | Dimensionless | Derived from Herfindahl-Hirschman Index: $1.0 - 0.4 \cdot \text{HHI}$ | EDI Calculator | **VALID** |
| **Posting Quality Score** | Dimensionless | score $[0.50, 1.00]$ | Dimensionless | Weighted salary transparency, verified employer flag, NSQF link | EDI Calculator | **VALID** |
| **Effective Demand Index (EDI)** | **Demand Flow** | **openings / month** | **Monthly** | $V \cdot \delta_{\text{dedup}} \cdot \text{Persistence} \cdot \text{Diversity} \cdot \text{Quality}$ | Heatmap, Net Gap, Forecast Series | **VALID** |
| **Sanctioned Seats ($S$)** | Decision / Capacity | seats / cohort batch | Discrete cohort batch (typically 30) | PMKVY / ITI center sanctioned training capacity | Supply Funnel, Simulator, CP-SAT Optimizer | **VALID** |
| **Enrolled Trainees** | Flow Rate | trainees / month | Monthly | $S \cdot \gamma_{\text{enroll}}$ | Supply Funnel | **VALID** |
| **Completed Trainees** | Flow Rate | trainees / month | Monthly | $\text{Enrolled} \cdot \gamma_{\text{complete}}$ | Supply Funnel | **VALID** |
| **Certified Trainees** | Flow Rate | certified workers / month | Monthly | $\text{Completed} \cdot \gamma_{\text{certify}}$ | Supply Funnel | **VALID** |
| **Placed Trainees** | Flow Rate | placed workers / month | Monthly | $\text{Certified} \cdot \gamma_{\text{place}}$ | Supply Funnel | **VALID** |
| **Effective Active Supply (EAS)** | **Supply Flow** | **entrants / month** | **Monthly** | $\text{Placed} \cdot \gamma_{\text{retain}} = S \cdot \Gamma_{\text{funnel}}$ | Net Gap, Time Series DB, Simulator | **VALID** |
| **Total Workforce Estimate** | **Stock Indicator** | **workers** | **Static Snapshot** | Census & PLFS district working-age population baseline | Contextual KPI Card (Never subtracted from flow) | **VALID (PRESERVED AS STOCK)** |
| **Pipeline Activation Lag ($\tau$)** | Duration / Time | months | Duration ($\tau \ge 2$) | $\tau_{\text{admin}} (1\text{m}) + \lceil T_{\text{course}}/30 \rceil + \tau_{\text{placement}} (1\text{m})$ | Simulator, Cohort Trajectory | **VALID** |
| **Net Gap / Shortage** | **Reconciled Flow** | **openings / month** | **Monthly** | $\text{EDI} - \text{EAS}$ (Flow $-$ Flow) | Heatmap, Forecaster, CP-SAT Problem Instance | **VALID** |
| **Point Forecast Projections** | Projected Flow | openings / month | Monthly ($h \in \{3, 6, 12\}$) | Winning Model projection ($h$ steps forward) | Forecast Recharts, Policy Brief | **VALID** |
| **Forecast Confidence Interval (CI)** | Error Envelope | openings / month | Monthly | Point Forecast $\pm z_{\alpha} \cdot \hat{\sigma}_{\epsilon}$ | Recharts Confidence Band Area | **VALID** |
| **Budget Ceiling** | Financial Resource | INR | Planning Period (e.g. 6-12 mo) | Program allocation limit | CP-SAT Optimizer Constraint | **VALID** |
| **Training Unit Cost** | Financial Rate | INR / trainee | Per trainee | Skill standard cost norms (NSDC/MSDE rates) | Budget Calculation in CP-SAT & Simulator | **VALID** |
| **Mitigated Shortage ($m_i$)** | Abated Flow | openings / month | Monthly | CP-SAT Integer variable: $0 \le m_i \le \text{gap}_i$ | CP-SAT Objective Function | **VALID** |

---

## 3. Detailed Verification of the Fundamental Rule

$$\text{Valid Gap Operation} \iff \text{unit}(\text{Demand}) \equiv \text{unit}(\text{Supply}) \quad \land \quad \text{period}(\text{Demand}) \equiv \text{period}(\text{Supply})$$

### 3.1 Flow vs. Stock Separation
* **The Rule:** You cannot subtract a stock of workers from a monthly flow of vacancies.
  $$\text{INVALID:} \quad \text{EDI } (100 \text{ openings/month}) - \text{Workforce } (80,000 \text{ workers})$$
* **Actual Code Implementation:**
  In `synthetic_generator.py`:
  ```python
  # Effective active supply after 6-month retention
  eas = round(placed * eta_ret, 1)  # Flow: placed trainees entering pool per month
  net_gap = round(edi - eas, 1)     # Flow - Flow: [openings/month] - [entrants/month]
  ```
  `District.total_workforce_est` is **never** used in `net_gap`. It is only consumed in `endpoints_geo.py` as descriptive demographic metadata.
* **Safety Mechanism Added:**
  `backend/app/core/units.py` defines `calculate_labour_gap()`. If an operator or script attempts:
  ```python
  calculate_labour_gap(
      DataPoint(value=100.0, unit="openings/month", period="monthly"),
      DataPoint(value=80.0, unit="workers", period="snapshot")
  )
  ```
  It immediately raises `UnitMismatchError: Stock/Flow mismatch: cannot subtract stock unit ('workers') from flow unit ('openings/month').`

### 3.2 Monthly vs. Annual Temporal Alignment
* **The Rule:** You cannot subtract annualized capacity from monthly vacancy demand without rate conversion.
  $$\text{INVALID:} \quad 100 \text{ openings/month} - 960 \text{ entrants/year}$$
* **Safety Mechanism Added:**
  `calculate_labour_gap()` enforces `demand.period == supply.period`. An annualized entrant figure must be explicitly converted using `annual_to_monthly_flow()` ($960 / 12 = 80 \text{ entrants/month}$) before computing the gap. If passed directly, it raises `PeriodMismatchError`.

### 3.3 Geographic Granularity Alignment
* **The Rule:** You cannot subtract national or state supply pools from a district vacancy figure without spatial distribution weighting.
* **Safety Mechanism Added:**
  `calculate_labour_gap()` verifies `demand.geography_level == supply.geography_level`. Mismatched levels raise `GeographyMismatchError`.

---

## 4. Verification of Cohort Activation Lag ($T + \tau$)

A critical policy defect in unverified skilling systems is assuming immediate supply generation ($t_0 \to \text{supply}$).

### Implementation in `funnel_model.py` and `simulator.py`:
* **Course Duration ($T$):** Provided in days (e.g. 90 days). Converted to months: $\tau_{\text{course}} = \lceil T / 30 \rceil = 3$ months.
* **Administrative Mobilization ($\tau_{\text{admin}}$):** Fixed at 1 month for center notification, batch roster submission, and enrollment.
* **Assessment & Placement ($\tau_{\text{placement}}$):** Fixed at 1 month for Sector Skill Council testing, interview drives, and joining verification.
* **Total Fresh Seat Lag:**
  $$\tau_{\text{fresh}} = 1 + \lceil T/30 \rceil + 1 = 5 \text{ months (for 90-day course)}$$
* **Verification in Simulation Trajectory:**
  In `backend/app/services/simulation/simulator.py`:
  ```python
  for m in range(1, horizon_months + 1):
      supply_added = 0.0
      cohort_status = "BASELINE"

      if m >= start_month_offset + fresh_lag and additional_seats > 0:
          supply_added += effective_fresh_supply
          cohort_status = "FRESH_COHORT_ACTIVE"
      elif m < start_month_offset + fresh_lag and additional_seats > 0:
          cohort_status = "TRAINING_IN_PROGRESS"
  ```
  **Result:** For months $m < \text{start\_month\_offset} + \tau_{\text{fresh}}$, `supply_added` is **strictly 0.0**. The policy intervention does not affect supply until the cohort officially certifies and places.

---

## 5. Verification of the CP-SAT Optimizer Formulation

In `backend/app/services/optimizer/solver.py`:

1. **Shortage Non-Negativity:**
   $m_i \in [0, \text{gap}_i]$ is defined via:
   ```python
   m_i = model.NewIntVar(0, max(0, gap), f"mitigated_{i}")
   model.Add(m_i <= gap)
   ```
   Enforces $0 \le m_i \le \text{gap}_i$.
2. **Integer Batch Quotas:**
   $x_i = b_i \cdot \text{batch\_size}$, where $b_i \in \mathbb{Z}_{\ge 0}$ and $\text{batch\_size} = 30$.
   Fractional seats are strictly forbidden.
3. **Linearized Pipeline Yield Constraint:**
   $$\text{CP\_SAT\_YIELD\_SCALE} \cdot m_i \le \Gamma_{\text{fresh}} \cdot x_i + \Gamma_{\text{up}} \cdot y_i$$
   Scaled with named constant `CP_SAT_YIELD_SCALE = 1000`, matching fractional rates to integer precision.
4. **Budget Constraint:**
   Scaled with named constant `CP_SAT_BUDGET_SCALE = 1000` (Thousands of INR):
   $$\sum \text{unit\_cost}_k \cdot x_i + \dots \le \lfloor \text{budget\_ceiling} / 1000 \rfloor$$
   Dimensionally consistent and integer-exact.

---

## 6. Regression and Edge Case Test Suite

The new automated test file [backend/tests/test_milestone8_unit_audit.py](file:///c:/Users/ITLab-17/Desktop/skillful/backend/tests/test_milestone8_unit_audit.py) executes 12 rigorous audit checks:

1. `test_stock_flow_mismatch_fails`: $100 \text{ openings/month} - 80 \text{ workers} \implies$ **RAISES UnitMismatchError**.
2. `test_compatible_monthly_flows_succeed`: $100 \text{ openings/month} - 80 \text{ entrants/month} \implies$ **SUCCEEDS (+20.0 openings/month)**.
3. `test_periodic_mismatch_fails`: $100 \text{ openings/month} - 960 \text{ entrants/year} \implies$ **RAISES PeriodMismatchError**.
4. `test_explicit_annual_conversion_succeeds`: $960 \text{ entrants/year} \xrightarrow{\div 12} 80 \text{ entrants/month} \implies$ **SUCCEEDS (+20.0 openings/month)**.
5. `test_geographic_mismatch_fails`: District demand $-$ National supply $\implies$ **RAISES GeographyMismatchError**.
6. `test_zero_demand_flow`: $\text{EDI} = 0$, $\text{Supply} = 50 \implies \text{Net Gap} = -50.0$ (Oversupply).
7. `test_zero_supply_flow`: $\text{EDI} = 150$, $\text{Supply} = 0 \implies \text{Net Gap} = +150.0$ (Complete Deficit).
8. `test_zero_budget_optimizer`: Budget = ₹0 $\implies$ Allocates 0 seats, 0 cost, status `OPTIMAL`.
9. `test_large_budget_optimizer_caps`: Budget = ₹10 Cr $\implies$ Allocates seats up to trainer pool and center caps, without over-allocating beyond total gap.
10. `test_cohort_funnel_lag_zero_initial_supply`: Verifies supply is 0 during all training months.
11. `test_empty_backtester_series`: Backtester with empty or invalid series raises clean ValueError / handles gracefully.
12. `test_cpsat_named_scale_constants`: Confirms `CP_SAT_YIELD_SCALE` and `CP_SAT_BUDGET_SCALE` are exported and integer-safe.

---

## 7. Audit Conclusion & Decision

The quantitative core of **SkillPulse India** is mathematically and dimensionally consistent. All historical, forecasted, and simulated quantities operate on verified monthly flow rates ($\text{openings / month}$ vs $\text{entrants / month}$), while static workforce stocks are preserved purely as contextual indicators.

**FINAL DECISION:**  
**DIMENSIONALLY SOUND — PROCEED TO M8.2**
