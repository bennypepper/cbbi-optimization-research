import pandas as pd

print("=" * 60)
print("SPOT CHECK - cbbi_dataset.csv")
print("=" * 60)
df = pd.read_csv("data/processed/cbbi_dataset.csv", index_col="date", parse_dates=True)

print(f"Shape         : {df.shape}")
print(f"Date range    : {df.index.min().date()} -> {df.index.max().date()}")
print(f"in_sample     : {(df['phase']=='in_sample').sum()} baris")
print(f"out_of_sample : {(df['phase']=='out_of_sample').sum()} baris")
print(f"fill_flag=True: {df['fill_flag'].sum()} baris")
print(f"Any NaN       : {df.isnull().any().any()}")

print()
print("Nilai min/max setiap kolom indikator:")
ind_cols = ["cbbi_confidence","pi_cycle","rupl","rhodl_ratio","puell_multiple","two_year_ma_mult","trolololo","mvrv_zscore","reserve_risk","woobull"]
for c in ind_cols:
    print(f"  {c:<22}: min={df[c].min():.2f}, max={df[c].max():.2f}")

print()
print("Spot check 3 tanggal:")
for d in ["2012-01-01", "2021-01-01", "2026-03-15"]:
    row = df.loc[d]
    print(f"  {d}: cbbi_confidence={row['cbbi_confidence']:.2f}, btc_close={row['btc_close']}, phase={row['phase']}")

print()
print("Dtypes:")
print(df.dtypes.to_string())
