# CBBI Optimization Research

**Quantitative optimization of Bitcoin trading strategies using CBBI (Crypto Bull/Bear Index) on-chain indicators.**

> This repository is the research backbone for a PKL (Practicum Kerja Lapangan) research project.
> It covers **Phases 1–3**: data pipeline, statistical feature selection, and the backtesting optimization engine.
> The interactive web dashboard (Phase 4) lives in a [separate repository](https://github.com/yourusername/cbbi-dashboard) *(coming soon)*.

---

## Overview

The CBBI (Crypto Bull/Bear Index) aggregates nine on-chain Bitcoin metrics into a single composite confidence score [0–100]. In practice, traders apply intuitive thresholds — "buy when below 30, sell when above 70" — without any empirical basis for those values.

This research builds a rigorous quantitative framework to answer: **what are the actual optimal thresholds and allocation sizes, and how robust are they out of sample?**

The engine runs a full grid search over **1,293,750 parameter combinations** across two complementary research scenarios, evaluating three objectives: Total Return, Maximum Drawdown, and Sharpe Ratio.

---

## Research Questions

1. Which CBBI sub-indicator has the highest statistical significance as a trading signal basis?
2. What buy/sell threshold pair and asset allocation percentage maximizes Total Return?
3. What configuration minimizes Maximum Drawdown and maximizes Sharpe Ratio?
4. How much does performance degrade between In-Sample and Out-of-Sample (Scenario 1), and how does that compare to the historical maximum found in Scenario 2?

---

## Four-Phase Architecture

```
Phase 1 ── Data Pipeline & Preprocessing
Phase 2 ── Indicator Selection & Statistical Analysis
Phase 3 ── Dual-Scenario Optimization Engine & Validation  ◄── This repo
Phase 4 ── Interactive Web Dashboard (separate repo)
```

---

## Phase Summary

| Phase | Description | Key Output |
|---|---|---|
| **1 — Data Pipeline** | Parse CBBI XLSX + fetch BTC OHLC via yfinance; build lookahead-free master dataset | `data/processed/master_dataset.parquet` |
| **2 — Feature Selection** | Spearman correlation (5 lag windows) + Kruskal-Wallis distribution test; rank all 9 indicators | `analysis/selected_indicators.json` |
| **3 — Optimization** | Numba-accelerated grid search (1.29M trials × 2 scenarios × 3 objectives); manual backtesting verification | `results/optimal_params_summary.json` |

---

## Quickstart

### Requirements

- Python 3.10+
- Install dependencies: `pip install -r requirements.txt`

### Data Setup

**Step 1 — CBBI Dataset**

Download the official CBBI dataset from [cbbi.info](https://cbbi.info) (export to Excel) and place the file at the project root:

```
CBBI_dataset.xlsx   ← place here
```

> The dataset contains daily values for all 9 CBBI sub-indicators and their composite score from 2011 to present. It is free and publicly available from the CBBI authors.

**Step 2 — BTC Price Data**

BTC open prices are fetched automatically via `yfinance` on first run and cached to `data/raw/btc_open.parquet`. No manual download required.

### Reproduce the Full Pipeline

```bash
# Phase 1 — Build master dataset
python -c "from src.data.preprocessor import build_master_dataset; build_master_dataset()"

# Phase 2 — Run feature selection and indicator ranking
python -c "from src.analysis.feature_selector import run_full_analysis; run_full_analysis()"

# Phase 3 — Run dual-scenario grid search optimization
python src/optimization/run_phase3.py

# Phase 3 — Interactive CLI for manual backtest verification
python src/optimization/verify_manual.py
```

---

## Project Structure

```
cbbi-optimization-research/
├── src/
│   ├── data/
│   │   ├── loader.py           # CBBI XLSX parser + yfinance BTC price fetcher
│   │   └── preprocessor.py     # Dataset merge, forward-fill, phase tagging
│   ├── analysis/
│   │   └── feature_selector.py # Spearman correlation + Kruskal-Wallis + ranking
│   └── optimization/
│       ├── engine.py           # Core backtesting logic (Numba-accelerated)
│       ├── grid_search.py      # Parallel exhaustive grid search runner
│       ├── run_phase3.py       # Phase 3 entrypoint (both scenarios, all objectives)
│       └── verify_manual.py    # Interactive CLI backtesting verifier
│
├── data/
│   ├── raw/                    # btc_open.parquet — auto-generated, not committed
│   ├── processed/              # master_dataset.parquet — generated, not committed
│   └── metadata/
│       ├── source_notes.md     # Data provenance and coverage documentation
│       └── fill_log.csv        # Forward-fill audit log
│
├── analysis/                   # Phase 2 outputs — committed (small, meaningful)
│   ├── spearman_results.csv
│   ├── distribution_stats.json
│   ├── indicator_ranking.csv
│   └── selected_indicators.json
│
├── results/
│   ├── optimal_params_summary.json  # ← Primary research output
│   └── trial_log/              # Large parquet files — not committed (regenerate locally)
│
├── reports/
│   ├── feature_selection_report.md
│   ├── phase3_methodology_notes.md
│   ├── phase3_results_overview.md
│   └── charts/                 # PNG visualizations — committed
│
├── PRD_CBBI_Optimization.md    # Full Product Requirements Document
├── audit_manual.md             # Phase 3 manual audit checklist
├── requirements.txt
└── .gitignore
```

---

## Key Findings

> Full quantitative results: [`results/optimal_params_summary.json`](results/optimal_params_summary.json)
> Narrative summary: [`reports/phase3_results_overview.md`](reports/phase3_results_overview.md)

**Primary Signal Indicator Selected (Phase 2):** `Trolololo` (Logarithmic Regression / Bitcoin Rainbow Chart)

Phase 2 analysis identified `trolololo` as statistically superior to the composite CBBI Confidence Score across all lag windows — the basis for using it as the optimization signal in Phase 3, rather than the default composite.

---

## Methodology

### Anti-Lookahead Bias Design

This is the most critical correctness requirement in the system:

| Rule | Implementation |
|---|---|
| Signal observed at close of day T | `indicator[T]` |
| Trade executed at open of day T+1 | `btc_open[T+1]` |
| Missing value handling | Forward fill only (never backward) |
| Validation gate | `validate_no_lookahead()` runs before every optimization |

### Two-Scenario Framework

Two scenarios run independently with identical parameter search spaces:

| | Scenario 1 — Academic Validation | Scenario 2 — Maximum Exploration |
|---|---|---|
| **Purpose** | Prove out-of-sample robustness | Map the absolute historical maximum |
| **Optimization data** | In-Sample: 2012–2020 | Full dataset: 2012–2026 |
| **Validation** | Forward test on OOS: 2021–2026 | None (intentional) |
| **Lookahead bias** | None — strictly isolated | Present — explicitly disclosed |
| **Role in report** | Scientific validity benchmark | Comparative reference ceiling |

> ⚠️ **Scenario 2 Disclosure:** Results represent retrospective maximum potential only. They cannot be interpreted as predictive signals. This is documented explicitly in `results/optimal_params_summary.json` under the `"disclosure"` field.

### Parameter Search Space

| Parameter | Range | Step | Values |
|---|---|---|---|
| Threshold Buy | 1 – 45 | 1 | 45 |
| Threshold Sell | 55 – 100 | 1 | 46 |
| Buy Allocation (% of cash) | 1% – 25% | 1% | 25 |
| Sell Allocation (% of BTC held) | 1% – 25% | 1% | 25 |
| **Total combinations** | | | **1,293,750** |

### Optimization Objectives

Three independent objectives per scenario:

| Objective | Direction |
|---|---|
| `max_return` | Maximize total return |
| `min_drawdown` | Minimize maximum drawdown |
| `max_sharpe` | Maximize Sharpe ratio |

---

## Data Sources

| Data | Source | Access |
|---|---|---|
| CBBI indicators (all 9) + composite score | [cbbi.info](https://cbbi.info) — official CBBI dataset | Free, manual download |
| BTC daily open/close prices | [Yahoo Finance](https://finance.yahoo.com) via `yfinance` | Free, auto-fetched |

---

## Disclaimer

This project is a **research artifact** completed as part of a PKL (Practicum Kerja Lapangan) research program. All content is for educational and academic purposes only. Nothing in this repository constitutes financial advice. Cryptocurrency markets carry substantial risk, and past performance does not guarantee future results.

---

## License

[MIT License](LICENSE)

---

*Stack: Python · pandas · NumPy · Numba · scipy · yfinance · joblib · matplotlib · seaborn*
