# System Architecture
## Bitcoin Trading Parameter Optimization via Grid Search

**Version:** 2.1  
**Status:** Production / Final  
**Last Updated:** 2026-06-09 — Updated to reflect revised research framing

---

## 1. Project Overview

This document outlines the technical architecture of the Bitcoin Trading Parameter Optimization System. The system evaluates 10 on-chain indicators to select the most statistically significant signal (Logarithmic Regression / Trolololo), then optimizes trading parameters via exhaustive grid search across three evaluation metrics (Total Return, Maximum Drawdown, Sharpe Ratio).

The architecture is modularized into four core layers:
1. **Data Pipeline Layer:** Data ingestion, alignment, and preprocessing.
2. **Statistical Analysis Layer:** Indicator selection and significance testing.
3. **Optimization Engine Layer:** Multi-scenario parametric grid search.
4. **Presentation Layer:** Interactive web application for simulation and results.

---

## 2. Data Pipeline Layer

The data pipeline aggregates raw data from multiple sources into a single, cohesive master dataset, strictly enforcing anti-lookahead rules.

### 2.1 Data Sources
- **CBBI Source (XLSX):** Official daily index values (0-100) and indicator components (pi_cycle, rupl, rhodl_ratio, puell_multiple, two_year_ma_mult, mvrv_zscore, reserve_risk, woobull, cbbi_confidence) spanning from 2011 to 2026.
- **Trolololo — Independent Calculation *(Updated 2026-04-28)*:** The `trolololo` column is **no longer sourced from the CBBI XLSX**. It is computed independently from BTC-USD closing prices using the professor's **Dynamic Channel Normalization** formula (`src/data/trolololo.py`). This eliminates *Index Revision Bias* — the risk that Colin's retroactive formula updates silently shift historical signal values. The method uses two separate power-law base channels (`top_base = ln(10)×(2.900×ln(d+1400)−19.463)`, `bottom_base = ln(10)×(2.788×ln(d+1200)−19.463)`) where d = days since 2012-01-01, then fits linear regressions on residuals at confirmed historical cycle peaks (2017-12-17, 2021-11-10) and troughs (2015-01-14, 2018-12-15, 2022-11-21) to produce an adaptive channel. The index is normalized as `(price_log − channel_bottom) / (channel_top − channel_bottom)`, clipped to [0, 100].
- **Market Data (Yahoo Finance):** BTC-USD daily opening prices (`btc_open`), used exclusively for T+1 execution logic to prevent lookahead bias. Also used as the source for `btc_close`, which drives the Trolololo calculation.

### 2.2 Preprocessing Logic
- **Temporal Alignment:** Both sources are merged using a continuous daily `DatetimeIndex`.
- **Gap Handling:** Missing values (primarily weekend/holiday gaps in market data) are imputed using strict forward-fill (`ffill`), capped at a maximum of 7 consecutive days. Backward filling is strictly prohibited.
- **Phase Tagging:** Data is programmatically partitioned:
  - `in_sample`: 2012-01-01 to 2020-12-31
  - `out_of_sample`: 2021-01-01 to 2026-03-31

---

## 3. Statistical Analysis Layer

Before optimization, the system identifies the most statistically significant on-chain indicator to be used as the signal baseline.

### 3.1 Spearman Correlation Analysis
- Computes non-parametric Spearman rank correlation between indicator values and forward returns across multiple lag windows (7, 14, 30, 60, and 90 days).
- Assesses the predictive power of each sub-indicator independent of market regimes.

### 3.2 Market Regime Distribution
- Segments the market into four macro conditions: Accumulation, Neutral, Distribution, and Euphoria.
- Analyzes indicator distributions across these segments to rank indicators based on a composite score of correlation and statistical significance (p-value < 0.05).

---

## 4. Optimization Engine Layer

The optimization engine performs large-scale parameter searches to maximize specific objective functions.

### 4.1 Search Space & Parameters
The engine evaluates millions of combinations across four dimensions:
- **Buy Threshold:** 1 – 45 (Interval: 1)
- **Sell Threshold:** 55 – 100 (Interval: 1)
- **Buy Allocation:** 1% – 25% of available cash
- **Sell Allocation:** 1% – 25% of held BTC

### 4.2 Objective Functions
Optimization runs are executed independently targeting three primary objectives:
1. `max_return`: Maximize Total Return
2. `min_drawdown`: Minimize Maximum Drawdown
3. `max_sharpe`: Maximize Sharpe Ratio

### 4.3 Execution Scenarios
The system runs two distinct optimization scenarios to balance academic rigor with historical exploration:

#### Scenario 1: Academic Validation (Walk-Forward)
- **Training:** Optimized exclusively on the `in_sample` dataset.
- **Validation:** Best parameters are forward-tested on the unseen `out_of_sample` dataset.
- **Purpose:** Measures strategy robustness and quantifies performance degradation (overfitting).

#### Scenario 2: Maximum Historical Exploration
- **Training:** Optimized across the entire historical dataset.
- **Purpose:** Discovers the absolute theoretical limit of the strategy historically. Explicitly acknowledges lookahead bias and is used for reference, not prediction.

### 4.4 Search Algorithms
1. **Grid Search (Primary):** Exhaustive search utilizing `joblib` for parallel execution across all parameter permutations.
2. **Bayesian Optimization (Fallback):** Utilizes `Optuna` (TPE sampler) when search spaces expand beyond reasonable compute times.
3. **Genetic Algorithm:** Heuristic alternative for expansive multi-objective optimization.

---

## 5. Presentation Layer (Web Application)

The final layer is a Streamlit-based interactive web application deployed to cloud infrastructure.

### 5.1 Architecture Flow
- **Frontend UI:** Streamlit interface providing responsive layout and metric visualizations.
- **Backend Logic:** Connects to pre-computed results (`optimal_params.json` and `.parquet` trial logs) to ensure low-latency rendering.
- **Live Simulator:** An embedded backtesting engine that allows users to test custom parameter combinations on the fly against historical datasets.

### 5.2 Key Features
- **Scenario Comparison:** Side-by-side breakdown of Scenario 1 (IS vs OOS) and Scenario 2 metrics.
- **Interactive Backtesting:** Users can adjust thresholds and allocations to simulate unique risk profiles (Aggressive, Moderate, Conservative).
- **Transparency & Disclaimers:** UI strictly separates academic walk-forward results from the full-dataset exploration, explicitly defining the implications of index revision bias and lookahead limitations.
