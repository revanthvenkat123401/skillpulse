# SkillPulse India: RESTful API Contract Specification
**Document Version:** 1.0.0  
**Base URL:** `/api/v1`  
**OpenAPI Specification:** 3.1.0  
**Data Interchange Format:** JSON (`application/json`)  
**Character Encoding:** UTF-8

---

## 1. Global Standards & Conventions

### 1.1 Error Envelope Response
All HTTP 4xx and 5xx responses strictly adhere to RFC 7807 Problem Details:
```json
{
  "status_code": 400,
  "error_type": "VALIDATION_ERROR",
  "message": "Invalid forecast horizon requested.",
  "details": {
    "horizon_months": "Must be one of [3, 6, 12]."
  },
  "timestamp": "2026-10-05T15:22:00Z"
}
```

### 1.2 Mandatory Provenance Envelope
Every response containing analytical projections, indices, or recommendations includes the `provenance` block:
```json
{
  "provenance": {
    "data_source": "NCS_OPEN_DATA_REPRESENTATIVE_SAMPLE + SYNTH_SCENARIO_GEN",
    "dataset_version": "2026.03-PILOT",
    "transformation_version": "EDI_v1.4::COHORT_FUNNEL_v2.0",
    "model_version": "AUTO_ETS_v2.1",
    "run_id": "run_20261005_blr_ev_003",
    "is_synthetic": true,
    "generated_at": "2026-10-05T15:22:00Z"
  }
}
```

---

## 2. API Endpoints Catalog

### 2.1 Geographic & Administrative Endpoints

#### `GET /api/v1/districts`
Retrieves pilot districts with geographic coordinates, baseline demographics, and current aggregate labour balance.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `state_id` | string | No | - | Filter by State code (`KA`, `MH`, `OD`). |
| `sector_id` | string | No | - | Filter summary balance by specific sector. |

**Success Response (HTTP 200 OK):**
```json
{
  "districts": [
    {
      "id": "KA_BLR_URBAN",
      "state_id": "KA",
      "state_name": "Karnataka",
      "name": "Bengaluru Urban",
      "latitude": 12.9716,
      "longitude": 77.5946,
      "total_workforce_est": 5200000,
      "industrial_clusters": [
        "Electronics City",
        "Peenya Industrial Estate",
        "Whitefield Tech Corridor"
      ],
      "active_training_centers_count": 48,
      "aggregate_metrics": {
        "monthly_effective_demand": 14200.0,
        "monthly_effective_supply": 8900.0,
        "net_shortage": 5300.0,
        "severity_level": "CRITICAL_SHORTAGE"
      }
    }
  ],
  "total_count": 9,
  "provenance": { ... }
}
```

---

### 2.2 Skill Ontology & Taxonomy Endpoints

#### `GET /api/v1/skills`
Fetches canonical pilot skills with NCO-2015 codes, NSQF levels, training parameters, and search filters.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `sector_id` | string | No | - | Filter by Sector code (`IT_ITES`, `AUTO_EV`, etc.). |
| `nsqf_level` | integer | No | - | Filter by NSQF level (1 to 10). |
| `search` | string | No | - | Text substring search on canonical name or aliases. |

**Success Response (HTTP 200 OK):**
```json
{
  "skills": [
    {
      "id": "SKILL_EV_BATTERY_TECH",
      "sector_id": "AUTO_EV",
      "sector_name": "Automotive & Advanced Manufacturing",
      "canonical_name": "EV Battery Pack Assembly & Diagnostic Technician",
      "nco_code": "7412.0201",
      "nsqf_level": 4,
      "description": "Assembly, testing, thermal management integration, and diagnostic troubleshooting of lithium-ion traction battery modules.",
      "aliases": [
        "Battery Technician",
        "BMS Integration Specialist",
        "EV Energy Storage Assembler"
      ],
      "avg_training_days": 90,
      "trainer_ratio": 20,
      "cost_per_trainee_inr": 18500.0
    }
  ],
  "total_count": 35
}
```

#### `POST /api/v1/skills/match`
Maps an arbitrary job title or portal skill string to canonical taxonomy using local vector embeddings.

**Request Body:**
```json
{
  "query_title": "Electric vehicle battery testing assistant",
  "sector_hint": "AUTO_EV",
  "top_k": 3
}
```

