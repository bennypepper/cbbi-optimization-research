"""
tests/test_trolololo.py
=======================
Quick validation of the Trolololo computation.
Run from PKL_v4 root:  python tests/test_trolololo.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import yfinance as yf
import pandas as pd
from src.data.trolololo import compute_trolololo, get_regression_params, validate_against_reference

print("=" * 60)
print("STEP 1 - Fetching BTC-USD price history from yfinance...")
print("=" * 60)
btc = yf.download("BTC-USD", start="2012-01-01", auto_adjust=True, progress=False)
btc_close = btc["Close"].squeeze()
btc_close = btc_close.dropna()
print(f"Data range : {btc_close.index[0].date()} to {btc_close.index[-1].date()}")
print(f"Total rows : {len(btc_close)}")

print()
print("=" * 60)
print("STEP 2 - Regression parameters")
print("=" * 60)
params = get_regression_params(btc_close)
for k, v in params.items():
    print(f"  {k:<15}: {v}")

print()
print("=" * 60)
print("STEP 3 - Sample Trolololo values")
print("=" * 60)
trololo = compute_trolololo(btc_close)

sample_dates = [
    "2017-12-17",  # 2017 bull peak (~$20k)
    "2021-11-10",  # 2021 all-time high (~$69k)
    "2022-11-21",  # 2022 bear bottom (~$15.5k)
    "2023-01-01",  # early 2023
    "2024-01-01",  # post-halving buildup
    "2025-01-01",  # latest in master_dataset
]

print(f"{'Date':<15} | {'Trolololo':>10} | {'BTC Price (USD)':>16}")
print("-" * 48)
for d in sample_dates:
    try:
        ts = pd.Timestamp(d)
        idx = trololo.index.get_indexer([ts], method="nearest")[0]
        actual_date = trololo.index[idx]
        val = trololo.iloc[idx]
        price = btc_close.iloc[idx]
        print(f"{str(actual_date.date()):<15} | {val:>10.2f} | ${price:>15,.0f}")
    except Exception as e:
        print(f"{d:<15} | ERROR: {e}")

# Today
latest_idx = trololo.last_valid_index()
if latest_idx:
    print(f"{str(latest_idx.date()):<15} | {trololo[latest_idx]:>10.2f} | ${btc_close[latest_idx]:>15,.0f}  <- TODAY")

print()
print("=" * 60)
print("STEP 4 - Validation against professor's reference (26.7)")
print("=" * 60)
result = validate_against_reference(btc_close)
for k, v in result.items():
    print(f"  {k:<15}: {v}")

print()
print("NOTE: If status is FAIL, adjust BAND_MIN and BAND_MAX in")
print("      src/data/trolololo.py until 'computed' is close to 26.7")
