# SkillPulse India: System Architecture Specification
**Document Version:** 1.0.0  
**Target Ministry:** Ministry of Skill Development and Entrepreneurship (MSDE), Government of India  
**System Classification:** Labour-Market Decision Intelligence & Policy Optimization Platform  
**Operational Mode:** DETECT → FORECAST → EXPLAIN → SIMULATE → OPTIMIZE

---

## 1. Executive Summary & Core Mandate

**SkillPulse India** is an enterprise-grade decision intelligence platform designed to replace ad-hoc, retrospective skill surveys with a continuous, forward-looking, and mathematically rigorous pipeline.

The platform addresses a fundamental flaw in traditional skilling programs: **training seats are allocated based on historical quotas or raw job portal scraping rather than net effective workforce supply pipelines and quality-weighted, persistent local demand.**

### The Core Operating Loop

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│ 1. DETECT   │ ──> │ 2. FORECAST  │ ──> │ 3. EXPLAIN  │ ──> │ 4. SIMULATE  │ ──> │ 5. OPTIMIZE  │
│ Demand/     │     │ 3, 6, 12-mo  │     │ SHAP + Data │     │ Cohort Lag & │     │ Integer      │
│ Supply Gap  │     │ Multi-model  │     │ Provenance  │     │ Policy Knobs │     │ Programming  │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘     └──────────────┘
```

1. **DETECT**: Identifies localized (district-level) talent deficits and surpluses across 5 priority sectors by reconciling raw demand signals with effective active supply.
2. **FORECAST**: Benchmarks multiple statistical and machine learning models (Naive, Seasonal, AutoETS/ARIMA, LightGBM/Ridge) over 3, 6, and 12-month horizons with rolling-window cross-validation.
3. **EXPLAIN**: Decouples model feature importance (via Tree/Kernel SHAP) from empirical macroeconomic indicators and structural labor friction factors.
4. **SIMULATE**: Models the realistic training pipeline (Seat $\to$ Enrollment $\to$ Completion $\to$ Certification $\to$ Placement $\to$ Retention) accounting for strict course duration lags and dropout attrition.
5. **OPTIMIZE**: Employs mixed-integer linear programming (MILP / CP-SAT) to allocate training seats, center expansions, and upskilling programs under rigid district-level budget, trainer, and physical capacity constraints.

---

## 2. Critical Engineering Principles & Safeguards

| Principle | Strict Rule & Implementation Safeguard |
|---|---|
| **No Fact Invention** | System never hallucinates government statistics, schemes, or district figures. All non-official metrics are strictly marked. |
| **No Unauthorized Scraping** | Zero dependency on unauthorized LinkedIn, Naukri, or private portals. Input feeds utilize public open datasets (NCS, PLFS, NSDC reports) and a transparent synthetic scenario generator. |
| **Synthetic Provenance** | Clear visual and cryptographic flags: `is_synthetic: true` / `DEMO_MODE: active`. Synthetic runs are watermarked in reports, JSON payloads, and UI overlays. |
| **Edge-Compute Embeddings** | Vector taxonomic reconciliation executes locally using lightweight sentence encoders (e.g. `all-MiniLM-L6-v2` / ONNX) and FAISS/cosine indexing. No cloud LLM required. |
| **Supply != Seats** | A sanctioned seat does not equal immediate supply. All supply calculations apply a multi-stage attrition funnel and course-duration pipeline delay ($T + \tau$). |
| **Integer Decision Variables** | Interventions output strictly integer trainee counts ($x_{d,s,k} \in \mathbb{Z}_{\ge 0}$) because fractions of a training seat are unexecutable. |
| **No Forecasting Without Backtesting** | Forecasts are never published without rolling out-of-sample backtesting metrics ($WAPE$, $MAE$, $MASE$). |

---

## 3. Scope of Pilot Implementation

### 3.1 Geographic Coverage (3 Pilot States, 9 Target Districts)
- **Karnataka (South Hub)**:
  - *Bengaluru Urban* (Advanced Electronics, IT-ITeS, AI/Robotics)
  - *Dharwad* (Light Engineering, Auto Components, Food Processing)
  - *Dakshina Kannada / Mangaluru* (Logistics, Port Operations, Healthcare)
- **Maharashtra (Industrial & Logistics Corridor)**:
  - *Pune* (Automotive, Heavy Machinery, Embedded Systems)
  - *Nagpur* (Multimodal Logistics, Warehousing, Power)
  - *Aurangabad / Chhatrapati Sambhajinagar* (Pharma, Auto Ancillaries)
- **Odisha (Eastern Mineral & Green Transition Hub)**:
  - *Khordha / Bhubaneswar* (IT, Biotechnology, Renewable Energy Planning)
  - *Sundargarh / Rourkela* (Metallurgy, Heavy Equipment, Solar Installation)
  - *Ganjam* (Agritech, Maritime Logistics, Healthcare Support)

### 3.2 Target Sectors (5 Key Sectors)
1. **IT-ITeS & Digital Services** (Cloud, Cybersecurity, Embedded Firmware, AI Data Ops)
2. **Automotive & Advanced Manufacturing** (EV Powertrain Assembly, CNC/Robotic Welding, Quality Assurance)
3. **Healthcare & Life Sciences** (Emergency Medical Tech, Dialysis Technicians, Pharma Formulation)
4. **Green Energy & Power** (Solar PV Installation, Battery Storage Assembly, Wind Turbine Maintenance)
5. **Logistics & Supply Chain** (Automated Warehouse Ops, Cold-Chain Management, Fleet Telematics)

### 3.3 Skill Taxonomy Scope
- **35 Canonical Pilot Skills** aligned with **National Classification of Occupations (NCO-2015)** and **National Skills Qualifications Framework (NSQF Levels 3–7)**.

---

## 4. End-to-End System Architecture

```
                                      +---------------------------------------------+
                                      |                 DATA SOURCES                |
                                      +---------------------------------------------+
                                       |                     |                     |
                       +---------------+                     |                     +---------------+
                       |                                     |                                     |
               +---------------+                     +---------------+                     +---------------+
               | NCS / Job     |                     | PLFS & Census |                     | PMKVY / DGT   |
               | Open Portals  |                     | Microdata     |                     | Seat Rosters  |
               +---------------+                     +---------------+                     +---------------+
                       |                                     |                                     |
                       v                                     v                                     v
               +-----------------------------------------------------------------------------------+
               |                              SOURCE ADAPTER LAYER                                 |
               |  - Schema Normalization           - Temporal Alignment (Monthly)                  |
               |  - Missing Data Imputation         - Provenance Tagging & Checksumming            |
               |  - Synthetic Scenario Generator (Seed-Controlled, Configurable Shock Simulator)   |
               +-----------------------------------------------------------------------------------+
                                                        |
                                                        v
               +-----------------------------------------------------------------------------------+
               |                            CANONICAL SKILL ONTOLOGY                               |
               |  - Local SentenceTransformers (`all-MiniLM-L6-v2`) / FAISS Vector Store           |
               |  - NCO-2015 / NSQF Mapping Engine  - Aliases & Cross-Domain Similarity Graph      |
               +-----------------------------------------------------------------------------------+
                                       |                                           |
                    +------------------+                                           +------------------+
                    |                                                                                 |
                    v                                                                                 v