**Success Response (HTTP 200 OK):**
```json
{
  "query": "Electric vehicle battery testing assistant",
  "top_matches": [
    {
      "canonical_skill_id": "SKILL_EV_BATTERY_TECH",
      "canonical_name": "EV Battery Pack Assembly & Diagnostic Technician",
      "similarity_score": 0.8872,
      "match_type": "VECTOR_EMBEDDING_COSINE",
      "nsqf_level": 4,
      "is_exact_alias": false
    }
  ],
  "execution_engine": "SentenceTransformers (all-MiniLM-L6-v2) / Local FAISS"
}
```

---

### 2.3 Spatial Mismatch Heatmap

#### `GET /api/v1/heatmap`
Returns district × sector × skill mismatch grid with normalized shortage ratios for geographical mapping.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `state_id` | string | No | - | Filter by state. |
| `sector_id` | string | No | - | Filter by sector. |
| `time_period` | string | No | latest | Period format `YYYY-MM`. |

**Success Response (HTTP 200 OK):**
```json
{
  "time_period": "2026-09-01",
  "grid": [
    {
      "district_id": "KA_BLR_URBAN",
      "district_name": "Bengaluru Urban",
      "latitude": 12.9716,
      "longitude": 77.5946,
      "sector_id": "AUTO_EV",
      "skill_id": "SKILL_EV_BATTERY_TECH",
      "skill_name": "EV Battery Pack Assembly & Diagnostic Technician",
      "effective_demand": 420.0,
      "effective_supply": 180.0,
      "net_gap": 240.0,
      "mismatch_ratio": 2.33,
      "status": "ACUTE_SHORTAGE"
    }
  ],
  "provenance": { ... }
}
```

---

### 2.4 Time-Series Forecasting

#### `GET /api/v1/forecast`
Fetches multi-horizon (3, 6, 12-month) demand, supply, and net gap predictions with confidence bands, model backtesting evidence, and low-data flags.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `district_id` | string | Yes | - | District identifier (`KA_BLR_URBAN`). |
| `skill_id` | string | Yes | - | Skill identifier (`SKILL_EV_BATTERY_TECH`). |
| `horizon_months` | integer | No | 6 | Horizon (`3`, `6`, or `12`). |

**Success Response (HTTP 200 OK):**
```json
{
  "district_id": "KA_BLR_URBAN",
  "skill_id": "SKILL_EV_BATTERY_TECH",
  "horizon_months": 6,
  "history_cutoff_date": "2026-09-01",
  "historical_series": [
    {
      "date": "2026-07-01",
      "effective_demand": 380.0,
      "effective_supply": 170.0,
      "net_gap": 210.0
    },
    {
      "date": "2026-08-01",
      "effective_demand": 405.0,
      "effective_supply": 175.0,
      "net_gap": 230.0
    },
    {
      "date": "2026-09-01",
      "effective_demand": 420.0,
      "effective_supply": 180.0,
      "net_gap": 240.0
    }
  ],
  "projections": [
    {
      "forecast_date": "2026-10-01",
      "month_offset": 1,
      "projected_demand": 435.5,
      "projected_supply": 185.0,
      "projected_gap": 250.5,
      "ci_80": {"lower": 225.0, "upper": 276.0},
      "ci_95": {"lower": 208.0, "upper": 293.0}
    },
    {
      "forecast_date": "2027-03-01",
      "month_offset": 6,
      "projected_demand": 510.0,
      "projected_supply": 200.0,
      "projected_gap": 310.0,
      "ci_80": {"lower": 270.0, "upper": 350.0},
      "ci_95": {"lower": 245.0, "upper": 375.0}
    }
  ],
  "model_metadata": {
    "selected_model": "AUTO_ETS (Additive Error, Additive Trend)",
    "benchmark_comparison": {
      "NAIVE": {"wape": 0.182, "mae": 42.5},
      "SEASONAL_NAIVE": {"wape": 0.165, "mae": 38.1},
      "AUTO_ETS": {"wape": 0.089, "mae": 20.4, "mase": 0.62},
      "LIGHTGBM_AR": {"wape": 0.104, "mae": 24.1, "mase": 0.73}
    },
    "backtest_folds": 6,
    "selection_reason": "Lowest WAPE across rolling 6-month out-of-sample backtests."
  },
  "confidence_engine": {
    "confidence_score": 0.88,
    "confidence_level": "HIGH",
    "low_data_flag": false,
    "confidence_reason": "Dense 24-month historical series with consistent reporting cadence."
  },
  "provenance": { ... }
}
```

