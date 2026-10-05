# SkillPulse India: Machine Learning & Forecasting Specification
**Document Version:** 1.0.0  
**Focus:** Demand Forecasting, Supply Funnel Modeling, Rolling Backtesting, Explainability, and Confidence Scoring  
**Core Motto:** "No forecasting without backtesting. Simple, robust, explainable over complex black-box."

---

## 1. Machine Learning Pipeline Architecture

The forecasting subsystem operates independently on each $(d, s)$ time-series tuple, where $d \in \text{Districts}$ and $s \in \text{Skills}$.

```
                               +-----------------------------+
                               | Monthly (d, s) Time Series  |
                               | (History Length: N months)  |
                               +-----------------------------+
                                              |
                                              v
                               +-----------------------------+
                               |   Rolling-Window Validation |
                               |   (6 Folds, Walk-Forward)   |
                               +-----------------------------+
                                              |
                       +----------------------+----------------------+
                       |                      |                      |
                       v                      v                      v
             +-------------------+  +-------------------+  +-------------------+
             |  Naive & Seasonal |  |   AutoETS / ARIMA |  |   LightGBM / AR   |
             |     Baselines     |  |   (Statsmodels)   |  |   (Gradient Boost)|
             +-------------------+  +-------------------+  +-------------------+
                       |                      |                      |
                       +----------------------+----------------------+
                                              |
                                              v
                               +-----------------------------+
                               |   Error Evaluation (WAPE)   |
                               |   Pick Winning Model for    |
                               |   each (District x Skill)   |
                               +-----------------------------+
                                              |
                       +----------------------+----------------------+
                       |                                             |
                       v                                             v
        +-----------------------------+               +-----------------------------+
        |  Multi-Horizon Projections  |               |    Explainability Engine    |
        |  (h = 3, 6, 12 Months)      |               |  - TreeSHAP (ML features)   |
        |  Point Forecast & CI [80,95]|               |  - Empirical Data Drivers   |
        +-----------------------------+               +-----------------------------+
                       \                                             /
                        \---------------------+---------------------/
                                              |
                                              v
                               +-----------------------------+
                               |      Confidence Engine      |
                               |  - Volatility, Density,     |
                               |    WAPE => Score [0.0..1.0] |
                               |  - Low-Data Flag & Reason   |
                               +-----------------------------+
```

---

## 2. Model Zoo & Baseline Hierarchy

We implement a strictly benchmarked hierarchy of 4 model classes. An advanced model is never deployed unless it outperforms the simpler baselines on rolling backtesting.

### Model 1: Flat Naive Baseline ($M_0$)
Carries forward the most recently observed value.
$$\hat{y}_{t+h} = y_t$$
Serves as the foundational benchmark for evaluating whether any temporal pattern is learnable.

### Model 2: Seasonal Naive Baseline ($M_1$)
Projects the value observed exactly one cycle ($m = 12$ months) prior.
$$\hat{y}_{t+h} = y_{t+h - m \cdot \lceil h/m \rceil}$$
Captures cyclical Indian hiring rhythms (e.g. post-Diwali hiring, financial year-end Q4 surges).

### Model 3: AutoETS (Exponential Smoothing State Space) ($M_2$)
Implements Holt-Winters / ETS state space formulation:
$$y_t = (\ell_{t-1} + b_{t-1}) \cdot s_{t-m} + \varepsilon_t$$
$$\ell_t = \ell_{t-1} + b_{t-1} + \alpha \frac{\varepsilon_t}{s_{t-m}}$$
$$b_t = b_{t-1} + \beta (\ell_t - \ell_{t-1})$$
$$s_t = s_{t-m} + \gamma \frac{\varepsilon_t}{\ell_t}$$
- Evaluates Additive and Multiplicative error, trend, and seasonal components.
- Chooses optimal hyperparameters $(\alpha, \beta, \gamma, \phi)$ by minimizing the Akaike Information Criterion ($\text{AIC}_c$).
- Produces analytical forecast distributions and prediction intervals:
  $$\hat{y}_{t+h} \pm z_{1-\alpha/2} \cdot \sigma_h$$

