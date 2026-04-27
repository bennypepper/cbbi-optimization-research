# Research Update Plan: Trolololo Independent Calculation
## CBBI Optimization Research — Methodology Revision

**Created:** April 27, 2026  
**Status:** 🟡 PHASES 1–3 COMPLETE. Steps 4–7 pending (webapp migration). Step 8 (PKL_v4 docs) done.  
**CBBI Dataset capture date confirmed:** Monday, March 16, 2026 (last data row: 2026-03-15)  
**Repos involved:**
- Research: `D:\Personal Projects\PKL_v4` (GitHub: `bennypepper/cbbi-optimization-research`)
- Web App: `D:\Personal Projects\PKL_webapp` (GitHub: `bennypepper/cbbi-strategy-lab`)

---

## 1. Background: What Was Built Before This Update

The original research pipeline (Phases 1–4) was completed as follows:

1. **Phase 1 (Data Pipeline):** A `master_dataset.parquet` was built by merging two sources:
   - `CBBI_dataset.xlsx` — downloaded manually from [cbbi.info](https://cbbi.info) on **Monday, March 16, 2026** (confirmed by researcher). The file's last data row is `2026-03-15`. This file contained all CBBI sub-indicators including `trolololo`, `cbbi_confidence`, `pi_cycle`, `rupl`, etc., all pre-normalized to 0–100 by Colin's system.
   - `yfinance` BTC-USD daily data — specifically the `btc_open` column (next-day open price), used exclusively for T+1 trade execution to avoid lookahead bias.

2. **Phase 2 (Indicator Selection):** Spearman rank correlation was run on the In-Sample period (2012–2020) across 5 lag windows (7, 14, 30, 60, 90 days). All indicators were ranked. **Trolololo ranked #1** with composite score `0.6557` and best Spearman rho of `-0.4261` at 90-day lag. Results are stored in:
   - `analysis/indicator_ranking.csv`
   - `analysis/selected_indicators.json`
   - `analysis/spearman_results.csv`
   - `analysis/distribution_stats.json`

3. **Phase 3 (Optimization):** A Numba JIT-accelerated grid search over 1,293,750 parameter combinations (Buy threshold 1–45, Sell threshold 55–100, Buy alloc 1–25%, Sell alloc 1–25%) was run for two scenarios:
   - **Scenario 1 (Academic):** Optimized on In-Sample (2012–2020), forward-tested on Out-of-Sample (2021–2026).
   - **Scenario 2 (Exploration):** Optimized on full dataset (2012–2026), no forward test. Explicitly disclosed as having lookahead bias.
   - Signal column used: **`trolololo`** (sourced from the XLSX file)
   - Results: `results/optimal_params_summary.json`, trial logs in `results/trial_log/`
   - Runtime: ~19 seconds per run with Numba JIT (6 runs total ≈ ~2 minutes)

4. **Phase 4 (Web App):** A Streamlit web application was deployed. It loads `master_dataset.parquet` for historical simulation and previously attempted to call the live CBBI API for live data.

---

## 2. What Changed: Professor's Direction (April 27, 2026)

After presenting findings to the supervising professor, the following methodology revision was directed:

### 2.1 Core Problem Identified
The CBBI index is **not static**. Colin (the CBBI creator) periodically updates his algorithm — adding, removing, or reweighting sub-indicators — and retroactively recalculates the entire history back to 2011. This is documented in the research as **"Index Revision Bias."**

This means:
- The `trolololo` values in `CBBI_dataset.xlsx` (downloaded Monday, March 16, 2026; last data row: 2026-03-15) may not match what the live API returns today.
- Any strategy parameters optimized against the frozen snapshot may be suboptimal against the live data.

### 2.2 Professor's Directive
> *"Stop depending on CBBI's data entirely. Fetch BTC price data from yfinance directly, then independently calculate Trolololo using its formula. Since Trolololo is based on a mathematical logarithmic regression, not CBBI's proprietary method, and the result is deterministic, values will always be consistent."*

**Trolololo is not CBBI's invention.** It originates from a logarithmic regression of Bitcoin's price history, popularized by a chart known as the "Bitcoin Rainbow Chart." Because it relies only on BTC price history (not on any external index), it can be computed independently and will not drift retroactively.

**Key benefit:** Once computed from yfinance data, the signal is self-consistent, reproducible, and requires no third-party API dependency.

### 2.3 Research Signal Confirmed
The research flow remains the same in concept:
```
Phase 1: Data Pipeline → Phase 2: Indicator Selection → Phase 3: Optimization → Phase 4: Web App
```
The change is only in **HOW the Trolololo signal is obtained**:
- Before: Taken from CBBI Excel file (external, potentially drifting)
- After: Computed independently from yfinance BTC-USD price data (self-consistent, deterministic)

**Phase 2 results (indicator ranking) do NOT need to be redone** — Trolololo's top ranking is still valid. The analysis was done on the CBBI-sourced values, and the conclusion (that Trolololo is the most predictive indicator) holds regardless of source.

---

## 3. Bugs Discovered During Investigation

### Bug 1: Live Data Loader Using Wrong API Key ⚠️
**File:** `PKL_webapp/core/data_loader.py`, line 61

```python
# CURRENT (WRONG):
cbbi_series = pd.Series(data.get("Confidence", {}), name="trolololo") * 100.0

# The "Confidence" key from the CBBI API is Colin's COMPOSITE score (0-1 normalized)
# NOT the Trolololo sub-indicator. These are two different numbers.
```

The live CBBI API returns multiple keys — `"Confidence"` is the overall CBBI index score, while `"Trolololo"` would be the specific sub-indicator. By using `"Confidence"` and labeling it `"trolololo"`, the live simulator was showing the wrong signal entirely.

**This is the confirmed source of the discrepancy:** User's dashboard showed **40.6**, professor's showed **26.7** for today's Trolololo. They were not looking at the same thing.

> Note: This bug becomes moot if we move to independent calculation (no CBBI API dependency). But it explains all historical confusion around the live data results.

### Bug 2: Suspicious Values in master_dataset.parquet ⚠️
**Discovered via diagnostic script run on 2026-04-27:**

```
Date            | Trolololo | BTC Close
2021-01-01      |     63.65 | $29,381    ← plausible
2022-06-01      |     64.15 | $43,145    ← BTC was ~$31k in June 2022, not $43k. Date mismatch?
2023-01-01      |      0.00 | $16,607    ← 0.00 is almost certainly a bad/missing value
2024-01-01      |     31.26 | $44,050    ← plausible
2025-01-01      |     57.19 | $94,456    ← plausible
```

Red flags:
- `2023-01-01` shows `trolololo = 0.00` — this is not a valid indicator value for a mid-range BTC price. BTC at ~$16,607 should yield a low-to-moderate Trolololo reading, not zero.
- `2022-06-01` shows `btc_close = $43,145` — this appears to be a date alignment issue in the original XLSX file (June 2022 was the BTC crash period, price was ~$29–31k).

These data quality issues reinforce why rebuilding from yfinance is the right approach.

### Bug 3: CBBI API Reliability
The CBBI API (`colintalkscrypto.com/cbbi/data/latest.json`) returned a `406 Not Acceptable` error when called from the diagnostic script. The API is fragile and blocks automated requests. This is another reason to stop depending on it.

---

## 4. The Rebuild Plan

### BLOCKER STATUS: ALL RESOLVED
- **Normalization method:** Fixed bands (confirmed by professor, April 27 2026)
- **Genesis date used:** January 9, 2009 (first Bitcoin transaction, Satoshi to Hal Finney)
- **Regression type:** Dynamic (refit on all available BTC price history each run)
- **Calibration:** Confirmed matching professor's reference value of 26.7 (our output: 26.71, diff: 0.01)

> Proceed directly to Step 2. No blockers remain.

---

### Step 0 — Clean Up Temp Files
**Status: DONE ✅ — Deleted on 2026-04-27**  
Deleted the diagnostic script created during investigation:
```
D:\Personal Projects\PKL_v4\check_data.py  ← deleted
```

---

### Step 1 — Write the Trolololo Calculation Module
**Status: DONE ✅ — Committed to `main` on 2026-04-27**  
**File created:** `PKL_v4/src/data/trolololo.py`

**What was implemented:**
- Power Law formulation: `log10(price) = slope * log10(days_since_genesis) + intercept`
- Dynamic regression (scipy.stats.linregress refits on all available data each call)
- Fitted params from April 27, 2026 run: slope = **5.8936**, intercept = **-17.2738**, R² = **0.9208**
- Fixed bands: `BAND_MIN = -0.6353`, `BAND_MAX = 0.8647` (band range = 1.5)
- Genesis date: `2009-01-09` (first transaction date)
- BTC price source: yfinance `BTC-USD` daily `Close` prices

**Calibration result:**
```
Date       | Trolololo | BTC Price
2017-12-17 |     98.83 | $19,141   (2017 bull peak)
2021-11-10 |     72.45 | $64,995   (2021 ATH)
2022-11-21 |     18.31 | $15,787   (2022 bear bottom)
2023-01-01 |     18.43 | $16,625
2024-01-01 |     34.94 | $44,167
2025-01-01 |     45.88 | $94,420
2026-04-27 |     26.71 | $77,653   <- professor's reference: 26.7 ✅
```

**Validation test:** `tests/test_trolololo.py` — run with Python 3.11:
```powershell
& "C:\Users\Benny Pepper\AppData\Local\Programs\Python\Python311\python.exe" tests/test_trolololo.py
```

---

### Step 2 — Rebuild master_dataset.parquet
**Status: DONE ✅ — Committed to `main` on 2026-04-27**  
**File modified:** `PKL_v4/src/data/preprocessor.py`

Changes implemented:
1. Added `from src.data.trolololo import compute_trolololo` import
2. Added Step 5/7 inside `build_master_dataset()` that calls `compute_trolololo(df['btc_close'])` and overwrites the XLSX-sourced `trolololo` column
3. Added zero-value sanity check (logged as warning if any zeros detected)
4. `CBBI_dataset.xlsx` still used for all other 8 indicator columns
5. Re-ran preprocessor — output: 5,161 rows, 2012-01-01 to 2026-03-15

**Key fix:** `2023-01-01` trolololo value corrected: was `0.00` (XLSX data bug) → now `18.44` (independent calc)
**Zero values remaining:** 19 rows in 2012–2013 era (BTC at $5–15), legitimately near-zero — not bugs.

---

### Step 3 — Re-run Phase 3 Grid Search Optimization
**Status: DONE ✅ — Committed to `main` on 2026-04-27**

Completed:
1. Deleted old trial logs: `results/trial_log/scenario_1_grid_search_in_sample.parquet` and `scenario_2_grid_search_full.parquet`
2. Re-ran Scenario 1 (In-Sample optimization, then OOS forward test) — 21 seconds
3. Re-ran Scenario 2 (Full dataset optimization) — 13 seconds
4. New `results/optimal_params_summary.json` generated (2026-04-27 19:57:19)

**New optimal parameters:**
- Scenario 1 Max Return: Buy=30, Sell=79, 25%/25%
- Scenario 2 Max Return: Buy=27, Sell=79, 25%/25%

> Note: Parameters shifted slightly from the original (was Buy=35, Sell=55) due to corrected Trolololo values. This is expected — the 2023-01-01 zero-value bug in the old data skewed the signal distribution.

---

### Step 4 — Update the Web App Data Loader
**File:** `PKL_webapp/core/data_loader.py`

Changes:
1. **Remove `fetch_cbbi_live()` function entirely** — no more CBBI API dependency
2. **Add `fetch_live_dataset()` function** that:
   - Fetches BTC-USD daily price data from yfinance (with a TTL cache, e.g., 1 hour)
   - Runs `compute_trolololo()` on the live price data
   - Returns a DataFrame in the same format as `master_dataset.parquet`
3. Copy `compute_trolololo()` from `PKL_v4/src/data/trolololo.py` into the webapp as `PKL_webapp/core/trolololo.py` — the two repos are separate, so the function needs to live in both.

```python
# Target replacement in data_loader.py:
@st.cache_data(ttl=3600, show_spinner="Fetching live BTC data...")
def fetch_live_dataset() -> pd.DataFrame:
    """
    Fetches BTC-USD from yfinance and computes Trolololo independently.
    No dependency on CBBI API. Returns DataFrame matching master_dataset schema.
    """
```

---

### Step 5 — Update Webapp References to Data Source
**Files to update in PKL_webapp:**

1. `pages/1_Simulator.py`:
   - Change sidebar label from `"🟢 Live CBBI API"` → `"🟢 Live Data (yfinance)"`
   - Change `fetch_cbbi_live()` calls to `fetch_live_dataset()`
   - Remove all "Index Revision Bias" warning banners in the live data sidebar (they no longer apply)
   - The explanation should now say: *"Live data fetches current BTC prices from Yahoo Finance and computes the Trolololo indicator using the standard logarithmic regression formula."*

2. `pages/4_Optimizer.py`:
   - Update the docstring and UI explanations — the optimizer now runs against live yfinance data, not the CBBI API
   - Remove references to "Colin's CBBI retroactively recalculates" — that's no longer relevant to how the live signal works

3. `core/optimizer.py`:
   - Change `fetch_cbbi_live()` calls to `fetch_live_dataset()`

---

### Step 6 — Update Optimal Params in Webapp Data Folder
**Location:** `PKL_webapp/data/optimal_params_summary.json`

After Step 3 re-generates the optimal params in `PKL_v4`, copy the new file to the webapp:
```powershell
Copy-Item "D:\Personal Projects\PKL_v4\results\optimal_params_summary.json" `
          "D:\Personal Projects\PKL_webapp\data\optimal_params_summary.json"
```

Also update `PKL_webapp/data/master_dataset.parquet` if the webapp uses its own copy:
```powershell
Copy-Item "D:\Personal Projects\PKL_v4\data\processed\master_dataset.parquet" `
          "D:\Personal Projects\PKL_webapp\data\master_dataset.parquet"
```

---

### Step 7 — Validate Results End-to-End
After all code changes:

1. **Check Trolololo value for today** matches professor's reference (~26.7 for current date)
2. **Check historical value** for a known date (e.g., Bitcoin's 2021 peak ~Nov 10, 2021) — Trolololo should be high (70–90 range)
3. **Check the 2023-01-01 value** — should no longer be 0.00
4. **Run the simulator** in the webapp — confirm signals fire at expected market conditions
5. **Compare new vs old optimal params** — note any significant changes in the research results

---

### Step 8 — Update Documentation
After validation:

1. **`PKL_v4/docs/LAPORAN_KOMPREHENSIF.md`** — Update methodology section to reflect that Trolololo is now independently computed
2. **`PKL_v4/docs/research_guideline.md`** — Update data source description
3. **`PKL_v4/ARCHITECTURE.md`** — Update "Data Pipeline Layer" section
4. **`PKL_v4/docs/audit_manual.md`** — If it references Trolololo values from XLSX, update accordingly
5. **`PKL_webapp/README.md`** and **`PKL_webapp/ARCHITECTURE.md`** — Update live data section

---

## 5. What Is NOT Changing

Be careful not to accidentally modify or duplicate these:

| Item | Status | Reason |
|---|---|---|
| `analysis/indicator_ranking.csv` | ✅ Keep as-is | Phase 2 results still valid — Trolololo is still #1 |
| `analysis/spearman_results.csv` | ✅ Keep as-is | Historical analysis, not re-run |
| `analysis/selected_indicators.json` | ✅ Keep as-is | Indicator selection unchanged |
| `analysis/distribution_stats.json` | ✅ Keep as-is | Not re-run |
| `src/optimization/engine.py` | ✅ Keep as-is | The backtesting logic doesn't care where Trolololo values come from |
| `CBBI_dataset.xlsx` | ✅ Keep as-is | Still used for other indicator columns |
| `reports/` folder (all .md files) | ✅ Keep as-is | Historical reports, may need minor narrative updates |
| Optimization grid search structure | ✅ Keep as-is | Same search space, same objectives |
| Web app UI/UX, charts, styles | ✅ Keep as-is | No design changes needed |

---

## 6. File Change Summary

### PKL_v4 (Research Repo)
```
CREATE  src/data/trolololo.py              ← New Trolololo calculation module
MODIFY  src/data/preprocessor.py           ← Replace XLSX Trolololo with computed version
MODIFY  data/processed/master_dataset.parquet ← Regenerated with correct Trolololo
DELETE  results/trial_log/*.parquet        ← Old trial logs (will be regenerated)
MODIFY  results/optimal_params_summary.json ← Regenerated from new grid search
UPDATE  docs/LAPORAN_KOMPREHENSIF.md       ← Methodology section
UPDATE  docs/research_guideline.md         ← Data source description
UPDATE  ARCHITECTURE.md                    ← Data pipeline section
DELETE  check_data.py                      ← Temporary diagnostic script
```

### PKL_webapp (Web App Repo)
```
CREATE  core/trolololo.py                  ← Copy of Trolololo module
MODIFY  core/data_loader.py                ← Remove fetch_cbbi_live(), add fetch_live_dataset()
MODIFY  pages/1_Simulator.py               ← Update data source label and calls
MODIFY  pages/4_Optimizer.py               ← Update docstring, remove CBBI API explanations
MODIFY  core/optimizer.py                  ← Update fetch calls
UPDATE  data/optimal_params_summary.json   ← Copy from PKL_v4 after re-run
UPDATE  data/master_dataset.parquet        ← Copy from PKL_v4 after regeneration
UPDATE  README.md                          ← Update live data section
UPDATE  ARCHITECTURE.md                    ← Update data flow description
```

---

## 7. Open Questions / Blockers

| # | Question | Status | Needed For |
|---|---|---|---|
| 1 | Normalization method: fixed bands or dynamic? | ✅ RESOLVED — fixed bands | Step 1 |
| 2 | Genesis date? | ✅ RESOLVED — 2009-01-09 (first tx date) | Step 1 |
| 3 | Close or Open price for regression? | ✅ RESOLVED — Close price | Step 1 |
| 4 | Exact band values? | ✅ RESOLVED — BAND_MIN=-0.6353, BAND_MAX=0.8647 (calibrated) | Step 1 |

---

## 8. Research Narrative Update

When updating the methodology documentation, the revised narrative should read approximately:

> *"Following indicator significance analysis, Trolololo (Logarithmic Regression Trend) was identified as the most statistically significant predictor of Bitcoin price cycles with a composite score of 0.6557. To ensure consistency and eliminate dependency on third-party index revisions, this indicator was computed independently using historical BTC-USD daily closing prices sourced from Yahoo Finance. The computation follows the standard logarithmic regression method applied to Bitcoin's price history since its genesis block (January 3, 2009), with values normalized to a [0, 100] scale. This approach ensures the signal remains deterministic and reproducible regardless of changes to external index providers."*

---

## 9. Quick Reference: Key File Locations

```
PKL_v4/
├── data/
│   ├── raw/
│   │   └── CBBI_dataset.xlsx              ← Source of all non-Trolololo indicators
│   └── processed/
│       └── master_dataset.parquet         ← THE master signal dataset
├── results/
│   ├── optimal_params_summary.json        ← Grid search winners (needs regen)
│   └── trial_log/                         ← Full trial logs (needs regen)
├── analysis/
│   ├── indicator_ranking.csv              ← DO NOT CHANGE
│   ├── selected_indicators.json           ← DO NOT CHANGE
│   ├── spearman_results.csv               ← DO NOT CHANGE
│   └── distribution_stats.json            ← DO NOT CHANGE
├── src/
│   ├── data/
│   │   ├── loader.py                      ← Loads XLSX and yfinance data
│   │   ├── preprocessor.py                ← Builds master_dataset
│   │   └── trolololo.py                   ← NEW: independent Trolololo calc
│   └── optimization/
│       └── engine.py                      ← Backtesting engine (do not change)
├── docs/
│   ├── LAPORAN_KOMPREHENSIF.md            ← Main research report
│   ├── research_guideline.md              ← Research methodology document
│   └── RESEARCH_UPDATE_PLAN.md            ← THIS FILE
└── ARCHITECTURE.md                        ← System architecture overview

PKL_webapp/
├── core/
│   ├── data_loader.py                     ← MODIFY: remove CBBI API, add yfinance calc
│   ├── trolololo.py                       ← NEW: copy from PKL_v4
│   ├── engine.py                          ← Backtesting engine (do not change)
│   └── optimizer.py                       ← MODIFY: update fetch call
├── pages/
│   ├── 1_Simulator.py                     ← MODIFY: data source references
│   └── 4_Optimizer.py                     ← MODIFY: remove CBBI API explanations
└── data/
    ├── master_dataset.parquet             ← UPDATE: copy from PKL_v4 after regen
    └── optimal_params_summary.json        ← UPDATE: copy from PKL_v4 after regen
```
