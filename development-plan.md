# SkillPulse India: Phased Engineering & Development Plan
**Document Version:** 1.0.0  
**Methodology:** Verified Incremental Milestones  
**Target Completion:** SIH Hackathon Production Readiness  
**Quality Bar:** Fully automated test suites, zero unverified assumptions, comprehensive provenance tracking.

---

## 1. Development Principles & Verification Gateways

To satisfy the engineering standard required for a national decision-intelligence platform:
1. **Never implement in an unverified monolithic pass.**
2. Each milestone must produce **working code**, **passing automated tests**, and **verified sample outputs**.
3. All data models and algorithms must strictly adhere to the mathematical specs defined in `simulation-math.md` and `ml-spec.md`.
4. Any deviation from the initial specification must be recorded with explicit architectural rationale.

---

## 2. Milestone Roadmap & Acceptance Criteria

```
+-----------------------------------------------------------------------------------+
| MILESTONE 1: Environment, Domain Models & Deterministic Scenario Generator        |
| - Project initialization, SQLAlchemy ORM models, Pydantic schemas                 |
| - 3 Pilot States (KA, MH, OD), 9 Districts, 5 Sectors, 35 Canonical Skills        |
| - High-fidelity synthetic time-series generator (seed-controlled, marked data)    |
| - Verification: DB seed test, schema validation tests                             |
+-----------------------------------------------------------------------------------+
                                          │
                                          v
+-----------------------------------------------------------------------------------+
| MILESTONE 2: Local Skill Ontology & Taxonomic Reconciliation Engine               |
| - Lightweight local vector embeddings (all-MiniLM-L6-v2 / cosine similarity)       |
| - NCO-2015 and NSQF Level taxonomy integration                                   |
| - Human-reviewed override repository and alias lookup                              |
| - Verification: Cosine precision test, alias resolution test                      |
+-----------------------------------------------------------------------------------+
                                          │
                                          v
+-----------------------------------------------------------------------------------+
| MILESTONE 3: Demand (EDI) & Supply (Cohort Lag) Intelligence Services             |
| - Effective Demand Index (EDI): volume, persistence, HHI diversity, quality score |
| - Supply Pipeline Funnel: seat -> enrolled -> certified -> placed -> retained    |
| - Pipeline activation delay function (course duration + mobilization lag)         |
| - Verification: Cohort mathematical funnel test, EDI boundary tests               |
+-----------------------------------------------------------------------------------+
                                          │
                                          v
+-----------------------------------------------------------------------------------+
| MILESTONE 4: Multi-Model Forecasting, Rolling Backtest & Explainability           |
| - Model Zoo: Flat Naive, Seasonal Naive, AutoETS, LightGBM Autoregressive         |
| - Rolling 6-Fold Walk-Forward Cross-Validation (WAPE, MAE, MASE)                  |
| - Explainability Engine (TreeSHAP attribution + observable empirical evidence)    |
| - Confidence Engine: score [0.0..1.0], degradation breakdown, low-data alert      |
| - Verification: Out-of-sample backtest runner, SHAP additivity test               |
+-----------------------------------------------------------------------------------+
                                          │
                                          v
+-----------------------------------------------------------------------------------+
| MILESTONE 5: Policy Simulator & Integer Intervention Optimizer (OR-Tools CP-SAT)  |
| - Dynamic intervention simulator: seat additions, upskilling, stipend subsidies  |
| - Integer Programming (CP-SAT): budget ceiling, trainer capacity, center limits   |
| - Audit-ready MSDE Policy Brief generator (Markdown/JSON/Print docket)           |
| - Verification: CP-SAT solver feasibility test, integer seat constraint test      |
+-----------------------------------------------------------------------------------+
                                          │
                                          v
+-----------------------------------------------------------------------------------+
| MILESTONE 6: High-Throughput FastAPI Application & REST Contracts                 |
| - Endpoints: /districts, /skills, /heatmap, /forecast, /evidence, /simulate,     |
|   /optimize, /policy-brief, /skills/match                                         |
| - RFC 7807 error envelopes, provenance headers, OpenAPI docs                      |
| - Verification: Full Pytest test suite covering all HTTP contracts                |
+-----------------------------------------------------------------------------------+
                                          │
                                          v
+-----------------------------------------------------------------------------------+
| MILESTONE 7: Premium Next.js 14 Frontend User Interface                           |
| - Flow: India Overview -> State -> District -> Sector -> Skill -> Forecast        |
| - Interactive Leaflet GeoMap of District Mismatch Indices                         |
| - Recharts Time-Series with Confidence Bands and Historical Context               |
| - Client-side Interactive Policy Simulator Slider (<5ms local response)          |
| - Prescriptive Optimizer Panel and Executive MSDE Policy Brief Exporter           |
| - Clear "DEMO / SYNTHETIC SCENARIO" watermark and provenance badge               |
+-----------------------------------------------------------------------------------+
                                          │
                                          v
+-----------------------------------------------------------------------------------+
| MILESTONE 8: End-to-End Validation, Judge Test Checklist & Demonstration Runbook  |
| - Automated end-to-end integration tests                                          |
| - Hackathon Judge Verification Checklist & Demo script                            |
+-----------------------------------------------------------------------------------+
```