### Model 4: Autoregressive Gradient Boosted Trees (LightGBM) ($M_3$)
Formulates the forecasting task as a recursive autoregressive supervised tabular problem.
$$\hat{y}_{t+h} = f(\mathbf{x}_t)$$
**Feature Vector $\mathbf{x}_t$ includes:**
- **Autoregressive Lags:** $y_t, y_{t-1}, y_{t-2}, y_{t-3}, y_{t-6}, y_{t-12}$
- **Rolling Windows:** $\mu_{\text{roll}, 3}, \sigma_{\text{roll}, 3}, \mu_{\text{roll}, 6}, \sigma_{\text{roll}, 6}$
- **Linear Trend Slope:** Ordinary Least Squares slope over prior 6 months
- **Demand Signals:** Persistence days, employer count, posting quality index
- **Calendar Encodings:** Month sinusoidal cyclic features $\sin\left(\frac{2\pi m}{12}\right), \cos\left(\frac{2\pi m}{12}\right)$
- **Sectoral Covariates:** State industrial index, announced capital expenditure (capex) growth

---

## 3. Rolling Time-Series Cross-Validation Protocol

To guarantee that reported performance is realistic, we enforce **Rolling-Window Walk-Forward Validation** across $K = 6$ folds.

```
Fold 1: [--- Train: Months 1..18 ---] [ Test: 19..21 (h=3) ]
Fold 2: [--- Train: Months 1..19 ---] [ Test: 20..22 (h=3) ]
Fold 3: [--- Train: Months 1..20 ---] [ Test: 21..23 (h=3) ]
Fold 4: [--- Train: Months 1..21 ---] [ Test: 22..24 (h=3) ]
Fold 5: [--- Train: Months 1..22 ---] [ Test: 23..25 (h=3) ]
Fold 6: [--- Train: Months 1..23 ---] [ Test: 24..26 (h=3) ]
```

### 3.1 Evaluation Metrics

#### 1. Weighted Absolute Percentage Error (WAPE) - Primary Selection Metric
$$\text{WAPE} = \frac{\sum_{k=1}^K \sum_{h=1}^H |y_{k,h} - \hat{y}_{k,h}|}{\sum_{k=1}^K \sum_{h=1}^H y_{k,h}}$$
*Why WAPE over MAPE?* In labour market datasets, certain emerging skills or smaller districts have periods of near-zero demand. Standard MAPE divides by $y_t$, causing infinite or exploding values. WAPE aggregates before dividing, providing stable, robust percentages.

#### 2. Mean Absolute Error (MAE)
$$\text{MAE} = \frac{1}{K \cdot H} \sum_{k=1}^K \sum_{h=1}^H |y_{k,h} - \hat{y}_{k,h}|$$

#### 3. Mean Absolute Scaled Error (MASE)
$$\text{MASE} = \frac{\text{MAE}}{\frac{1}{N-1} \sum_{t=2}^N |y_t - y_{t-1}|}$$
A $\text{MASE} < 1.0$ mathematically proves that the model performs strictly better than the in-sample one-step naive baseline.

---

## 4. Model Selection Policy

For every $(d, s)$ series:
1. Compute $\text{WAPE}_M$ for all $M \in \{M_0, M_1, M_2, M_3\}$.
2. The candidate with the minimum $\text{WAPE}$ is selected as the winning model:
   $$M^* = \arg\min_{M} \text{WAPE}_M$$
3. **Safety Fallback Constraint:** If the best ML model ($M_3$) achieves a $\text{WAPE}$ improvement of less than $3\%$ over $M_2$ (AutoETS), $M_2$ is selected by default to favor parsimony and avoid overfitting on small samples.
4. Record selected model name, backtest WAPE, MAE, and MASE permanently in the `forecast_series` database record.

---

## 5. Explainability Architecture (SHAP + Evidence Decoupling)

A major failure of modern ML in government is presenting feature importance as causal fact. SkillPulse India enforces a strict two-tier decoupled explanation system.