+---------------------------------------------+                   +---------------------------------------------+
|          DEMAND INTELLIGENCE ENGINE         |                   |          SUPPLY INTELLIGENCE ENGINE         |
|  - Raw Posting Volume                       |                   |  - Sanctioned Capacity & Enrollment         |
|  - Persistence Index (Duration Active)      |                   |  - Completion & Certification Loss Funnel   |
|  - Employer Concentration (Herfindahl-HHI)  |                   |  - Placement & 6-Month Retention Rates      |
|  - Posting Quality & Deduplication Hook     |                   |  - Pipeline Delay (Cohort Duration Lag)     |
|  ==> Effective Demand Index (EDI)           |                   |  ==> Effective Active Supply (EAS)          |
+---------------------------------------------+                   +---------------------------------------------+
                    \                                                               /
                     \------------------------------+------------------------------/
                                                    |
                                                    v
               +-----------------------------------------------------------------------------------+
               |                          TIME-SERIES FORECASTING ENGINE                           |
               |  - Horizon: 3, 6, 12 Months                                                       |
               |  - Candidates: Naive, Seasonal Naive, AutoARIMA / ETS, LightGBM Autoregressive    |
               |  - Backtesting: Rolling 6-fold Window Cross-Validation (WAPE, MAE, MASE)          |
               |  - Model Selection: Best-performing metric per (District x Skill) series          |
               +-----------------------------------------------------------------------------------+
                                                        |
                                                        v
               +-----------------------------------------------------------------------------------+
               |                     EXPLAINABILITY & CONFIDENCE ENGINES                           |
               |  - SHAP Explainer (Model Feature Contribution)                                    |
               |  - Macro/Structural Indicators (Industrial Investment, Capital Inflow, Attrition) |
               |  - Confidence Score [0.0 - 1.0] derived from Data Density, Volatility, & WAPE     |
               +-----------------------------------------------------------------------------------+
                                                        |
                                                        v
               +-----------------------------------------------------------------------------------+
               |                         SIMULATION & OPTIMIZATION CORE                            |
               |  - Policy Simulator: Dynamic Cohort Pipeline ($t + \tau$ activation)             |
               |  - OR-Tools CP-SAT Optimizer: Integer Allocation of Seats & Centers               |
               |  - Constraints: Budget Cap, Trainer Pool, Center Square Footage, Minimum Batch    |
               +-----------------------------------------------------------------------------------+
                                                        |
                                                        v
               +-----------------------------------------------------------------------------------+
               |                               API & DELIVERY LAYER                                |
               |  - FastAPI Clean Architecture Endpoints (`/forecast`, `/simulate`, `/optimize`)   |
               |  - Next.js 14 Responsive UI (Leaflet GIS, Recharts, Interactive Slider Simulator)  |
               |  - Exportable MSDE Policy Briefs (Markdown / PDF / Print-Ready Executive Dockets) |
               +-----------------------------------------------------------------------------------+
