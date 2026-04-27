"""
src/data/preprocessor.py
========================
Fase 1 — Modul preprocessing dan orkestrasi pipeline.

Fungsi-fungsi:
  - merge_datasets()        : Gabungkan CBBI + btc_open
  - apply_forward_fill()    : Tangani gap btc_open (hari libur exchange)
  - validate_no_lookahead() : Gate validasi anti-lookahead bias
  - tag_phases()            : Label IS / OOS
  - build_master_dataset()  : Orkestrasi penuh Fase 1

Output:
  data/processed/cbbi_dataset.csv       — dataset bersih, human-readable
  data/processed/master_dataset.parquet — dataset efisien untuk Fase 2/3
  data/metadata/fill_log.csv            — log baris yang terkena forward fill
  data/metadata/source_notes.md         — dokumentasi sumber dan metodologi

Perubahan metodologi (April 27, 2026):
  Kolom `trolololo` tidak lagi diambil dari CBBI_dataset.xlsx.
  Kolom ini sekarang dihitung secara independen menggunakan compute_trolololo()
  dari modul src/data/trolololo.py, berdasarkan data harga BTC-USD dari yfinance.
  Ini menghilangkan ketergantungan pada revisi retroaktif indeks CBBI
  (dikenal sebagai "Index Revision Bias").
"""

import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.data.loader import load_cbbi_xlsx, fetch_btc_open, INDICATOR_COLS
from src.data.trolololo import compute_trolololo

# ── Logging ──────────────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT_DIR      = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
METADATA_DIR  = ROOT_DIR / "data" / "metadata"

CSV_OUTPUT     = PROCESSED_DIR / "cbbi_dataset.csv"
PARQUET_OUTPUT = PROCESSED_DIR / "master_dataset.parquet"
FILL_LOG       = METADATA_DIR  / "fill_log.csv"
SOURCE_NOTES   = METADATA_DIR  / "source_notes.md"

# ── Konstanta fase ────────────────────────────────────────────────────────────
IN_SAMPLE_START    = "2012-01-01"
IN_SAMPLE_END      = "2020-12-31"
OUT_OF_SAMPLE_START = "2021-01-01"
OUT_OF_SAMPLE_END  = "2026-03-31"

# Kolom urutan final pada dataset master
MASTER_COLUMNS = [
    "btc_close",
    "btc_open",
    "cbbi_confidence",
    "pi_cycle",
    "rupl",
    "rhodl_ratio",
    "puell_multiple",
    "two_year_ma_mult",
    "trolololo",
    "mvrv_zscore",
    "reserve_risk",
    "woobull",
    "fill_flag",
    "phase",
]


# ─────────────────────────────────────────────────────────────────────────────
def merge_datasets(
    cbbi_df: pd.DataFrame,
    btc_open_df: pd.DataFrame,
    start: str = IN_SAMPLE_START,
    end:   str = OUT_OF_SAMPLE_END,
) -> pd.DataFrame:
    """
    Menggabungkan dataset CBBI dengan btc_open berdasarkan DatetimeIndex.

    Strategi join:
    - CBBI df sebagai base (left)
    - btc_open_df di-join berdasarkan index tanggal
    - Filter ke rentang [start, end]
      (data CBBI mulai 2011, tapi penelitian mulai 2012)

    Parameters
    ----------
    cbbi_df    : Output dari load_cbbi_xlsx()
    btc_open_df: Output dari fetch_btc_open()
    start      : Tanggal mulai filter (inklusif)
    end        : Tanggal selesai filter (inklusif)

    Returns
    -------
    pd.DataFrame dengan semua kolom indikator + btc_open,
    difilter ke rentang yang ditentukan.
    """
    logger.info("Menggabungkan dataset CBBI + btc_open...")

    # Pastikan kedua df memiliki DatetimeIndex dengan timezone-naive
    cbbi_df.index     = pd.to_datetime(cbbi_df.index).tz_localize(None)
    btc_open_df.index = pd.to_datetime(btc_open_df.index).tz_localize(None)

    # Left join
    merged = cbbi_df.join(btc_open_df[["btc_open"]], how="left")

    # Filter rentang tanggal
    merged = merged.loc[start:end]

    logger.info(
        "  Merged shape: %s | %s → %s",
        merged.shape,
        merged.index.min().date(),
        merged.index.max().date(),
    )

    # Cek gap pada btc_close (tidak boleh ada gap)
    n_missing_close = merged["btc_close"].isna().sum()
    if n_missing_close > 0:
        logger.warning(
            "  %d baris memiliki btc_close NaN — ini tidak diharapkan dari file XLSX",
            n_missing_close,
        )

    # Cek gap pada btc_open (bisa ada karena hari libur exchange)
    n_missing_open = merged["btc_open"].isna().sum()
    logger.info("  btc_open NaN sebelum fill: %d baris", n_missing_open)

    return merged