```
+---------------------------------------------------------------------------------+
|                       TWO-TIER EXPLAINABILITY SYSTEM                            |
+---------------------------------------------------------------------------------+
|  TIER 1: Statistical Feature Contribution (TreeSHAP)                           |
|  - How much each input feature moved the model's base prediction (in units of y)|
|  - "lag_1_demand contributed +24.6 postings; trend_slope contributed +8.5"      |
|  - Explicit Disclaimer: "Statistical attribution != Econometric causality"      |
+---------------------------------------------------------------------------------+
|  TIER 2: Observable Empirical Ground Evidence (Institutional Indicators)        |
|  - Employer Diversification: HHI < 0.15 (Broad-based market demand)             |
|  - Vacancy Duration: 38 days average (Structural shortage indicator)           |
|  - Training Pipeline: Local ITI capacity running at 94% utilization            |
+---------------------------------------------------------------------------------+
```

### SHAP Formulation (LightGBM)
$$\hat{f}(\mathbf{x}) = \phi_0 + \sum_{j=1}^P \phi_j(\mathbf{x})$$
Where $\phi_0 = \mathbb{E}[f(\mathbf{X})]$ is the expected baseline, and $\phi_j$ is the Shapley value for feature $j$, satisfying efficiency, symmetry, and additivity.

---

## 6. Mathematical Formulation of the Confidence Engine

Every forecast projection must deliver a rigorous confidence score $C \in [0.0, 1.0]$ and an explicit textual justification.

$$C = w_1 \cdot C_{\text{density}} + w_2 \cdot C_{\text{accuracy}} + w_3 \cdot C_{\text{volatility}} + w_4 \cdot C_{\text{recency}}$$
With weights:
$$w_1 = 0.30, \quad w_2 = 0.35, \quad w_3 = 0.20, \quad w_4 = 0.15$$

### Component Formulations:

1. **Data Density Score ($C_{\text{density}}$):**
   $$C_{\text{density}} = \min\left(1.0, \frac{N_{\text{observed}}}{24}\right) \cdot (1 - \text{fraction\_missing})$$
   Full score requires at least 24 contiguous months of reporting history.

2. **Historical Accuracy Score ($C_{\text{accuracy}}$):**
   $$C_{\text{accuracy}} = \max\left(0.0, 1.0 - \text{WAPE}_{M^*}\right)$$
   Directly anchored to the winning model's out-of-sample backtested error.

3. **Series Stability Score ($C_{\text{volatility}}$):**
   $$CV = \frac{\sigma_y}{\mu_y + \epsilon}, \quad C_{\text{volatility}} = \frac{1}{1 + CV}$$
   Penalizes sporadic spikes and erratic zero-demand fluctuations.

4. **Reporting Recency Score ($C_{\text{recency}}$):**
   $$C_{\text{recency}} = \exp\left(-\frac{\Delta t_{\text{months\_since\_last\_data}}}{3}\right)$$

### Confidence Classification Rules:
- **HIGH:** $C \ge 0.75$ and $N \ge 18$ and $C_{\text{accuracy}} \ge 0.70$
- **MEDIUM:** $0.50 \le C < 0.75$
- **LOW:** $C < 0.50$ OR $N < 12$ OR Missing Data $> 25\%$

### Low-Data Alert Mechanism:
If $N < 12$ or missing data exceeds $25\%$:
- `low_data_flag = true`
- Confidence reason is populated with actionable feedback:
  > *"Caution: High uncertainty. Series possesses only {N} months of observation (minimum recommended: 24). Projections are anchored to state-level sectoral averages."*

---

## 7. Skill Ontology & Offline Embedding Vector Space

To achieve local, offline taxonomic reconciliation without cloud APIs:
- **Base Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2` (quantized ONNX runtime or PyTorch CPU, 22MB footprint).
- **Index:** FAISS FlatL2 / IndexFlatIP (Normalized Inner Product for Cosine Similarity).
- **Vocabulary:** 35 Canonical Skills + 240 Official NCO-2015 Titles + 450 Common Job Portal Aliases.
- **Decision Thresholds:**
  - $\text{Cosine} \ge 0.85$: Automated high-confidence mapping.
  - $0.70 \le \text{Cosine} < 0.85$: Flagged for human review.
  - $\text{Cosine} < 0.70$: Classified as UNMAPPED / NOVEL SKILL.
