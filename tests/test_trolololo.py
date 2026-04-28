"""
tests/test_trolololo.py
=======================
Validation of the Trolololo dynamic channel normalization.
Run from PKL_v4 root:  py -3.11 tests/test_trolololo.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import yfinance as yf
import pandas as pd
from src.data.trolololo import (
    compute_trolololo,
    get_channel_params,
    get_cycle_marks,
    validate_against_reference,
    CONFIRMED_HIGHS,
    CONFIRMED_LOWS,
    ORIGIN_DATE,
)

print("=" * 65)
print("STEP 1 - Fetching BTC-USD price history from yfinance...")
print("=" * 65)
btc = yf.download("BTC-USD", start="2012-01-01", auto_adjust=True, progress=False)
if isinstance(btc.columns, pd.MultiIndex):
    btc.columns = btc.columns.get_level_values(0)
btc_close = btc["Close"].squeeze().dropna()
btc_close.index = pd.to_datetime(btc_close.index).tz_localize(None)
print(f"Data range : {btc_close.index[0].date()} to {btc_close.index[-1].date()}")
print(f"Total rows : {len(btc_close)}")

print()
print("=" * 65)
print("STEP 2 - Cycle marks (confirmed + algorithmic)")
print("=" * 65)
high_marks, low_marks = get_cycle_marks(btc_close)
print(f"Confirmed HIGH dates : {CONFIRMED_HIGHS}")
print(f"Confirmed LOW dates  : {CONFIRMED_LOWS}")
print(f"Total high marks in dataset : {high_marks.sum()}")
print(f"Total low  marks in dataset : {low_marks.sum()}")
hi_dates = [str(btc_close.index[i].date()) for i in range(len(btc_close)) if high_marks[i]]
lo_dates = [str(btc_close.index[i].date()) for i in range(len(btc_close)) if low_marks[i]]
print(f"High mark dates in data     : {hi_dates}")
print(f"Low  mark dates in data     : {lo_dates}")

print()
print("=" * 65)
print("STEP 3 - Channel regression parameters")
print("=" * 65)
params = get_channel_params(btc_close)
for k, v in params.items():
    print(f"  {k:<30}: {v}")

print()
print("=" * 65)
print("STEP 4 - Sample Trolololo values (sanity check)")
print("=" * 65)
trololo = compute_trolololo(btc_close)

# Expected behavior:
#   2017-12-17 (2017 peak)     : should be HIGH (70-100)
#   2021-11-10 (2021 ATH)      : should be HIGH (70-100, ideally near 100)
#   2022-11-21 (2022 bottom)   : should be LOW  (0-30)
#   2018-12-15 (2018 bottom)   : should be LOW  (0-30)
#   2024-01-01 (post-halving)  : should be MID  (20-60)

sample_dates = [
    ("2015-01-14", "2015 bear bottom  [expect LOW  0-30] "),
    ("2017-12-17", "2017 bull peak    [expect HIGH 70-100]"),
    ("2018-12-15", "2018 bear bottom  [expect LOW  0-30] "),
    ("2021-11-10", "2021 ATH          [expect HIGH 70-100]"),
    ("2022-11-21", "2022 bear bottom  [expect LOW  0-30] "),
    ("2023-06-01", "mid 2023          [expect MID  20-60] "),
    ("2024-01-01", "Jan 2024          [expect MID  30-70] "),
]

print(f"{'Date':<13} | {'Value':>7} | {'BTC Price':>13} | Note")
print("-" * 75)
for d, note in sample_dates:
    try:
        ts  = pd.Timestamp(d)
        idx = trololo.index.get_indexer([ts], method="nearest")[0]
        val   = trololo.iloc[idx]
        price = btc_close.iloc[idx]
        date_str = str(trololo.index[idx].date())
        print(f"{date_str:<13} | {val:>7.2f} | ${price:>12,.0f} | {note}")
    except Exception as e:
        print(f"{d:<13} | ERROR: {e}")

# Latest value
latest_idx = trololo.last_valid_index()
if latest_idx:
    val   = trololo[latest_idx]
    price = btc_close[latest_idx]
    print(f"{str(latest_idx.date()):<13} | {val:>7.2f} | ${price:>12,.0f} | <- TODAY")

print()
print("=" * 65)
print("STEP 5 - Zero/NaN audit (2023-01-01 historical bug check)")
print("=" * 65)
suspect_dates = ["2021-01-01", "2022-01-01", "2023-01-01", "2024-01-01"]
print(f"{'Date':<13} | {'Trolololo':>10} | {'BTC Close':>13}")
print("-" * 42)
for d in suspect_dates:
    ts  = pd.Timestamp(d)
    idx = trololo.index.get_indexer([ts], method="nearest")[0]
    val   = trololo.iloc[idx]
    price = btc_close.iloc[idx]
    flag  = " <-- SUSPICIOUS (was 0.00 in old XLSX)" if val < 1.0 else ""
    print(f"{str(trololo.index[idx].date()):<13} | {val:>10.2f} | ${price:>12,.0f}{flag}")

print()
print("=" * 65)
print("STEP 6 - Current value report")
print("=" * 65)
result = validate_against_reference(btc_close)
for k, v in result.items():
    print(f"  {k:<15}: {v}")
print()
print("Dynamic channel formula active. No fixed reference value needed.")
print("Verify sanity: cycle peaks should be near 100, bottoms near 0.")