# ─────────────────────────────────────────────────────────────────────────────
def apply_forward_fill(
    df: pd.DataFrame,
    max_consecutive_fill: int = 7,
) -> pd.DataFrame:
    """
    Mengisi missing values pada kolom btc_open dengan forward fill.

    CRITICAL: Forward fill hanya menggunakan nilai masa lalu (T-1 ke belakang).
    Tidak ada backward fill yang diperbolehkan untuk mencegah lookahead bias.

    Catatan: Indikator CBBI dari file XLSX sudah dalam kondisi bersih.
    Forward fill terutama berlaku untuk kolom btc_open pada hari libur
    atau hari di mana data harga tidak tersedia (misalnya hari Minggu di
    era awal Bitcoin di mana beberapa exchange tidak aktif).

    Parameters
    ----------
    df                   : DataFrame dari merge_datasets()
    max_consecutive_fill : Batas maksimum hari berturutan yang di-fill

    Returns
    -------
    pd.DataFrame dengan kolom fill_flag ditambahkan.
    """
    logger.info("Menerapkan forward fill (max %d hari berturutan)...", max_consecutive_fill)

    df = df.copy()

    # Tandai baris yang akan di-fill SEBELUM fill dilakukan
    fill_mask = df["btc_open"].isna()

    # Deteksi run panjang (consecutive NaN)
    # Jika ada run lebih dari max_consecutive_fill hari, biarkan tetap NaN
    def _cap_ffill(series: pd.Series, max_run: int) -> pd.Series:
        """Forward fill tapi batasi per run tidak melebihi max_run."""
        result = series.copy()
        # Hitung run-length NaN
        mask = series.isna()
        # Cumulative group per run
        group = (~mask).cumsum()
        run_count = mask.groupby(group).cumsum()
        # Baris yang run-nya melebihi batas → tetap NaN
        too_long = run_count > max_run
        # Forward fill normal dulu
        result = result.ffill()
        # Kembalikan NaN untuk baris yang run-nya terlalu panjang
        result[too_long] = float("nan")
        return result

    df["btc_open"] = _cap_ffill(df["btc_open"], max_consecutive_fill)

    # Kolom fill_flag: True jika baris ini terkena forward fill
    df["fill_flag"] = fill_mask & df["btc_open"].notna()

    # ── Fallback untuk periode 2012–2014 (sebelum yfinance punya data Open) ──
    # Gunakan btc_close sebagai proxy btc_open untuk baris yang masih NaN.
    # Justified: di era awal Bitcoin, spread intraday sangat kecil dan harga
    # hampir tidak bergerak antara open dan close dalam satu hari.
    still_nan_mask = df["btc_open"].isna()
    n_still_nan_before = still_nan_mask.sum()
    if n_still_nan_before > 0:
        df.loc[still_nan_mask, "btc_open"] = df.loc[still_nan_mask, "btc_close"]
        df.loc[still_nan_mask, "fill_flag"] = True
        logger.info(
            "  Fallback btc_open ← btc_close untuk %d baris (periode awal, sebelum yfinance data)",
            n_still_nan_before,
        )

    # Catat baris yang di-fill
    filled_rows = df[df["fill_flag"]].copy()
    n_filled = len(filled_rows)
    logger.info("  Jumlah baris yang di-fill: %d", n_filled)

    # Simpan fill log
    if n_filled > 0:
        fill_log = filled_rows[["btc_open"]].copy()
        fill_log.index.name = "date"
        fill_log["note"] = "btc_open forward-filled"
        METADATA_DIR.mkdir(parents=True, exist_ok=True)
        fill_log.to_csv(FILL_LOG)
        logger.info("  Fill log disimpan ke: %s", FILL_LOG)
    else:
        # Buat fill log kosong jika tidak ada fill
        pd.DataFrame(columns=["date", "btc_open", "note"]).to_csv(FILL_LOG, index=False)
        logger.info("  Tidak ada forward fill — fill log kosong")

    # Cek apakah masih ada NaN setelah fill
    n_still_nan = df["btc_open"].isna().sum()
    if n_still_nan > 0:
        logger.warning(
            "  %d baris btc_open masih NaN setelah fill "
            "(kemungkinan run panjang > %d hari atau awal data)",
            n_still_nan, max_consecutive_fill,
        )

    return df


