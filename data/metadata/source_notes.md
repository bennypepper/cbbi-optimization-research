# Source Notes — Dataset Master CBBI Optimization

**Dibuat:** 2026-04-28 16:40:10

## Sumber Data

### 1. Indikator CBBI (Sumber Utama)
- **File:** `CBBI_dataset.xlsx`
- **Asal:** Laman resmi CBBI — [cbbi.info](https://cbbi.info)
- **Cakupan asli:** 2011-06-27 – 2026-03-15 (5.376 baris)
- **Cakupan digunakan:** 2012-01-01 – 2026-03-15
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

4. **Kolom sinyal default:** `cbbi_confidence` (Composite CBBI Score resmi) 
   digunakan sebagai kolom sinyal default pada mesin optimisasi. Indikator 
   individual juga tersedia untuk eksplorasi di Fase 2.

5. **Trolololo — Dynamic Channel Normalization (April 28, 2026):** Kolom `trolololo`
   tidak lagi diambil dari CBBI_dataset.xlsx. Nilainya dihitung ulang secara
   independen dari data harga BTC-USD (kolom `btc_close`) menggunakan formula
   **Dynamic Channel Normalization** yang dikonfirmasi oleh pembimbing (2026-04-28).
   Formula menggunakan dua channel power-law terpisah dalam ruang natural-log:
     - top_base    = ln(10) × (2.900 × ln(d + 1400) − 19.463)
     - bottom_base = ln(10) × (2.788 × ln(d + 1200) − 19.463)
   di mana d = hari sejak 2012-01-01. Residual pada titik-titik siklus historis
   (HIGH: 2017-12-17, 2021-11-10; LOW: 2015-01-14, 2018-12-15, 2022-11-21)
   di-fit dengan regresi linear untuk menghasilkan channel adaptif. Normalisasi:
   index = (price_log − channel_bottom) / (channel_top − channel_bottom), clip [0,100].
   Ini menghilangkan Index Revision Bias — risiko bahwa nilai historis berubah
   saat Colin memperbarui algoritma indeks CBBI secara retroaktif.
