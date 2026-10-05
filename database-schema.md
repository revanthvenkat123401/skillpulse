# SkillPulse India: Database Schema Specification
**Document Version:** 1.0.0  
**Target Engines:** PostgreSQL 15+ / Supabase (Production) & SQLite 3.38+ with WAL (Local Zero-Config Test Suite)  
**Schema Versioning:** Alembic Migrations

---

## 1. Relational Entity Relationship Overview

The schema is divided into 4 core functional domains:
1. **Spatial & Sectoral Foundations**: States, Districts, Sectors, Canonical Skills, and Training Centers.
2. **Taxonomy & Skill Mapping**: Vectorized representations, NCO-2015 codes, NSQF levels, aliases, and human override logs.
3. **Labour Market Intelligence**: Monthly time-series of raw/effective demand, training pipeline funnels, and provenance metadata.
4. **Predictive & Prescriptive Output**: Forecast benchmarks, SHAP explanations, simulation parameters, and CP-SAT optimization results.

```
 [states] ──< [districts] ──< [training_centers] ──< [center_courses]
    │              │                                        │
    │              │                                        │
    │         [labor_market_time_series] >──────────┐       │
    │              │                                │       │
    v              v                                v       v
 [sectors] ──< [skills] ───────────────────────> [forecast_series]
    │              │                                    │
    │      [skill_mappings]                             v
    │                                          [forecast_explanations]
    │                                                   │
    └───────────────── [policy_briefs] <────────────────┘
                               │
               [simulation_scenarios] / [optimization_runs]
```

---

## 2. DDL Table Definitions (PostgreSQL Dialect)

### 2.1 Spatial & Sectoral Domain

