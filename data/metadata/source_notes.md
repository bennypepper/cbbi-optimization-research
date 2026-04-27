# Source Notes — Dataset Master CBBI Optimization

**Dibuat:** 2026-04-09 19:40:16  
**Last updated:** 2026-04-27

## Sumber Data

### 1. Indikator CBBI (Sumber Utama)
- **File:** `CBBI_dataset.xlsx`
- **Asal:** Laman resmi CBBI — [cbbi.info](https://cbbi.info)
- **Tanggal pengunduhan:** **Senin, 16 Maret 2026** (Monday, March 16, 2026)
- **Cakupan asli:** 2011-06-27 – 2026-03-15 (5.376 baris)
- **Cakupan digunakan:** 2012-01-01 – 2026-03-15
- **Format asal:** String persentase ("31.95%") dan harga ("$72,713")
- **Parsing:** Persentase → float64 (skala 0–100), Harga → float64 (USD)
- **Normalisasi:** Tidak diperlukan — CBBI.info sudah menyediakan nilai [0–100]
- **⚠️ Catatan revisi (April 2026):** Kolom `trolololo` dalam file ini merupakan versi CBBI dari indikator (tunduk pada Index Revision Bias). Kolom ini sedang digantikan dengan versi yang dihitung secara independen menggunakan data harga BTC dari yfinance dan formula regresi logaritmik standar. Lihat `docs/RESEARCH_UPDATE_PLAN.md` untuk detail.

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
| Confidence | cbbi_confidence | Composite CBBI Score (bukan sinyal utama — hanya konteks) |
| PiCycle | pi_cycle | Pi Cycle Top Indicator |
| RUPL | rupl | Relative Unrealized Profit/Loss |
| RHODL | rhodl_ratio | RHODL Ratio |
| Puell | puell_multiple | Puell Multiple |
| 2YMA | two_year_ma_mult | 2-Year Moving Average Multiplier |
| Trolololo | trolololo | Logarithmic Regression / Rainbow Chart — **kolom sinyal utama** ⚠️ sedang diganti versi independen |
| MVRV | mvrv_zscore | MVRV Z-Score |
| ReserveRisk | reserve_risk | Reserve Risk |
| Woobull | woobull | Woobull NVT |
| *(derived)* | btc_open | Harga pembukaan BTC dari yfinance |
| *(derived)* | fill_flag | True jika baris terkena forward fill |
| *(derived)* | phase | Label fase: in_sample / out_of_sample |

## Statistik Dataset Master

| Metrik | Nilai |
|---|---|
| Total baris | 5,161 |
| Rentang tanggal | 2012-01-01 – 2026-03-15 |
| Fase in_sample (2012–2020) | 3,288 baris |
| Fase out_of_sample (2021–2026) | 1,873 baris |
| Baris dengan forward fill (btc_open) | 990 baris |

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

4. **Kolom sinyal utama:** `trolololo` (Logarithmic Regression / Rainbow Chart) 
   adalah kolom sinyal yang digunakan pada mesin optimisasi dan simulator, 
   berdasarkan hasil analisis signifikansi statistik Fase 2 (composite score tertinggi: 0.6557). 
   Kolom `cbbi_confidence` dipertahankan dalam dataset sebagai konteks referensi saja.

5. **Revisi metodologi (April 2026):** Berdasarkan arahan pembimbing, kolom `trolololo` 
   akan diganti dari versi CBBI-XLSX menjadi versi yang dihitung secara independen 
   menggunakan data yfinance + formula regresi logaritmik dengan fixed bands normalization. 
   Ini menghilangkan ketergantungan pada CBBI API dan memastikan konsistensi nilai 
   yang tidak berubah akibat pembaruan formula oleh Colin. 
   Dataset snapshot CBBI-XLSX (diunduh 16 Maret 2026) tetap digunakan untuk 
   semua indikator LAINNYA sebagai data analisis Fase 2.