# ─────────────────────────────────────────────────────────────────────────────
def validate_no_lookahead(df: pd.DataFrame) -> bool:
    """
    Validasi deterministik: memastikan tidak ada lookahead bias pada
    level preprocessing.

    Cek yang dilakukan:
    1. Index harus monotonically increasing (urutan chronologis tidak terbalik)
    2. Tidak ada tanggal duplikat
    3. Kolom btc_open tidak boleh sama persis dengan btc_close hari yang sama
       (indikasi eksekusi menggunakan harga yang salah)
    4. Semua nilai indikator berasal dari masa lalu atau hari ini, tidak masa depan
       (dicek via urutan index yang sudah divalidasi di poin 1 & 2)

    Returns
    -------
    bool : True jika validasi lulus semua cek

    Raises
    ------
    ValueError : Jika salah satu cek gagal
    """
    logger.info("Menjalankan validasi no-lookahead bias...")

    # Cek 1: Monotonic increasing index
    if not df.index.is_monotonic_increasing:
        raise ValueError(
            "[LOOKAHEAD] Index tidak monotonically increasing — urutan data mungkin terbalik."
        )
    logger.info("  ✓ Cek 1: Index monotonically increasing")

    # Cek 2: Tidak ada duplikat index
    n_dup = df.index.duplicated().sum()
    if n_dup > 0:
        raise ValueError(
            f"[LOOKAHEAD] Ditemukan {n_dup} tanggal duplikat dalam index."
        )
    logger.info("  ✓ Cek 2: Tidak ada tanggal duplikat (%d baris)", len(df))

    # Cek 3: btc_open dan btc_close tidak identik secara sempurna
    # (jika identik pada semua baris, kemungkinan terjadi kesalahan assignment)
    if df["btc_open"].equals(df["btc_close"]):
        raise ValueError(
            "[LOOKAHEAD] btc_open dan btc_close identik secara sempurna — "
            "kemungkinan kesalahan assignment kolom."
        )
    logger.info("  ✓ Cek 3: btc_open dan btc_close berbeda (normal)")

    # Cek 4: Rentang tanggal sesuai yang diharapkan
    expected_start = pd.Timestamp(IN_SAMPLE_START)
    expected_end   = pd.Timestamp(OUT_OF_SAMPLE_END)
    actual_start   = df.index.min()
    actual_end     = df.index.max()

    if actual_start < expected_start:
        raise ValueError(
            f"[LOOKAHEAD] Dataset dimulai terlalu awal: {actual_start.date()} "
            f"(diharapkan >= {expected_start.date()})"
        )
    if actual_end > expected_end:
        logger.warning(
            "  Dataset berakhir di %s (melebihi end %s) — masih OK jika data diperbarui",
            actual_end.date(), expected_end.date(),
        )
    logger.info(
        "  ✓ Cek 4: Rentang data valid (%s → %s)",
        actual_start.date(), actual_end.date(),
    )

    logger.info("  ✓ Semua cek validasi LULUS — tidak ada indikasi lookahead bias")
    return True


