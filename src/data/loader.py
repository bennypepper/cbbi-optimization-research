"""
src/data/loader.py
==================
Fase 1 — Modul pemuatan data mentah.

Dua fungsi utama:
  - load_cbbi_xlsx()  : Parse file XLSX resmi CBBI → DataFrame bersih
  - fetch_btc_open()  : Ambil btc_open harian dari yfinance

Semua nilai indikator CBBI dikonversi dari string persen ("31.95%") ke
float64 (31.95), tetap dalam skala [0.0 – 100.0] sesuai definisi CBBI resmi.
"""

import os
import logging
from pathlib import Path

import pandas as pd
import yfinance as yf

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT_DIR   = Path(__file__).resolve().parents[2]
RAW_DIR    = ROOT_DIR / "data" / "raw"
XLSX_PATH  = ROOT_DIR / "CBBI_dataset.xlsx"
BTC_CACHE  = RAW_DIR / "btc_open.parquet"

# ── Kolom mapping: nama XLSX → nama internal ──────────────────────────────────
COLUMN_RENAME = {
    "Date":        "date",
    "Price":       "btc_close",
    "Confidence":  "cbbi_confidence",
    "PiCycle":     "pi_cycle",
    "RUPL":        "rupl",
    "RHODL":       "rhodl_ratio",
    "Puell":       "puell_multiple",
    "2YMA":        "two_year_ma_mult",
    "Trolololo":   "trolololo",
    "MVRV":        "mvrv_zscore",
    "ReserveRisk": "reserve_risk",
    "Woobull":     "woobull",
}

# Kolom indikator yang berbentuk string persen ("XX.XX%") → float
INDICATOR_COLS = [
    "cbbi_confidence", "pi_cycle", "rupl", "rhodl_ratio",
    "puell_multiple", "two_year_ma_mult", "trolololo",
    "mvrv_zscore", "reserve_risk", "woobull",
]


def _parse_pct_string(series: pd.Series) -> pd.Series:
    """
    Konversi kolom string persentase ke float64.
    Contoh: '31.95%' → 31.95  |  '0.00%' → 0.0

    Nilai yang tidak dapat di-parse akan menjadi NaN dan dicatat.
    """
    cleaned = series.astype(str).str.replace("%", "", regex=False).str.strip()
    result  = pd.to_numeric(cleaned, errors="coerce")
    n_failed = result.isna().sum()
    if n_failed > 0:
        logger.warning(
            "  [parse_pct] %d nilai gagal di-parse menjadi NaN pada kolom '%s'",
            n_failed, series.name,
        )
    return result


def _parse_price_string(series: pd.Series) -> pd.Series:
    """
    Konversi kolom harga string ke float64.
    Contoh: '$72,713' → 72713.0  |  '$1,234,567' → 1234567.0
    """
    cleaned = (
        series.astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
    )
    result = pd.to_numeric(cleaned, errors="coerce")
    n_failed = result.isna().sum()
    if n_failed > 0:
        logger.warning(
            "  [parse_price] %d nilai harga gagal di-parse menjadi NaN",
            n_failed,
        )
    return result