---

## 3. Detailed Milestone Tasks & Deliverables

### Milestone 1: Environment, Domain Models & Scenario Generator
- **Deliverables:**
  - `backend/app/models/`: SQLAlchemy models for states, districts, sectors, skills, centers, time-series, forecasts, optimizations.
  - `backend/app/schemas/`: Pydantic V2 schemas for input validation and serialized outputs.
  - `backend/app/services/adapters/synthetic_generator.py`: Generates 24-month historical series for 9 districts $\times$ 35 skills with realistic seasonal patterns, industrial shock events, and provenance tags.
  - `tests/test_milestone1_models_and_data.py`: Automated tests verifying relational integrity and deterministic data generation.

### Milestone 2: Skill Ontology & Vector Matching Engine
- **Deliverables:**
  - `backend/data/canonical_skills.json`: Complete pilot taxonomy (35 skills with NCO codes, NSQF levels, training hours, aliases).
  - `backend/app/services/ontology/matcher.py`: Embedding-based taxonomic resolver using local vector representations and cosine distance.
  - `tests/test_milestone2_ontology.py`: Automated tests verifying exact alias resolution, vector cosine ranking, and threshold gating.

### Milestone 3: Demand & Supply Intelligence Engines
- **Deliverables:**
  - `backend/app/services/demand/edi_calculator.py`: Implementation of EDI formula with HHI diversity, persistence capping, and deduplication.
  - `backend/app/services/supply/funnel_model.py`: Multi-stage funnel attrition and cohort duration lag calculator.
  - `tests/test_milestone3_demand_supply.py`: Automated tests verifying that training seats are discounted by pipeline attrition and delayed by training duration.

### Milestone 4: Forecasting, Rolling Backtesting & Explainability
- **Deliverables:**
  - `backend/app/services/forecasting/model_zoo.py`: Naive, Seasonal Naive, AutoETS, and LightGBM models.
  - `backend/app/services/forecasting/backtester.py`: Rolling walk-forward cross-validation engine calculating WAPE, MAE, and MASE.
  - `backend/app/services/explainability/explainer.py`: TreeSHAP feature attributions decoupled from observed economic indicators.
  - `backend/app/services/forecasting/confidence_engine.py`: Confidence score calculation and low-data alert generator.
  - `tests/test_milestone4_forecasting.py`: Automated tests evaluating model selection and confidence scoring.

### Milestone 5: Simulation & Integer Optimizer (CP-SAT)
- **Deliverables:**
  - `backend/app/services/simulation/simulator.py`: Dynamic policy scenario simulator with monthly supply activation curves.
  - `backend/app/services/optimizer/solver.py`: Google OR-Tools CP-SAT solver enforcing integer batch variables, trainer ratios, and budget limits.
  - `backend/app/services/brief/generator.py`: Automated MSDE Policy Brief compiler.
  - `tests/test_milestone5_simulation_optimizer.py`: Automated tests verifying integer batch constraints and budget feasibility.

### Milestone 6: FastAPI Application & REST Contracts
- **Deliverables:**
  - `backend/app/api/v1/`: Complete API routers matching `api-contract.md`.
  - `backend/main.py`: FastAPI application entry point with CORS, lifespan events, and error handlers.
  - `tests/test_milestone6_api.py`: Comprehensive TestClient API test suite.

### Milestone 7: Next.js Frontend User Interface
- **Deliverables:**
  - Responsive, modern Next.js application adhering to government executive dashboard standards.
  - Interactive Leaflet district map, Recharts forecast and funnel visualizers, local reactive simulation slider, and policy brief exporter.
  - Demo/Synthetic mode watermark throughout the interface.

### Milestone 8: Judge Test Checklist & Demonstration Runbook
- **Deliverables:**
  - `checklist.md`: Step-by-step verification checklist for hackathon judges.
  - `runbook.md`: Quickstart deployment commands.
