# Bitcoin Trading Parameter Optimization via Grid Search

**Optimalisasi Parameter Trading Bitcoin Menggunakan Grid Search pada Tiga Metrik Evaluasi Berbasis Indikator Logarithmic Regression**

> This repository is the research backbone for a PKL (Practicum Kerja Lapangan) research project.
> It covers **Phases 1–3**: data pipeline, statistical feature selection, and the backtesting optimization engine.
> The interactive web dashboard (Phase 4) lives in a [separate repository](https://github.com/bennypepper/btc-strategy-lab).

---

## Overview

Many popular Bitcoin on-chain indicators exist (Pi Cycle Top, MVRV Z-Score, Puell Multiple, Logarithmic Regression, etc.), but there is no empirical study comparing which indicator is statistically the strongest trading signal, nor any data-driven method for determining optimal buy/sell thresholds.

This research builds a rigorous quantitative framework that (1) selects the best indicator via Spearman correlation, (2) optimizes threshold and allocation parameters via exhaustive grid search, and (3) measures actual performance across In-Sample and Out-of-Sample periods.

The engine runs a full grid search over **1,293,750 parameter combinations** across two complementary research scenarios, evaluating three objectives: Total Return, Maximum Drawdown, and Sharpe Ratio.

---

## Research Objectives

1. **Identify the best indicator:** Which Bitcoin on-chain indicator has the highest statistical significance as a trading signal, based on Spearman correlation across 5 lag windows and Kruskal-Wallis distribution testing?
2. **Find optimal parameter values:** What buy/sell threshold pair and allocation percentage optimizes performance across three evaluation metrics (Total Return, Maximum Drawdown, Sharpe Ratio) via grid search?
3. **Measure actual IS vs OOS performance:** How do optimal parameters perform on In-Sample (2012–2020) vs Out-of-Sample (2021–2026) data, and what is the magnitude of degradation?

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
| **1 — Data Pipeline** | Parse 10 on-chain indicators from CBBI dataset + independently compute Logarithmic Regression from yfinance BTC price data + fetch BTC OHLC; build lookahead-free master dataset | `data/processed/master_dataset.parquet` |
| **2 — Feature Selection** | Spearman correlation (5 lag windows) + Kruskal-Wallis distribution test; rank all 10 indicators; select Logarithmic Regression as best signal | `analysis/selected_indicators.json` |
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
>
> **Note:** The `trolololo` column in the master dataset is **NOT taken from this XLSX file**. It is computed independently from BTC price data using logarithmic regression (see `src/data/trolololo.py`). This eliminates *Index Revision Bias*. The XLSX is still required for all other 8 indicators.

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
# Supports [1] Historical parquet or [2] Live yfinance + independent Trolololo
python -m src.optimization.verify_manual
```

---

## Project Structure

```
btc-trading-optimization/
├── src/
│   ├── data/
│   │   ├── loader.py           # CBBI XLSX parser + yfinance BTC price fetcher
│   │   ├── preprocessor.py     # Dataset merge, forward-fill, phase tagging, Trolololo injection
│   │   └── trolololo.py        # Independent Trolololo calc (logarithmic regression, yfinance)
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

**1. Best Indicator: Logarithmic Regression**

Phase 2 analysis ranked 10 on-chain indicators by Spearman correlation across 5 lag windows. Logarithmic Regression achieved the highest composite score (0.6819) with Spearman ρ = −0.4698 at 90-day lag, significantly outperforming all other indicators. This indicator is computed independently from BTC price data via Dynamic Channel Normalization, with no dependency on third-party APIs.

**2. Optimal Parameters Found (3 Risk Profiles)**

| Profile | Buy Threshold | Sell Threshold | Alloc Buy | Alloc Sell | Return (Full) | CAGR |
|---|---|---|---|---|---|---|
| Aggressive (Max Return) | 5 | 96 | 25% | 15% | 912,316× | 162.9%/yr |
| Conservative (Min Drawdown) | 1 | 61 | 1% | 15% | 1,642× | 68.4%/yr |
| Balanced (Max Sharpe) | 1 | 57 | 21% | 3% | 104,303× | 125.6%/yr |

**3. Performance Degradation (Overfitting Evidence)**

Scenario 1 (Aggressive profile): parameters yielding **125,702×** return on In-Sample (CAGR 268.6%/yr) produced **3.74×** (profit of +273.75%, CAGR +28.9%/yr) on Out-of-Sample. The magnitude gap is **33,610×**, providing empirical proof of performance degradation due to the transition from the early hyper-growth era to a mature cycle, highlighting the importance of In-Sample/Out-of-Sample separation. Note that all strategy profiles still beat the Buy & Hold OOS benchmark (+19.0% CAGR) with much lower drawdowns.

**Independent Design to Bypass Index Revision Bias**

During web application validation, third-party composite CBBI values were found to shift retroactively when the formula is updated (documented drift of +14.48 points on 2021-01-01 between research snapshot and live API). To eliminate this instrument-level limitation, the primary Logarithmic Regression indicator is computed locally using Dynamic Channel Normalization and is completely immune to external API revisions.

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

| | Scenario 1: Academic Validation | Scenario 2: Maximum Exploration |
|---|---|---|
| **Purpose** | Prove out-of-sample robustness | Map the absolute historical maximum |
| **Optimization data** | In-Sample: 2012–2020 | Full dataset: 2012–2026 |
| **Validation** | Forward test on OOS: 2021–2026 | None (intentional) |
| **Lookahead bias** | None (strictly isolated) | Present (explicitly disclosed) |
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
| 8 CBBI indicators (pi_cycle, rupl, rhodl_ratio, puell_multiple, two_year_ma_mult, mvrv_zscore, reserve_risk, woobull) + composite score | [cbbi.info](https://cbbi.info), the official CBBI dataset | Free, manual download |
| **Logarithmic Regression** *(updated 2026-04-27)* | Computed independently via `src/data/trolololo.py` from BTC-USD daily close prices (yfinance). Eliminates Index Revision Bias. | Free, auto-computed |
| BTC daily open/close prices | [Yahoo Finance](https://finance.yahoo.com) via `yfinance` | Free, auto-fetched |

> ⚠️ **Dataset Snapshot Notice:** The CBBI dataset used in this research is a **static snapshot** taken at the time of Phase 1 pipeline execution. The ColintalksCrypto API retroactively updates its historical values when the index formula changes. Results from this repository are reproducible only against the frozen `master_dataset.parquet`, not against a live API query of the same date range.

---

## Disclaimer

This project is a **research artifact** completed as part of a PKL (Practicum Kerja Lapangan) research program. All content is for educational and academic purposes only. Nothing in this repository constitutes financial advice. Cryptocurrency markets carry substantial risk, and past performance does not guarantee future results.

Optimal parameters reported in this repository are calibrated against a specific frozen snapshot of the CBBI dataset. Deploying these parameters against the live API without re-optimization may yield different performance outcomes due to retroactive formula revisions by the index author. This limitation is caused by retroactive formula updates by the index author.

---

## License

[MIT License](LICENSE)

---

*Stack: Python · pandas · NumPy · Numba · scipy · yfinance · joblib · matplotlib · seaborn*