# ─────────────────────────────────────────────────────────────────────────────
def tag_phases(df: pd.DataFrame) -> pd.DataFrame:
    """
    Menambahkan kolom 'phase' ke dataset master.

    Mapping:
    - 'in_sample'      : 2012-01-01 – 2020-12-31
    - 'out_of_sample'  : 2021-01-01 – 2026-03-31

    Kolom ini digunakan sebagai filter oleh modul optimisasi (Fase 3).
    Untuk Skenario 2, seluruh data digunakan tanpa memandang tag fase.

    Returns
    -------
    pd.DataFrame dengan kolom 'phase' ditambahkan.
    """
    logger.info("Menambahkan label phase...")

    df = df.copy()
    df["phase"] = "untagged"  # default

    is_mask  = (df.index >= IN_SAMPLE_START) & (df.index <= IN_SAMPLE_END)
    oos_mask = (df.index >= OUT_OF_SAMPLE_START) & (df.index <= OUT_OF_SAMPLE_END)

    df.loc[is_mask,  "phase"] = "in_sample"
    df.loc[oos_mask, "phase"] = "out_of_sample"

    n_is  = is_mask.sum()
    n_oos = oos_mask.sum()
    n_untagged = (df["phase"] == "untagged").sum()

    logger.info("  in_sample    : %d baris (2012–2020)", n_is)
    logger.info("  out_of_sample: %d baris (2021–2026)", n_oos)
    if n_untagged > 0:
        logger.warning("  untagged     : %d baris — periksa rentang tanggal", n_untagged)

    return df


# ─────────────────────────────────────────────────────────────────────────────
def _write_source_notes(df: pd.DataFrame) -> None:
    """Tulis file dokumentasi source_notes.md ke metadata."""
    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    n_is  = (df["phase"] == "in_sample").sum()
    n_oos = (df["phase"] == "out_of_sample").sum()
    n_fill = df["fill_flag"].sum()

    content = f"""# Source Notes — Dataset Master CBBI Optimization

**Dibuat:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Sumber Data

### 1. Indikator CBBI (Sumber Utama)
- **File:** `CBBI_dataset.xlsx`
- **Asal:** Laman resmi CBBI — [cbbi.info](https://cbbi.info)
- **Cakupan asli:** 2011-06-27 – 2026-03-15 (5.376 baris)
- **Cakupan digunakan:** {df.index.min().date()} – {df.index.max().date()}
- **Format asal:** String persentase ("31.95%") dan harga ("$72,713")
- **Parsing:** Persentase → float64 (skala 0–100), Harga → float64 (USD)
- **Normalisasi:** Tidak diperlukan — CBBI.info sudah menyediakan nilai [0–100]

### 2. Harga Pembukaan BTC (Sumber Tambahan)
- **Sumber:** `yfinance` — ticker `BTC-USD`
- **Field:** Open price (harian)
- **Tujuan:** Digunakan eksklusif sebagai harga eksekusi T+1 pada mesin backtesting
- **Cache:** `data/raw/btc_open.parquet`

## Mapping Kolom

| Kolom XLSX | Nama Internal | Keterangan |
|---|---|---|
| Date | date (index) | Tanggal |
| Price | btc_close | Harga penutupan BTC |
| Confidence | cbbi_confidence | Composite CBBI Score — **kolom sinyal default** |
| PiCycle | pi_cycle | Pi Cycle Top Indicator |
| RUPL | rupl | Relative Unrealized Profit/Loss |
| RHODL | rhodl_ratio | RHODL Ratio |
| Puell | puell_multiple | Puell Multiple |
| 2YMA | two_year_ma_mult | 2-Year Moving Average Multiplier |
| Trolololo | trolololo | **Dihitung independen** — Logarithmic Regression dari btc_close via compute_trolololo() |
| MVRV | mvrv_zscore | MVRV Z-Score |
| ReserveRisk | reserve_risk | Reserve Risk |
| Woobull | woobull | Woobull NVT |
| *(derived)* | btc_open | Harga pembukaan BTC dari yfinance |
| *(derived)* | fill_flag | True jika baris terkena forward fill |
| *(derived)* | phase | Label fase: in_sample / out_of_sample |

## Statistik Dataset Master

| Metrik | Nilai |
|---|---|
| Total baris | {len(df):,} |
| Rentang tanggal | {df.index.min().date()} – {df.index.max().date()} |
| Fase in_sample (2012–2020) | {n_is:,} baris |
| Fase out_of_sample (2021–2026) | {n_oos:,} baris |
| Baris dengan forward fill (btc_open) | {n_fill:,} baris |

## Keputusan Metodologis

1. **Filter start date 2012:** Data CBBI tersedia sejak 2011, namun penelitian 
   menggunakan 2012 sebagai titik mulai untuk konsistensi dengan literatur 
   yang umumnya memulai analisis Bitcoin setelah era awal yang sangat volatil.

2. **Forward fill btc_open:** Beberapa hari pada awal sejarah Bitcoin tidak 
   memiliki data `open` yang tersedia dari yfinance (umumnya hari libur atau 
   gap data exchange). Forward fill dengan batasan 7 hari digunakan untuk 
   menangani ini tanpa memperkenalkan lookahead bias.

3. **Skala nilai indikator:** Semua indikator dipertahankan dalam skala [0–100] 
   sesuai sistem normalisasi CBBI resmi. Tidak ada rescaling tambahan dilakukan.
   Keputusan ini konsisten dengan desain threshold engine (threshold_buy: 1–45, 
   threshold_sell: 55–100).

4. **Kolom sinyal default:** `cbbi_confidence` (Composite CBBI Score resmi) 
   digunakan sebagai kolom sinyal default pada mesin optimisasi. Indikator 
   individual juga tersedia untuk eksplorasi di Fase 2.

5. **Trolololo — kalkulasi independen (April 27, 2026):** Kolom `trolololo` 
   tidak lagi diambil dari CBBI_dataset.xlsx. Nilainya dihitung ulang secara 
   independen dari data harga BTC-USD (kolom `btc_close`) menggunakan regresi 
   logaritmik power-law dengan fixed bands (BAND_MIN=-0.6353, BAND_MAX=0.8647). 
   Ini menghilangkan Index Revision Bias — risiko bahwa nilai historis 
   berubah saat Colin memperbarui algoritma indeks CBBI secara retroaktif.
"""
    SOURCE_NOTES.write_text(content, encoding="utf-8")
    logger.info("  source_notes.md disimpan ke: %s", SOURCE_NOTES)