---

### 2.5 Explainability & Provenance

#### `GET /api/v1/evidence`
Explains *why* the forecast was produced, decoupling statistical model feature attribution (SHAP) from observable economic and institutional evidence.

**Query Parameters:**
| Parameter | Type | Required | Description |
|---|---|---|---|
| `district_id` | string | Yes | District identifier. |
| `skill_id` | string | Yes | Skill identifier. |

**Success Response (HTTP 200 OK):**
```json
{
  "district_id": "KA_BLR_URBAN",
  "skill_id": "SKILL_EV_BATTERY_TECH",
  "statistical_feature_contributions": [
    {
      "feature": "lag_1_demand_momentum",
      "shap_value": 24.6,
      "interpretation": "Strong upward trajectory in past 30-day postings."
    },
    {
      "feature": "sector_industrial_capex_growth",
      "shap_value": 18.2,
      "interpretation": "Elevated state-level EV manufacturing approvals."
    },
    {
      "feature": "seasonal_hiring_surge",
      "shap_value": 7.4,
      "interpretation": "Q3 post-monsoon manufacturing ramp-up."
    }
  ],
  "observed_empirical_evidence": [
    {
      "indicator": "Employer Breadth",
      "metric_value": "42 unique hiring entities",
      "signal": "Demand is dispersed across OEMs and Tier-1 suppliers, not driven by a single recruiter."
    },
    {
      "indicator": "Posting Persistence",
      "metric_value": "Average vacancy tenure: 38 days",
      "signal": "Exceeds district median of 21 days; indicates structural talent scarcity."
    },
    {
      "indicator": "Local Training Pipeline",
      "metric_value": "2 accredited centers in district",
      "signal": "Current seat capacity (240 seats/yr) cannot satisfy 510/month annualized replacement."
    }
  ],
  "causality_disclaimer": "SHAP values represent statistical model feature dependencies and do not constitute formal econometric causal proof.",
  "provenance": { ... }
}
```

---

### 2.6 Policy Simulation

#### `POST /api/v1/simulate`
Simulates the impact of policy interventions with realistic cohort lag, certification dropouts, and placement attrition.

**Request Body:**
```json
{
  "district_id": "KA_BLR_URBAN",
  "skill_id": "SKILL_EV_BATTERY_TECH",
  "horizon_months": 12,
  "interventions": {
    "additional_sanctioned_seats": 120,
    "trainer_augmentation_count": 6,
    "upskilling_adjacent_technicians": 40,
    "stipend_subsidy_inr_per_trainee": 2500.0,
    "start_month_offset": 1
  }
}
```

**Success Response (HTTP 200 OK):**
```json
{
  "simulation_id": "sim_849202394",
  "district_id": "KA_BLR_URBAN",
  "skill_id": "SKILL_EV_BATTERY_TECH",
  "pipeline_parameters": {
    "course_duration_days": 90,
    "pipeline_lag_months": 3,
    "enrollment_rate": 0.95,
    "completion_rate": 0.88,
    "certification_rate": 0.92,
    "placement_rate": 0.78,
    "net_pipeline_efficiency": 0.599
  },
  "total_financial_commitment_inr": 2520000.0,
  "monthly_trajectory": [
    {
      "month_offset": 1,
      "date": "2026-10-01",
      "baseline_gap": 250.5,
      "simulated_supply_added": 0.0,
      "reconciled_gap": 250.5,
      "cohort_status": "ENROLLMENT_IN_PROGRESS"
    },
    {
      "month_offset": 3,
      "date": "2026-12-01",
      "baseline_gap": 275.0,
      "simulated_supply_added": 0.0,
      "reconciled_gap": 275.0,
      "cohort_status": "EXAMINATION_AND_CERTIFICATION"
    },
    {
      "month_offset": 4,
      "date": "2027-01-01",
      "baseline_gap": 290.0,
      "simulated_supply_added": 72.0,
      "reconciled_gap": 218.0,
      "cohort_status": "FIRST_COHORT_PLACED"
    },
    {
      "month_offset": 6,
      "date": "2027-03-01",
      "baseline_gap": 310.0,
      "simulated_supply_added": 102.0,
      "reconciled_gap": 208.0,
      "cohort_status": "UPKILLED_ADJACENT_WORKFORCE_ACTIVE"
    }
  ],
  "net_shortage_reduction_pct_at_12mo": 34.2,
  "cost_per_net_placed_worker_inr": 24705.88,
  "provenance": { ... }
}
```

