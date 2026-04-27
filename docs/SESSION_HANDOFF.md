
---

## 10. Session Log — April 27, 2026

### 10.1 Trolololo Formula — Scientific Basis

The Trolololo indicator is a **Power Law**, not merely a logarithmic regression. Key references:

- **Original post (2014):** Trololo user on BitcoinTalk — `https://bitcointalk.org/index.php?topic=831547.0`
  - Used mixed-log formula: `log10(price) = D * ln(days) - C` (non-standard)

- **Power Law reframe (Santostasi, 2024):** Giovanni Santostasi on Medium.
  - Correct form: `Price = A * days^n` or `log10(price) = n * log10(days) + log10(A)`
  - Fitted values: n ~= 5.83, A = 10^(-17)
  - Article: `https://giovannisantostasi.medium.com/btc-trolololo-model-revisited-still-valid-today-is-really-a-power-law-in-disguise-da11b58cf5de`

**Our implementation uses the Power Law (log10-log10) formulation**, which is scientifically superior. Our fitted slope of 5.8936 is consistent with Santostasi's n ~= 5.83 (small difference due to more recent data).

This can and should be cited in the research report methodology section.

### 10.2 Methodology Note — Genesis Date Choice

- Genesis Block (Bitcoin network started): **January 3, 2009**
- First Bitcoin transaction (Satoshi to Hal Finney): **January 9, 2009**
- **We use January 9, 2009** — consistent with many public Trolololo implementations.
- The 6-day difference is absorbed by the calibration constants.

### 10.3 Data Quality Issues Found (Old master_dataset)

The old `master_dataset.parquet` (sourced from CBBI XLSX) had confirmed bad values:
- `2023-01-01`: `trolololo = 0.00` — invalid zero (should be ~18)
- `2022-06-01`: `btc_close = $43,145` — date alignment error (actual BTC was ~$31k)

These are fully resolved by rebuilding from yfinance in Step 2.

### 10.4 Files Created/Modified This Session

| File | Action | Notes |
|---|---|---|
| `src/data/trolololo.py` | CREATED | Core Trolololo module, calibrated to 26.71 |
| `tests/test_trolololo.py` | CREATED | Validation script |
| `data/metadata/source_notes.md` | UPDATED | Added capture date (Mar 16, 2026), revision note |
| `docs/LAPORAN_KOMPREHENSIF.md` | UPDATED | Fixed dataset capture date |
| `docs/RESEARCH_UPDATE_PLAN.md` | UPDATED | This file — all findings documented |
| `ARCHITECTURE.md` | REWRITTEN | Converted from Indonesian to English |
| `check_data.py` | TO DELETE | Temp diagnostic script in repo root |

---

## 11. Agent Handoff Brief

> **READ THIS FIRST if you are a new agent continuing this work.**

### What This Project Is

A Bitcoin trading strategy optimization research project. The core research is DONE (Phases 1-4 completed). This update revises the **signal column** (`trolololo`) from a CBBI-sourced value to an independently computed Power Law regression. The research structure, optimization engine, and web app UI do NOT change.

### Where Everything Is

```
Research repo : D:\Personal Projects\PKL_v4
                GitHub: bennypepper/cbbi-optimization-research

Web app repo  : D:\Personal Projects\PKL_webapp
                GitHub: bennypepper/cbbi-strategy-lab

Python to use : C:\Users\Benny Pepper\AppData\Local\Programs\Python\Python311\python.exe
                (Python 3.14 is in PATH but is a bare install — always use Python311)
```

### Documents to Read Before Doing Anything

Read these in order:

1. `docs/RESEARCH_UPDATE_PLAN.md` (this file) — full plan, what is done, what is next
2. `src/data/trolololo.py` — the new Trolololo module (Phase 1, already done)
3. `data/metadata/source_notes.md` — dataset provenance and methodology notes
4. `src/data/preprocessor.py` — the file to modify in Step 2
5. `PKL_webapp/core/data_loader.py` — the file to modify in Step 4

### Current Status of Steps

| Step | Description | Status |
|---|---|---|
| Step 0 | Delete `check_data.py` from repo root | Pending (minor) |
| Step 1 | Write `src/data/trolololo.py` | DONE — calibrated to 26.71 |
| **Step 2** | Rebuild `master_dataset.parquet` | **START HERE** |
| Step 3 | Re-run Phase 3 grid search (6 runs, ~2 min) | After Step 2 |
| Step 4 | Update `PKL_webapp/core/data_loader.py` | After Step 3 |
| Step 5 | Update webapp page references | After Step 4 |
| Step 6 | Copy results files to webapp data/ folder | After Step 5 |
| Step 7 | End-to-end validation | After Step 6 |
| Step 8 | Update documentation | After Step 7 |

### Step 2 — Exact Instructions

Modify `PKL_v4/src/data/preprocessor.py`, specifically the `build_master_dataset()` function.
Add these two lines after the master dataframe is assembled:

```python
from src.data.trolololo import compute_trolololo
df["trolololo"] = compute_trolololo(df["btc_close"])
```

Then:
1. Run the preprocessor to regenerate `data/processed/master_dataset.parquet`
2. Verify `df["trolololo"]["2023-01-01"]` is NOT 0.00 (was a bad value before)
3. Verify `df["trolololo"]["2026-04-27"]` is close to 26.71

### Step 3 — Running Phase 3

```powershell
# First delete old trial logs
Remove-Item "D:\Personal Projects\PKL_v4\results\trial_log\*.parquet"

# Then find and run the optimization scripts in src/optimization/
# Each run takes ~19 seconds with Numba JIT
# 6 total runs (2 scenarios x 3 objectives)
```

### Critical Rules — Do NOT Touch

- `analysis/indicator_ranking.csv` — Phase 2 results, still valid, leave alone
- `analysis/selected_indicators.json` — leave alone
- `analysis/spearman_results.csv` — leave alone
- `src/optimization/engine.py` — backtesting engine, no changes needed
- `CBBI_dataset.xlsx` — still needed for other indicator columns, do not delete
- `reports/` folder — all .md files, leave alone

### Key Invariant for Step 3

The optimization engine reads column `"trolololo"` from the master dataset.
As long as the rebuilt parquet has that column with [0-100] float values, Phase 3
runs without any code changes to the engine.

### Do NOT Re-run Phase 2

Phase 2 (Spearman indicator ranking) does NOT need to be re-run.
The conclusion (Trolololo ranked #1 with composite score 0.6557) was reached
with CBBI-sourced values and remains valid. The analysis files are the
formal record of the research and must not be altered.