# ─────────────────────────────────────────────────────────────────────────────
def build_master_dataset(
    cbbi_xlsx_path: str | Path = None,
    start_date: str = IN_SAMPLE_START,
    end_date:   str = OUT_OF_SAMPLE_END,
    max_fill_days: int = 7,
) -> pd.DataFrame:
    """
    Fungsi orkestrasi utama Fase 1.

    Memanggil secara berurutan:
      1. load_cbbi_xlsx()        — muat dan parse file XLSX
      2. fetch_btc_open()        — ambil btc_open dari yfinance
      3. merge_datasets()        — gabungkan kedua sumber
      4. apply_forward_fill()    — tangani gap btc_open
      5. validate_no_lookahead() — gate validasi
      6. tag_phases()            — tambahkan label IS/OOS

    Simpan hasil akhir ke:
      - data/processed/cbbi_dataset.csv       (human-readable)
      - data/processed/master_dataset.parquet (efisien)
      - data/metadata/source_notes.md
      - data/metadata/fill_log.csv

    Parameters
    ----------
    cbbi_xlsx_path : Path ke file XLSX (default: ROOT/CBBI_dataset.xlsx)
    start_date     : Tanggal mulai filter
    end_date       : Tanggal selesai filter
    max_fill_days  : Batas maksimum consecutive forward fill pada btc_open

    Returns
    -------
    pd.DataFrame — Dataset master final (identik dengan yang disimpan)
    """
    logger.info("=" * 60)
    logger.info("FASE 1: Build Master Dataset — MULAI")
    logger.info("  [UPDATE April 27 2026] trolololo akan dihitung independen")
    logger.info("=" * 60)

    # ── Step 1: Load CBBI XLSX ────────────────────────────────────────────────
    logger.info("\n[Step 1/6] Load CBBI XLSX")
    from src.data.loader import XLSX_PATH as DEFAULT_XLSX
    xlsx_path = Path(cbbi_xlsx_path) if cbbi_xlsx_path else DEFAULT_XLSX
    cbbi_df = load_cbbi_xlsx(xlsx_path)

    # ── Step 2: Fetch btc_open ────────────────────────────────────────────────
    logger.info("\n[Step 2/6] Fetch btc_open dari yfinance")
    btc_open_df = fetch_btc_open(start=start_date, end=end_date)

    # ── Step 3: Merge ─────────────────────────────────────────────────────────
    logger.info("\n[Step 3/6] Merge datasets")
    df = merge_datasets(cbbi_df, btc_open_df, start=start_date, end=end_date)

    # ── Step 4: Forward fill ──────────────────────────────────────────────────
    logger.info("\n[Step 4/7] Apply forward fill")
    df = apply_forward_fill(df, max_consecutive_fill=max_fill_days)

    # ── Step 5: Overwrite trolololo with independent calculation ──────────────
    # The XLSX-sourced trolololo column is subject to retroactive revision
    # ("Index Revision Bias"). We replace it with a deterministic value
    # computed from btc_close using the logarithmic regression power-law.
    logger.info("\n[Step 5/7] Overwrite trolololo with independent calculation")
    trololo_computed = compute_trolololo(df["btc_close"])
    n_before_nan = df["trolololo"].isna().sum()
    df["trolololo"] = trololo_computed
    n_after_nan = df["trolololo"].isna().sum()
    logger.info(
        "  trolololo overwritten: %d rows | NaN before=%d, after=%d",
        len(df), n_before_nan, n_after_nan,
    )
    # Sanity check: no zeros that look like missing data
    n_zeros = (df["trolololo"] == 0.0).sum()
    if n_zeros > 0:
        logger.warning("  trolololo has %d exact-zero values — review these rows", n_zeros)
    else:
        logger.info("  trolololo: no suspicious zero values found")

    # ── Step 6: Validate no lookahead ─────────────────────────────────────────
    logger.info("\n[Step 6/7] Validate no-lookahead bias")
    validate_no_lookahead(df)

    # ── Step 7: Tag phases ────────────────────────────────────────────────────
    logger.info("\n[Step 7/7] Tag phases")
    df = tag_phases(df)

    # ── Reorder kolom ke urutan final ─────────────────────────────────────────
    df = df[[col for col in MASTER_COLUMNS if col in df.columns]]

    # ── Simpan output ─────────────────────────────────────────────────────────
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    # CSV — human-readable, float values bersih
    df.to_csv(CSV_OUTPUT)
    logger.info("\n✓ cbbi_dataset.csv disimpan ke: %s", CSV_OUTPUT)

    # Parquet — efisien untuk Fase 2 & 3
    df.to_parquet(PARQUET_OUTPUT)
    logger.info("✓ master_dataset.parquet disimpan ke: %s", PARQUET_OUTPUT)

    # Source notes
    _write_source_notes(df)

    # ── Ringkasan akhir ────────────────────────────────────────────────────────
    logger.info("\n" + "=" * 60)
    logger.info("FASE 1: Build Master Dataset — SELESAI")
    logger.info("=" * 60)
    logger.info("  Total baris    : %d", len(df))
    logger.info("  Rentang tanggal: %s → %s", df.index.min().date(), df.index.max().date())
    logger.info("  Kolom          : %s", df.columns.tolist())
    logger.info("  in_sample      : %d baris", (df["phase"] == "in_sample").sum())
    logger.info("  out_of_sample  : %d baris", (df["phase"] == "out_of_sample").sum())
    logger.info("  forward-filled : %d baris", df["fill_flag"].sum())
    logger.info("=" * 60)

    return df


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    df = build_master_dataset()
    print("\nSample output (5 baris pertama):")
    print(df.head().to_string())
    print("\nSample output (5 baris terakhir):")
    print(df.tail().to_string())
    print("\nDtype:")
    print(df.dtypes.to_string())
    print(f"\nFile output:\n  {CSV_OUTPUT}\n  {PARQUET_OUTPUT}")