---

### 2.7 Prescriptive Optimization

#### `POST /api/v1/optimize`
Solves an integer programming model (OR-Tools CP-SAT) to compute the globally optimal allocation of training seats and trainer deployments across skills under budget and capacity ceilings.

**Request Body:**
```json
{
  "state_id": "KA",
  "district_ids": ["KA_BLR_URBAN", "KA_DHARWAD", "KA_MANGALURU"],
  "sector_id": "AUTO_EV",
  "horizon_months": 6,
  "budget_ceiling_inr": 15000000.0,
  "constraints": {
    "max_new_trainers_statewide": 25,
    "max_seats_per_center": 150,
    "min_batch_size": 20,
    "allow_center_expansion": true
  }
}
```

**Success Response (HTTP 200 OK):**
```json
{
  "optimization_id": "opt_20261005_901",
  "solver_telemetry": {
    "solver_engine": "OR-Tools CP-SAT (Integer Linear Programming)",
    "status": "OPTIMAL",
    "solve_time_ms": 142,
    "integer_variables_count": 45,
    "constraints_evaluated": 112
  },
  "summary": {
    "total_budget_allocated_inr": 14680000.0,
    "budget_utilization_pct": 97.87,
    "total_training_seats_allocated": 780,
    "projected_total_shortage_reduction": 498,
    "aggregate_deficit_mitigation_pct": 41.2
  },
  "allocations": [
    {
      "district_id": "KA_BLR_URBAN",
      "skill_id": "SKILL_EV_BATTERY_TECH",
      "additional_seats": 240,
      "trainers_needed": 12,
      "unit_cost_inr": 18500.0,
      "total_cost_inr": 4440000.0,
      "unmitigated_gap_6mo": 310,
      "expected_placed_supply_6mo": 144,
      "remaining_gap_6mo": 166,
      "gap_reduction_pct": 46.45
    },
    {
      "district_id": "KA_DHARWAD",
      "skill_id": "SKILL_CNC_ROBOTIC_OPERATOR",
      "additional_seats": 180,
      "trainers_needed": 9,
      "unit_cost_inr": 16000.0,
      "total_cost_inr": 2880000.0,
      "unmitigated_gap_6mo": 220,
      "expected_placed_supply_6mo": 112,
      "remaining_gap_6mo": 108,
      "gap_reduction_pct": 50.91
    }
  ],
  "provenance": { ... }
}
```

---

### 2.8 MSDE Policy Brief Docket

#### `GET /api/v1/policy-brief`
Generates a structured, audit-ready MSDE Policy Brief in JSON, Markdown, and print-ready summary format.

**Query Parameters:**
| Parameter | Type | Required | Description |
|---|---|---|---|
| `district_id` | string | Yes | Target district. |
| `sector_id` | string | Yes | Target industrial sector. |
| `horizon_months` | integer | No (Default: 6) | Forecast reference horizon. |

**Success Response (HTTP 200 OK):**
```json
{
  "brief_id": "PB_KA_BLR_AUTO_20261005",
  "docket_title": "MSDE Labour Market Diagnostic & Intervention Plan: Bengaluru Urban (Automotive & EV)",
  "executive_summary": "Acute 6-month talent deficit detected in EV battery assembly and powertrain testing. Current institutional capacity satisfies only 43% of annualized replacement demand...",
  "key_findings": [
    "EV Battery Assembly faces an unmitigated 6-month deficit of 310 certified technicians.",
    "Pipeline attrition analysis indicates a 40.1% loss from initial seat enrollment to productive placement.",
    "Posting persistence of 38 days reflects localized talent scarcity rather than recruitment friction."
  ],
  "recommended_interventions": [
    "Sanction 240 additional NSQF Level-4 seats across 2 designated ITIs in Bengaluru Urban.",
    "Deploy 12 certified master trainers through the DGT fast-track instructor fellowship.",
    "Initiate 40 adjacent-worker bridge upskilling programs for ICE mechanics (6-week duration)."
  ],
  "budget_requirement_inr": 4440000.0,
  "expected_shortage_abatement_pct": 46.5,
  "provenance_checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "is_synthetic": true
}
```