def load_cbbi_xlsx(filepath: str | Path = XLSX_PATH) -> pd.DataFrame:
    """
    Memuat file XLSX resmi CBBI dan melakukan parsing seluruh kolom.

    Langkah parsing:
    1. Baca file XLSX (sheet: 'Sheet1')
    2. Rename kolom ke nama internal
    3. Parsing kolom Date: string 'MM-DD-YYYY' → datetime64
    4. Parsing kolom btc_close: string '$72,713' → float 72713.0
    5. Parsing kolom indikator: string '31.95%' → float 31.95
    6. Urutkan ascending berdasarkan date (XLSX urutan descending)
    7. Set DatetimeIndex

    Returns
    -------
    pd.DataFrame
        Index : DatetimeIndex (frekuensi harian, ascending)
        Kolom : date (index), btc_close, cbbi_confidence,
                pi_cycle, rupl, rhodl_ratio, puell_multiple,
                two_year_ma_mult, trolololo, mvrv_zscore,
                reserve_risk, woobull
        Semua nilai indikator dalam float64, skala [0.0 – 100.0]
    """
    filepath = Path(filepath)
    logger.info("Memuat CBBI dataset dari: %s", filepath)

    # 1. Baca XLSX
    df = pd.read_excel(filepath, sheet_name="Sheet1", dtype=str)
    logger.info("  Raw shape: %s", df.shape)

    # 2. Rename kolom
    df = df.rename(columns=COLUMN_RENAME)

    # 3. Parse tanggal — XLSX mengandung dua format berbeda:
    #    - "MM-DD-YYYY"            (string, 10 karakter) → format asli CBBI
    #    - "YYYY-MM-DD HH:MM:SS"  (19 karakter, Excel auto-parse datetime ke string)
    #    Strategi: coba format MM-DD-YYYY dulu, fallback ke infersi otomatis
    date_col = df["date"].astype(str).str.strip()

    def _flexible_parse(s: str) -> pd.Timestamp:
        """Parse tanggal dengan fallback antara dua format."""
        try:
            if len(s) == 10 and s[2] == "-":
                # Format: MM-DD-YYYY
                return pd.to_datetime(s, format="%m-%d-%Y")
            else:
                # Format: YYYY-MM-DD HH:MM:SS atau varian lain
                return pd.to_datetime(s, infer_datetime_format=True)
        except Exception:
            return pd.NaT

    df["date"] = date_col.apply(_flexible_parse)
    n_bad_dates = df["date"].isna().sum()
    if n_bad_dates > 0:
        logger.warning("  %d baris memiliki tanggal tidak valid — akan di-drop", n_bad_dates)
        df = df.dropna(subset=["date"])
    logger.info("  Tanggal berhasil di-parse: %d baris", len(df))

    # 4. Parse harga BTC
    df["btc_close"] = _parse_price_string(df["btc_close"])

    # 5. Parse semua kolom indikator persen
    for col in INDICATOR_COLS:
        df[col] = _parse_pct_string(df[col])

    # 6. Urutkan ascending (XLSX datang dalam urutan descending/terbaru duluan)
    df = df.sort_values("date").reset_index(drop=True)

    # 7. Set DatetimeIndex
    df = df.set_index("date")
    df.index.name = "date"

    # Validasi rentang nilai indikator
    for col in INDICATOR_COLS:
        col_min = df[col].min()
        col_max = df[col].max()
        if col_min < -0.01 or col_max > 100.01:
            logger.warning(
                "  Kolom '%s' memiliki nilai di luar [0,100]: min=%.4f, max=%.4f",
                col, col_min, col_max,
            )

    logger.info(
        "  CBBI dataset dimuat: %d baris | %s → %s",
        len(df),
        df.index.min().date(),
        df.index.max().date(),
    )
    return df


def fetch_btc_open(
    start: str = "2012-01-01",
    end:   str = "2026-03-31",
    use_cache: bool = True,
) -> pd.DataFrame:
    """
    Mengambil kolom btc_open harian dari yfinance (ticker: BTC-USD).
    Digunakan eksklusif untuk harga eksekusi T+1.

    Cache disimpan ke data/raw/btc_open.parquet untuk menghindari
    re-fetch berulang kali.

    Parameters
    ----------
    start       : Tanggal mulai, format 'YYYY-MM-DD'
    end         : Tanggal selesai, format 'YYYY-MM-DD'
    use_cache   : Jika True dan cache ada, gunakan cache

    Returns
    -------
    pd.DataFrame
        Index : DatetimeIndex (frekuensi harian)
        Kolom : ['btc_open']  — float64, harga USD
    """
    # Cek cache
    if use_cache and BTC_CACHE.exists():
        logger.info("  [yfinance] Menggunakan cache: %s", BTC_CACHE)
        cached = pd.read_parquet(BTC_CACHE)
        # Validasi cakupan cache
        if (
            cached.index.min() <= pd.Timestamp(start)
            and cached.index.max() >= pd.Timestamp(end)
        ):
            logger.info(
                "  Cache valid: %s → %s (%d baris)",
                cached.index.min().date(), cached.index.max().date(), len(cached),
            )
            return cached.loc[start:end]
        else:
            logger.info("  Cache tidak cukup cakupannya — re-fetch dari yfinance")

    logger.info("  [yfinance] Fetching BTC-USD Open: %s → %s", start, end)
    raw = yf.download(
        "BTC-USD",
        start=start,
        end=end,
        interval="1d",
        auto_adjust=True,
        progress=False,
    )

    if raw.empty:
        raise RuntimeError("yfinance mengembalikan data kosong. Periksa koneksi internet.")

    # Ambil hanya kolom Open, rename
    btc_open = raw[["Open"]].copy()
    btc_open.columns = ["btc_open"]
    btc_open.index.name = "date"

    # Simpan cache
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    btc_open.to_parquet(BTC_CACHE)
    logger.info(
        "  btc_open disimpan ke cache: %d baris | %s → %s",
        len(btc_open), btc_open.index.min().date(), btc_open.index.max().date(),
    )

    return btc_open