```

---

## 5. Technology Stack Decisions & Justifications

| Component | Selected Technology | Justification & Architectural Trade-offs |
|---|---|---|
| **Backend Framework** | **FastAPI (Python 3.11/3.14)** | High-throughput async endpoints, native Pydantic schema validation, automatic OpenAPI v3 documentation, standard for enterprise AI/ML. |
| **Data & ORM** | **PostgreSQL + Supabase** (with SQLite fallback for local test harness) | Relational integrity, temporal window queries, JSONB storage for explainability/provenance payloads, offline capability. |
| **Vector Engine** | **FAISS-CPU + SentenceTransformers / ONNX** | Fully offline, zero cloud API dependencies, sub-millisecond similarity queries for skill mapping. |
| **Statistical & ML** | **NumPy, SciPy, Statsmodels, Scikit-learn, LightGBM** | High-performance backtesting, explainable tree models, deterministic outputs with seed control. |
| **Optimization** | **Google OR-Tools (CP-SAT Solver)** | Industrial-strength mixed-integer constraint programming; guarantees optimal or provably bounded integer solutions. |
| **Frontend Web** | **Next.js (App Router), TypeScript, Tailwind CSS** | Server-side rendering, type-safe API consumption, component isolation, instant client-side responsive interactions. |
| **Visualizations** | **Recharts & Leaflet.js** | Lightweight, open-source canvas/SVG rendering, zero mandatory Mapbox API keys or commercial licensing hurdles. |

---

## 6. Directory Structure & Modular Layout

```
skillful/
├── docs/                               # Architectural and Engineering Specs
│   ├── architecture.md
│   ├── database-schema.md
│   ├── api-contract.md
│   ├── ml-spec.md
│   ├── simulation-math.md
│   └── development-plan.md
├── backend/
│   ├── app/
│   │   ├── api/                        # Route Handlers (FastAPI Routers)
│   │   │   ├── deps.py
│   │   │   └── v1/
│   │   │       ├── endpoints_geo.py
│   │   │       ├── endpoints_skills.py
│   │   │       ├── endpoints_forecast.py
│   │   │       ├── endpoints_simulate.py
│   │   │       ├── endpoints_optimize.py
│   │   │       └── endpoints_brief.py
│   │   ├── core/                       # App Configuration & Security
│   │   │   ├── config.py
│   │   │   └── logging.py
│   │   ├── db/                         # Database Sessions & Base Models
│   │   │   ├── session.py
│   │   │   └── init_db.py
│   │   ├── models/                     # SQLAlchemy ORM Models
│   │   │   ├── district.py
│   │   │   ├── skill.py
│   │   │   ├── labor_market.py
│   │   │   └── intervention.py
│   │   ├── schemas/                    # Pydantic Request/Response Contracts
│   │   │   ├── district.py
│   │   │   ├── skill.py
│   │   │   ├── forecast.py
│   │   │   ├── simulation.py
│   │   │   └── optimization.py
│   │   └── services/                   # Decoupled Business & Algorithmic Logic
│   │       ├── adapters/               # NCS, PLFS, Synthetic Generators
│   │       ├── ontology/               # Vector Embedding & Skill Matcher
│   │       ├── demand/                 # Effective Demand Index (EDI)
│   │       ├── supply/                 # Cohort Lag & Pipeline Funnel
│   │       ├── forecasting/            # Model Zoo, Backtesting, Selection
│   │       ├── explainability/         # SHAP & Indicator Decomposer
│   │       ├── simulation/             # Dynamic Intervention Runner
│   │       └── optimizer/              # OR-Tools CP-SAT Formulator
│   ├── tests/                          # Automated Pytest Suite
│   ├── data/                           # Canonical Taxonomies & Seed Data
│   ├── requirements.txt
│   └── main.py
├── frontend/
│   ├── src/
│   │   ├── app/                        # Next.js App Router Pages
│   │   ├── components/                 # Reusable UI & Widget Modules
│   │   │   ├── map/                    # Leaflet District GeoMap
│   │   │   ├── charts/                 # Recharts Forecast & Cohort Visualizers
│   │   │   ├── simulator/              # Instant Slider Feedback Controller
│   │   │   ├── optimizer/              # Constraint Configurator & Result Table
│   │   │   └── ui/                     # Accessible Base UI Elements
│   │   ├── lib/                        # API Client & Math Helpers
│   │   └── types/                      # TypeScript Schema Interfaces
│   ├── package.json
│   ├── tailwind.config.js
│   └── tsconfig.json
└── README.md
```

---

## 7. Security, Provenance & Verification Guarantees

Every data packet traversing SkillPulse India carries an immutable provenance tuple:
```json
{
  "source_authority": "Ministry of Labour & Employment / Synthetic Generator",
  "dataset_version": "2026.03-SYNTH-PILOT",
  "transformation_pipeline": "EDI_v1.4::COHORT_FUNNEL_v2.0",
  "model_run_id": "run_20261005_blr_ev_003",
  "generated_at": "2026-10-05T15:21:00Z",
  "is_synthetic": true
}
```
This ensures zero ambiguity during audit reviews by state directorates or MSDE policymakers.
