# SkillPulse India: Simulation & Optimization Mathematical Specification
**Document Version:** 1.0.0  
**Focus:** Effective Demand Index (EDI), Multi-Stage Supply Cohort Funnel, Dynamic Pipeline Lag, and Mixed-Integer Constraint Optimization (MILP / CP-SAT)

---

## 1. Effective Demand Modeling (EDI)

Raw job vacancies retrieved from job portals or employment exchanges represent crude, distorted demand. SkillPulse India filters and scales raw counts into an **Effective Demand Index (EDI)**.

### Mathematical Formulation:
$$\text{EDI}_{d,s,t} = V_{d,s,t} \cdot \delta_{d,s} \cdot P_{d,s,t} \cdot D_{d,s,t} \cdot Q_{d,s,t}$$

Where:
- $V_{d,s,t} \in \mathbb{Z}_{\ge 0}$: Raw posting volume observed for skill $s$ in district $d$ at month $t$.
- $\delta_{d,s} \in [0.70, 0.95]$: **Deduplication Discount Factor**, eliminating ghost postings, syndicated scraper duplicates, and identical cross-posted vacancies.
- $P_{d,s,t}$: **Vacancy Persistence Multiplier**:
  $$P_{d,s,t} = \min\left(1.5, \, \max\left(0.5, \, \frac{\bar{T}_{\text{active}}}{30}\right)\right)$$
  Where $\bar{T}_{\text{active}}$ is the mean days a vacancy remains open. Vacancies lasting >30 days indicate persistent structural shortages; transient openings (<10 days) are scaled down.
- $D_{d,s,t}$: **Employer Diversity Factor (Inverse Concentration)**:
  Derived from the Herfindahl-Hirschman Index (HHI) across unique employers $i \in \{1, \dots, E\}$:
  $$\text{HHI}_{d,s,t} = \sum_{i=1}^E \left( \frac{v_i}{V} \right)^2 \in [0, 1]$$
  $$D_{d,s,t} = 1.0 - 0.4 \cdot \text{HHI}_{d,s,t}$$
  If a single firm generates 90% of postings, $\text{HHI} \approx 0.81 \implies D \approx 0.676$. If 50 employers post evenly, $\text{HHI} \approx 0.02 \implies D \approx 0.992$.
- $Q_{d,s,t} \in [0.60, 1.00]$: **Posting Quality Index**, scored by salary disclosure, verifiable physical office, clear NSQF-aligned job role description, and authenticated GSTIN/EPFO registration.

---

## 2. Supply Funnel & Dynamic Cohort Pipeline Modeling

### 2.1 The Multi-Stage Attrition Funnel

A cardinal rule of SkillPulse India is: **A training seat is NOT an active worker.**

```
[Sanctioned Seats: S]
         │  x Enrollment Rate (η_enroll ≈ 0.92)
         v
  [Enrolled: E]
         │  x Completion Rate (η_comp ≈ 0.85)
         v
 [Completed: C]
         │  x Certification Rate (η_cert ≈ 0.90)
         v
 [Certified: K]
         │  x Placement Rate (η_place ≈ 0.72)
         v
  [Placed: P]
         │  x 6-Month Retention Rate (η_ret ≈ 0.82)
         v
[Effective Active Workforce: EAS]
```

### Cumulative Pipeline Multiplier ($\Gamma$):
$$\Gamma_s = \eta_{\text{enroll}, s} \cdot \eta_{\text{comp}, s} \cdot \eta_{\text{cert}, s} \cdot \eta_{\text{place}, s} \cdot \eta_{\text{ret}, s}$$

For a representative EV technician course:
$$\Gamma_{\text{EV}} = 0.92 \cdot 0.85 \cdot 0.90 \cdot 0.72 \cdot 0.82 = \mathbf{0.415} \quad (41.5\%)$$
Sanctioning 1,000 seats yields only **415 net effective productive workers** in the district labour pool.

---

### 2.2 Temporal Activation Lag Model

Supply response is delayed by three strict real-world components:
1. **Administrative & Mobilization Lag ($\tau_{\text{admin}}$):** Batch mobilization, student counseling, portal registration (Nominal: 1 month).
2. **Instructional Duration Lag ($\tau_{\text{course}}$):** Prescribed NSQF curriculum hours:
   $$\tau_{\text{course}, s} = \left\lceil \frac{\text{CourseHours}_s}{150} \right\rceil \text{ months} \quad (\text{e.g., 360 hours} \implies 3 \text{ months})$$
3. **Assessment, Placement & Onboarding Lag ($\tau_{\text{place}}$):** SSC assessment, interview drives, relocation (Nominal: 1 month).

Total Pipeline Lag:
$$\tau_{\text{total}, s} = \tau_{\text{admin}} + \tau_{\text{course}, s} + \tau_{\text{place}}$$

### Supply Activation Step Function:
Let an intervention sanctioning $x$ seats commence at month $t_0$. The incremental workforce arrival at month $t$ is:
$$\Delta \text{Supply}_s(t) = \begin{cases} 0, & \text{if } t < t_0 + \tau_{\text{total}, s} \\ x \cdot \Gamma_s, & \text{if } t \ge t_0 + \tau_{\text{total}, s} \end{cases}$$

---

### 2.3 Adjacent-Worker Bridge Upskilling

In addition to fresh entrant training, the system models fast-track upskilling of workers with adjacent skillsets (e.g. converting an Internal Combustion Engine technician into an EV battery technician):
- **Reduced Duration:** $\tau_{\text{course, upskill}} = 1.5$ months
- **Higher Retention & Placement:** $\Gamma_{\text{upskill}} = 0.78$
- **Lower Training Cost:** $c_{\text{upskill}, s} = 0.45 \cdot c_{\text{fresh}, s}$