#### `states`
```sql
CREATE TABLE states (
    id VARCHAR(10) PRIMARY KEY,              -- ISO/State Code e.g. 'KA', 'MH', 'OD'
    name VARCHAR(100) NOT NULL UNIQUE,       -- 'Karnataka', 'Maharashtra', 'Odisha'
    region VARCHAR(50) NOT NULL,             -- 'South', 'West', 'East'
    capital VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### `districts`
```sql
CREATE TABLE districts (
    id VARCHAR(20) PRIMARY KEY,              -- e.g. 'KA_BLR_URBAN', 'MH_PUNE', 'OD_KHORDHA'
    state_id VARCHAR(10) NOT NULL REFERENCES states(id) ON DELETE RESTRICT,
    name VARCHAR(100) NOT NULL,              -- 'Bengaluru Urban', 'Pune', 'Khordha'
    latitude NUMERIC(9, 6) NOT NULL,
    longitude NUMERIC(9, 6) NOT NULL,
    total_workforce_est INT NOT NULL,        -- Baseline labour pool from Census/PLFS
    industrial_clusters JSONB DEFAULT '[]'::jsonb, -- e.g. ['Peenya Industrial Area', 'Electronics City']
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_districts_state ON districts(state_id);
```

#### `sectors`
```sql
CREATE TABLE sectors (
    id VARCHAR(20) PRIMARY KEY,              -- 'IT_ITES', 'AUTO_EV', 'HEALTHCARE', 'GREEN_ENERGY', 'LOGISTICS'
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    priority_weight NUMERIC(3, 2) DEFAULT 1.00, -- Multiplier for state/national industrial priority
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### `skills`
```sql
CREATE TABLE skills (
    id VARCHAR(50) PRIMARY KEY,              -- e.g. 'SKILL_EV_BATTERY_TECH'
    sector_id VARCHAR(20) NOT NULL REFERENCES sectors(id) ON DELETE RESTRICT,
    canonical_name VARCHAR(150) NOT NULL UNIQUE,
    nco_code VARCHAR(20),                    -- National Classification of Occupations code e.g. '7412.0201'
    nsqf_level INT CHECK (nsqf_level BETWEEN 1 AND 10),
    description TEXT,
    aliases JSONB DEFAULT '[]'::jsonb,       -- e.g. ['Battery Pack Assembly Technician', 'BMS Tech']
    avg_training_days INT NOT NULL DEFAULT 90, -- Nominal duration for cohort lag calculation
    trainer_ratio INT NOT NULL DEFAULT 20,   -- Trainees per 1 certified trainer
    cost_per_trainee_inr NUMERIC(10, 2) NOT NULL DEFAULT 15000.00, -- Govt standard reimbursement cost
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_skills_sector ON skills(sector_id);
```

#### `skill_mappings`
```sql
CREATE TABLE skill_mappings (
    id SERIAL PRIMARY KEY,
    source_title VARCHAR(200) NOT NULL,      -- Unstructured title from portal or scheme roster
    canonical_skill_id VARCHAR(50) NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    similarity_score NUMERIC(5, 4) NOT NULL, -- Cosine similarity from SentenceTransformers (0.0 to 1.0)
    mapping_source VARCHAR(50) NOT NULL,     -- 'FAISS_VECTOR', 'EXACT_ALIAS', 'HUMAN_OVERRIDE'
    is_verified BOOLEAN DEFAULT FALSE,
    verified_by VARCHAR(100),
    verified_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_source_mapping UNIQUE(source_title, canonical_skill_id)
);
CREATE INDEX idx_skill_map_source ON skill_mappings(source_title);
```

---

### 2.2 Infrastructure & Capacity Domain

#### `training_centers`
```sql
CREATE TABLE training_centers (
    id VARCHAR(50) PRIMARY KEY,              -- e.g. 'TC_KA_BLR_001'
    district_id VARCHAR(20) NOT NULL REFERENCES districts(id) ON DELETE RESTRICT,
    name VARCHAR(200) NOT NULL,
    center_type VARCHAR(50) NOT NULL,        -- 'GOVT_ITI', 'PMKK', 'POLYTECHNIC', 'PRIVATE_TSP'
    max_total_capacity INT NOT NULL,         -- Physical seating / laboratory ceiling
    certified_trainers INT NOT NULL,         -- Available instructor headcount
    latitude NUMERIC(9, 6),
    longitude NUMERIC(9, 6),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_centers_district ON training_centers(district_id);
```

#### `center_courses`
```sql
CREATE TABLE center_courses (
    id SERIAL PRIMARY KEY,
    center_id VARCHAR(50) NOT NULL REFERENCES training_centers(id) ON DELETE CASCADE,
    skill_id VARCHAR(50) NOT NULL REFERENCES skills(id) ON DELETE RESTRICT,
    sanctioned_seats INT NOT NULL,
    batch_size INT NOT NULL DEFAULT 30,
    is_active BOOLEAN DEFAULT TRUE,
    CONSTRAINT uq_center_skill UNIQUE(center_id, skill_id)
);
```

---

### 2.3 Labour Market Time Series (Monthly Aggregations)

#### `labor_market_time_series`
```sql
CREATE TABLE labor_market_time_series (
    id BIGSERIAL PRIMARY KEY,
    district_id VARCHAR(20) NOT NULL REFERENCES districts(id) ON DELETE RESTRICT,
    skill_id VARCHAR(50) NOT NULL REFERENCES skills(id) ON DELETE RESTRICT,
    time_period DATE NOT NULL,               -- Represented as first day of month 'YYYY-MM-01'
    
    -- Demand Indicators
    raw_demand_postings INT NOT NULL DEFAULT 0,
    posting_persistence_days NUMERIC(5, 2) DEFAULT 0.0,
    unique_employers_count INT NOT NULL DEFAULT 0,
    employer_hhi NUMERIC(5, 4) DEFAULT 0.0, -- Herfindahl-Hirschman Index of demand concentration
    posting_quality_score NUMERIC(4, 3) DEFAULT 0.85, -- Parsed salary info, contact verification
    effective_demand_index NUMERIC(10, 2) NOT NULL,  -- Computed EDI signal
    
    -- Supply Indicators (Funnel)
    enrolled_trainees INT NOT NULL DEFAULT 0,
    completed_trainees INT NOT NULL DEFAULT 0,
    certified_trainees INT NOT NULL DEFAULT 0,
    placed_trainees INT NOT NULL DEFAULT 0,
    effective_active_supply NUMERIC(10, 2) NOT NULL, -- Placement * retention adjusted supply
    
    -- Reconciled Balance
    net_gap NUMERIC(10, 2) GENERATED ALWAYS AS (effective_demand_index - effective_active_supply) STORED,
    
    -- Provenance & Metadata
    data_source VARCHAR(100) NOT NULL,       -- 'NCS_PUBLIC_PORTAL', 'PLFS_ANNUAL', 'SYNTHETIC_SCENARIO_V1'
    is_synthetic BOOLEAN NOT NULL DEFAULT FALSE,
    provenance_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_district_skill_period UNIQUE(district_id, skill_id, time_period)
);
CREATE INDEX idx_lm_series_query ON labor_market_time_series(district_id, skill_id, time_period);
CREATE INDEX idx_lm_series_synthetic ON labor_market_time_series(is_synthetic);
```

---

### 2.4 Forecasting & Explainability Domain

#### `forecast_runs`
```sql
CREATE TABLE forecast_runs (
    id VARCHAR(64) PRIMARY KEY,              -- SHA256 of parameters or UUID e.g. 'run_20261005_001'
    run_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    training_cutoff_date DATE NOT NULL,
    benchmark_models JSONB NOT NULL,         -- ['NAIVE', 'SEASONAL_NAIVE', 'AUTO_ETS', 'LIGHTGBM']
    validation_folds INT NOT NULL DEFAULT 6,
    is_synthetic BOOLEAN NOT NULL DEFAULT FALSE,
    executed_by VARCHAR(100) DEFAULT 'SYSTEM_CRON'
);
```

#### `forecast_series`
```sql
CREATE TABLE forecast_series (
    id BIGSERIAL PRIMARY KEY,
    run_id VARCHAR(64) NOT NULL REFERENCES forecast_runs(id) ON DELETE CASCADE,
    district_id VARCHAR(20) NOT NULL REFERENCES districts(id) ON DELETE RESTRICT,
    skill_id VARCHAR(50) NOT NULL REFERENCES skills(id) ON DELETE RESTRICT,
    target_metric VARCHAR(30) NOT NULL,      -- 'EFFECTIVE_DEMAND', 'EFFECTIVE_SUPPLY', 'NET_GAP'
    horizon_months INT NOT NULL CHECK (horizon_months IN (3, 6, 12)),
    forecast_date DATE NOT NULL,             -- Horizon projection month 'YYYY-MM-01'
    
    -- Forecast Outputs
    point_forecast NUMERIC(10, 2) NOT NULL,
    ci_lower_80 NUMERIC(10, 2) NOT NULL,
    ci_upper_80 NUMERIC(10, 2) NOT NULL,
    ci_lower_95 NUMERIC(10, 2) NOT NULL,
    ci_upper_95 NUMERIC(10, 2) NOT NULL,
    
    -- Model Selection & Validation Evidence
    selected_model VARCHAR(50) NOT NULL,     -- e.g. 'AUTO_ETS', 'LIGHTGBM_AR'
    backtest_wape NUMERIC(6, 4) NOT NULL,    -- Weighted Absolute Percentage Error on test folds
    backtest_mae NUMERIC(10, 2) NOT NULL,
    backtest_mase NUMERIC(6, 4),             -- Mean Absolute Scaled Error vs Naive
    
    -- Confidence Engine Output
    confidence_score NUMERIC(4, 3) NOT NULL, -- 0.000 to 1.000
    confidence_level VARCHAR(20) NOT NULL,   -- 'HIGH', 'MEDIUM', 'LOW'
    low_data_flag BOOLEAN NOT NULL DEFAULT FALSE,
    confidence_reason TEXT,                  -- Reason for degradation if score < 0.70
    
    CONSTRAINT uq_forecast_target UNIQUE(run_id, district_id, skill_id, target_metric, horizon_months, forecast_date)
);
CREATE INDEX idx_forecast_lookup ON forecast_series(district_id, skill_id, horizon_months);
```

#### `forecast_explanations`
```sql
CREATE TABLE forecast_explanations (
    id BIGSERIAL PRIMARY KEY,
    forecast_series_id BIGINT NOT NULL REFERENCES forecast_series(id) ON DELETE CASCADE,
    
    -- Decoupled Explanations
    shap_feature_contributions JSONB NOT NULL, -- {"lag_3_demand": 14.2, "trend_slope": 8.5, "sector_capex": 22.1}
    observed_data_evidence JSONB NOT NULL,     -- {"recent_industrial_mou_cr": 450, "hhi_diversification": "+12%"}
    friction_factors JSONB NOT NULL,           -- {"trainer_shortage": true, "migration_drain": "moderate"}
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_forecast_exp_series ON forecast_explanations(forecast_series_id);
```

---

### 2.5 Simulation & Prescriptive Optimization Domain

#### `simulation_scenarios`
```sql
CREATE TABLE simulation_scenarios (
    id VARCHAR(64) PRIMARY KEY,              -- UUID
    session_id VARCHAR(100),
    scenario_name VARCHAR(150) NOT NULL,
    district_id VARCHAR(20) NOT NULL REFERENCES districts(id),
    skill_id VARCHAR(50) NOT NULL REFERENCES skills(id),
    base_forecast_run_id VARCHAR(64) REFERENCES forecast_runs(id),
    
    -- Simulation Knobs Applied
    additional_seats INT NOT NULL DEFAULT 0,
    trainer_expansion_count INT NOT NULL DEFAULT 0,
    upskilling_adjacent_count INT NOT NULL DEFAULT 0,
    stipend_subsidy_percentage NUMERIC(5, 2) DEFAULT 0.0,
    
    -- Output Trajectories
    monthly_lagged_supply JSONB NOT NULL,    -- Trajectory of supply arrival by month t+1..t+12
    monthly_reconciled_gap JSONB NOT NULL,   -- Resulting net shortage trajectory
    total_budget_spent NUMERIC(12, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### `optimization_runs`
```sql
CREATE TABLE optimization_runs (
    id VARCHAR(64) PRIMARY KEY,
    district_id VARCHAR(20) REFERENCES districts(id), -- NULL if multi-district state run
    sector_id VARCHAR(20) REFERENCES sectors(id),     -- NULL if multi-sector run
    horizon_months INT NOT NULL DEFAULT 6,
    
    -- Policy Constraints Supplied
    max_budget_inr NUMERIC(14, 2) NOT NULL,
    max_new_trainers INT NOT NULL,
    max_center_seat_expansion INT NOT NULL,
    allow_adjacent_upskilling BOOLEAN DEFAULT TRUE,
    
    -- Solver Telemetry
    solver_status VARCHAR(50) NOT NULL,      -- 'OPTIMAL', 'FEASIBLE', 'INFEASIBLE'
    solve_duration_ms INT NOT NULL,
    objective_gap_reduction_pct NUMERIC(5, 2) NOT NULL,
    total_cost_allocated_inr NUMERIC(14, 2) NOT NULL,
    
    -- Prescribed Actions
    seat_allocations JSONB NOT NULL,         -- [{"district_id": "...", "skill_id": "...", "additional_seats": 120, ...}]
    affected_skills_count INT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### `policy_briefs`
```sql
CREATE TABLE policy_briefs (
    id VARCHAR(64) PRIMARY KEY,
    district_id VARCHAR(20) NOT NULL REFERENCES districts(id),
    sector_id VARCHAR(20) NOT NULL REFERENCES sectors(id),
    forecast_run_id VARCHAR(64) NOT NULL REFERENCES forecast_runs(id),
    optimization_run_id VARCHAR(64) REFERENCES optimization_runs(id),
    title VARCHAR(250) NOT NULL,
    executive_summary TEXT NOT NULL,
    critical_findings JSONB NOT NULL,        -- Top 3 deficit skills, projected attrition
    prescribed_interventions JSONB NOT NULL, -- Actionable seat/trainer additions with budget
    provenance_checksum VARCHAR(64) NOT NULL,-- SHA256 of backing data rows
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

---

## 3. Data Integrity & Migration Strategy

1. **Foreign Key Enforcement**: All district and skill references cascade appropriately or restrict deletes to guarantee historical audit integrity.
2. **Deterministic Checksums**: Tables supporting policy briefs store SHA-256 hashes of input parameters to guarantee non-repudiation.
3. **Dual Compatibility**: DDL types strictly map between PostgreSQL (`JSONB`, `NUMERIC`, `TIMESTAMP WITH TIME ZONE`) and SQLite (`TEXT`, `REAL`, `TEXT`) through SQLAlchemy abstraction layer.