---

## 3. Prescriptive Intervention Optimizer Formulation

The optimization engine calculates the exact integer number of training seats and upskilling quotas to sanction across districts and skills, maximizing net shortage reduction within strict budgetary, trainer, and infrastructure bounds.

### 3.1 Mathematical Program (MILP / CP-SAT)

#### Indices and Sets:
- $d \in \mathcal{D}$: Target districts
- $s \in \mathcal{S}$: Target skills
- $t \in \{1, \dots, H\}$: Forecast horizon (typically $H = 6$ or $H = 12$)

#### Input Parameters:
- $G_{d,s}$: Unmitigated forecasted net talent deficit at horizon $H$ ($\max(0, \, \hat{\text{Demand}} - \hat{\text{Supply}}$)
- $w_s$: Priority weighting of sector/skill (from MSDE national mission priorities)
- $c_{s}$: Unit cost per fresh training seat (INR)
- $c_{\text{up}, s}$: Unit cost per upskilling seat (INR)
- $R_s$: Trainee-to-Trainer ratio (e.g. 20 trainees per 1 certified instructor)
- $\Gamma_s$: Cumulative fresh training pipeline yield
- $\Gamma_{\text{up}, s}$: Cumulative upskilling pipeline yield
- $B$: Total available intervention budget (INR)
- $T_d$: Available certified trainer pool capacity in district $d$
- $C_d$: Maximum physical seat capacity ceiling in district $d$
- $B_{\text{size}}$: Standard classroom batch increment (e.g. 30 seats)

#### Decision Variables:
- $b_{d,s} \in \mathbb{Z}_{\ge 0}$: Number of 30-student batches sanctioned (Integer)
- $x_{d,s} = B_{\text{size}} \cdot b_{d,s}$: Total fresh training seats (Integer)
- $y_{d,s} \in \mathbb{Z}_{\ge 0}$: Trainees allocated to bridge upskilling (Integer)
- $m_{d,s} \ge 0$: Actual effective talent shortage mitigated (Continuous / Auxiliary)

---

### 3.2 Objective Function
Maximize the total priority-weighted reduction in talent shortage:
$$\max \sum_{d \in \mathcal{D}} \sum_{s \in \mathcal{S}} w_s \cdot m_{d,s}$$

Subject to:

#### 1. Shortage Upper Bound (No Over-Supply Wastage):
The mitigated shortage cannot exceed the unmitigated deficit:
$$m_{d,s} \le G_{d,s}, \quad \forall d \in \mathcal{D}, s \in \mathcal{S}$$
$$m_{d,s} \le \Gamma_s \cdot x_{d,s} + \Gamma_{\text{up}, s} \cdot y_{d,s}, \quad \forall d \in \mathcal{D}, s \in \mathcal{S}$$

#### 2. Fiscal Budget Constraint:
Total capital allocated cannot exceed the designated financial ceiling:
$$\sum_{d \in \mathcal{D}} \sum_{s \in \mathcal{S}} \left( c_s \cdot x_{d,s} + c_{\text{up}, s} \cdot y_{d,s} \right) \le B$$

#### 3. Trainer Availability Constraint:
Required certified instructors cannot exceed available district headcount:
$$\sum_{s \in \mathcal{S}} \left\lceil \frac{x_{d,s} + y_{d,s}}{R_s} \right\rceil \le T_d, \quad \forall d \in \mathcal{D}$$
*(Formulated in CP-SAT via integer division $t_{d,s} \cdot R_s \ge x_{d,s} + y_{d,s}$)*

#### 4. Physical Center Capacity Constraint:
Total seats concurrently running cannot exceed accredited infrastructure:
$$\sum_{s \in \mathcal{S}} x_{d,s} \le C_d, \quad \forall d \in \mathcal{D}$$

#### 5. Modularity & Non-Negativity:
$$b_{d,s} \in \mathbb{Z}_{\ge 0}, \quad x_{d,s} = 30 \cdot b_{d,s}, \quad y_{d,s} \in \mathbb{Z}_{\ge 0}, \quad m_{d,s} \ge 0$$

---

## 4. Frontend Deterministic Simulation Response Curves

To guarantee ultra-fast client-side UI slider interactions (<5ms) without polling the backend on every slider pixel movement, the backend pre-calculates and exports the closed-form response equations to the frontend client.

### Client-Side Closed Form:
Given slider values $(x, y, \Delta \text{stipend})$:

1. **Incurred Budget ($B_{\text{calc}}$):**
   $$B_{\text{calc}}(x, y) = x \cdot c_s + y \cdot c_{\text{up}, s} + (x + y) \cdot \Delta \text{stipend}$$

2. **Supply Arrival Vector for Month $m \in \{1, \dots, 12\}$:**
   $$\text{SupplyAdded}(m) = \begin{cases} 
   0, & m < \tau_{\text{up}} \\
   y \cdot \Gamma_{\text{up}}, & \tau_{\text{up}} \le m < \tau_{\text{fresh}} \\
   y \cdot \Gamma_{\text{up}} + x \cdot \Gamma_{\text{fresh}} \cdot \left(1 + \min(0.15, \frac{\Delta \text{stipend}}{10000})\right), & m \ge \tau_{\text{fresh}}
   \end{cases}$$

3. **Reconciled Shortage:**
   $$\text{Gap}_{\text{sim}}(m) = \max\left(0, \, \hat{\text{Demand}}(m) - \left[ \hat{\text{Supply}}(m) + \text{SupplyAdded}(m) \right]\right)$$

This mathematical decoupling allows the Next.js user interface to re-render charts at 60 FPS while remaining mathematically identical to server calculations.
