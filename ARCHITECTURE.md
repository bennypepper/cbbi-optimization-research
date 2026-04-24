# Dokumentasi Arsitektur Sistem
## Sistem Optimisasi Strategi Perdagangan Bitcoin Berbasis Indikator CBBI

**Versi:** 2.0  
**Tanggal:** April 2026  
**Author:** Solo Developer  
**Status:** Draft

---

## 1. Ringkasan Proyek

### 1.1 Latar Belakang

Proyek ini merupakan implementasi teknis dari penelitian "Optimisasi Parameter Threshold dan Alokasi Aset Berbasis Indikator CBBI untuk Memaksimalkan Kinerja Portofolio Bitcoin." Sistem dibangun dalam empat fase yang mencakup pipeline data, seleksi indikator, mesin optimisasi parametrik dua skenario, dan aplikasi web interaktif berbasis cloud.

### 1.2 Tujuan Sistem

- Menghasilkan dataset bersih dan terstruktur dari harga BTC dan seluruh komponen indikator CBBI (2012–2026).
- Mengidentifikasi indikator CBBI yang paling signifikan secara statistik sebagai basis sinyal perdagangan.
- Menjalankan dua skenario optimisasi yang saling melengkapi: Skenario 1 (validasi akademis dengan split IS/OOS) dan Skenario 2 (eksplorasi potensi maksimal dengan full dataset).
- Menyediakan aplikasi web publik dengan dua fungsi utama: simulator backtesting bebas untuk pengguna, dan halaman hasil penelitian yang menampilkan kedua skenario secara berdampingan.

### 1.3 Rumusan Masalah Penelitian

Sistem ini dibangun untuk menjawab empat pertanyaan penelitian berikut:

1. Indikator CBBI mana yang memiliki tingkat signifikansi statistik tertinggi sebagai dasar pembuatan sinyal eksekusi perdagangan?
2. Berapa nilai batas picu beli dan jual beserta persentase alokasi aset yang paling optimal untuk menghasilkan metrik Total Return tertinggi?
3. Bagaimana konfigurasi parameter yang diperlukan untuk menghasilkan risiko terendah berdasarkan metrik Maximum Drawdown, serta tingkat pengembalian yang disesuaikan dengan risiko berdasarkan metrik Sharpe Ratio?
4. Seberapa besar selisih degradasi kinerja yang terjadi antara fase In-Sample dan Out-of-Sample pada Skenario 1, dan sejauh mana perbedaannya terhadap potensi kinerja historis maksimal yang ditemukan pada Skenario 2?

### 1.4 Batasan Umum Parameter Optimisasi

| Parameter | Rentang | Interval |
| :--- | :--- | :--- |
| Threshold Buy | 1 – 45 | 1 |
| Threshold Sell | 55 – 100 | 1 |
| Alokasi Buy (% kas) | 1% – 25% | 1% |
| Alokasi Sell (% BTC) | 1% – 25% | 1% |
| Skenario 1 — In-Sample | 2012 – 2020 | — |
| Skenario 1 — Out-of-Sample | 2021 – Mar 2026 | — |
| Skenario 2 — Full Dataset | 2012 – Mar 2026 | — |

### 1.5 Definisi Dua Skenario Penelitian

| Dimensi | Skenario 1 | Skenario 2 |
| :--- | :--- | :--- |
| Nama | Pendekatan Validasi Akademis | Pendekatan Eksplorasi Maksimal |
| Data optimisasi | In-Sample: 2012–2020 | Full dataset: 2012–2026 |
| Validasi | Forward Test pada OOS: 2021–2026 | Tidak ada forward test |
| Lookahead bias | Tidak ada — terisolasi ketat | Ada secara sadar — wajib didisklosur |
| Tujuan utama | Membuktikan robustness strategi | Memetakan batas potensi historis absolut |
| Peran dalam laporan | Tolok ukur validitas ilmiah | Referensi eksplorasi komparatif |

### 1.6 Landasan Teoritis & Target Kajian Pustaka

Penelitian ini berlandaskan pada sejumlah kerangka konseptual dan referensi empiris yang relevan. Target kajian pustaka pada fase awal penelitian adalah merangkum minimal **5 hingga 7 referensi akademis** yang mencakup topik-topik berikut sebagai fondasi argumentasi metodologis:

1. **Metrik on-chain Bitcoin sebagai indikator siklus pasar** — mencakup MVRV Z-Score, NUPL (Net Unrealized Profit/Loss), Puell Multiple, dan Reserve Risk.
2. **Optimisasi parameter pada sistem perdagangan algoritmik** — menggunakan metode Grid Search, Bayesian Optimization, dan Genetic Algorithm.
3. **Backtesting kuantitatif pada pasar aset kripto** — khususnya terkait penghindaran lookahead bias dan validasi berbasis walk-forward testing.
4. **Metodologi pemisahan data In-Sample dan Out-of-Sample** dalam konteks pengembangan strategi perdagangan yang robust.
5. **Karakteristik siklus makro aset kripto** dan implikasinya terhadap frekuensi sinyal perdagangan berbasis indikator on-chain.

> **Target Literatur:** Kajian komprehensif terhadap literatur-literatur ini membentuk landasan metodologis sebelum eksekusi pengumpulan data.

### 1.7 Arsitektur Empat Komponen Utama

```
KOMPONEN 1: Data Pipeline & Preprocessing
        |
KOMPONEN 2: Seleksi Indikator & Analisis Statistik
        |
KOMPONEN 3: Mesin Optimisasi Dua Skenario & Validasi
        |
KOMPONEN 4: Aplikasi Web Interaktif (Deploy Online)
```

---

## 2. KOMPONEN 1 — Data Pipeline & Preprocessing

### 2.1 Tujuan Komponen

Menghasilkan satu dataset master yang bersih, lengkap, dan siap digunakan oleh seluruh modul downstream. Dataset master dibentuk dari dua sumber yang saling melengkapi: (1) file XLSX resmi CBBI yang sudah mengandung seluruh indikator dan Confidence Score, dan (2) data harga BTC harian dari `yfinance` yang diperlukan untuk kolom `btc_open` sebagai harga eksekusi T+1. Dataset akhir harus bebas dari lookahead bias pada level preprocessing dan memiliki indeks waktu yang konsisten.

### 2.2 Sumber Data

#### 2.2.1 Dataset CBBI Resmi (Sumber Utama — Sudah Tersedia)

Seluruh indikator CBBI dan Confidence Score telah tersedia secara lengkap dalam file lokal yang diunduh langsung dari laman resmi CBBI ([cbbi.info](https://cbbi.info)). Tidak ada API fetching, kalkulasi manual, atau scraping indikator yang diperlukan.

| Atribut | Detail |
| :--- | :--- |
| File sumber | `data/raw/CBBI_dataset.xlsx` (file lokal, sudah tersedia) |
| Asal data | Laman resmi CBBI — [cbbi.info](https://cbbi.info) |
| Cakupan | 2011-06-27 – 2026-03-15 (5.376 baris harian) |
| Format nilai | String persentase (e.g. `"31.95%"`) — perlu parsing ke float |

**Kolom yang tersedia dalam file XLSX:**

| Kolom XLSX | Nama Internal | Deskripsi |
| :--- | :--- | :--- |
| `Date` | `date` | Tanggal (string, format `MM-DD-YYYY`) |
| `Price` | `btc_close` | Harga penutupan BTC (string, e.g. `"$72,713"`) |
| `Confidence` | `cbbi_confidence` | Composite CBBI Confidence Score [0–100] |
| `PiCycle` | `pi_cycle` | Pi Cycle Top Indicator [0–100] |
| `RUPL` | `rupl` | Relative Unrealized Profit/Loss [0–100] |
| `RHODL` | `rhodl_ratio` | RHODL Ratio [0–100] |
| `Puell` | `puell_multiple` | Puell Multiple [0–100] |
| `2YMA` | `two_year_ma_mult` | 2-Year Moving Average Multiplier [0–100] |
| `Trolololo` | `trolololo` | Logarithmic Regression (Rainbow Chart) [0–100] |
| `MVRV` | `mvrv_zscore` | MVRV Z-Score [0–100] |
| `ReserveRisk` | `reserve_risk` | Reserve Risk [0–100] |
| `Woobull` | `woobull` | Woobull NVT [0–100] |

> **Catatan:** Semua nilai indikator sudah dinormalisasi ke skala [0–100] oleh sistem CBBI resmi. Tidak ada normalisasi ulang yang diperlukan. Kolom `Price` digunakan sebagai `btc_close` (harga sinyal hari T), namun `btc_open` (harga eksekusi T+1) tetap harus diambil dari `yfinance` karena tidak tersedia di file XLSX.

#### 2.2.2 Harga BTC Harian (Sumber Tambahan — Untuk `btc_open` Saja)

`btc_open` diperlukan secara eksklusif untuk implementasi aturan eksekusi T+1 (sinyal dari `close[T]`, eksekusi di `open[T+1]`). Kolom ini tidak tersedia di file XLSX CBBI dan harus diambil secara terpisah.

| Atribut | Detail |
| :--- | :--- |
| Sumber | `yfinance` — ticker `BTC-USD` |
| Field yang diambil | `date`, `open` |
| Frekuensi | Daily (1D) |
| Cakupan | 2012-01-01 – 2026-03-31 |

### 2.3 Spesifikasi Modul

#### Modul `src/data/loader.py`

```python
def load_cbbi_xlsx(filepath: str = "data/raw/CBBI_dataset.xlsx") -> pd.DataFrame:
    """
    Memuat file XLSX resmi CBBI dan melakukan parsing seluruh kolom.

    Langkah parsing:
    1. Baca file XLSX (sheet: 'Sheet1')
    2. Parsing kolom Date: string 'MM-DD-YYYY' → datetime64
    3. Parsing kolom Price: string '$72,713' → float (hilangkan '$' dan ',')
    4. Parsing seluruh kolom indikator: string '31.95%' → float 31.95
       (hilangkan '%', konversi ke float)
    5. Urutkan ascending berdasarkan date (data XLSX urutan descending)
    6. Set DatetimeIndex

    Returns:
        DataFrame dengan kolom:
        ['date', 'btc_close', 'cbbi_confidence',
         'pi_cycle', 'rupl', 'rhodl_ratio', 'puell_multiple',
         'two_year_ma_mult', 'trolololo', 'mvrv_zscore',
         'reserve_risk', 'woobull']
        Seluruh nilai indikator dalam tipe float64, skala [0.0 – 100.0]
    """

def fetch_btc_open(start: str, end: str) -> pd.DataFrame:
    """
    Mengambil kolom btc_open harian dari yfinance (ticker: BTC-USD).
    Digunakan eksklusif untuk harga eksekusi T+1.

    Args:
        start: '2012-01-01'
        end:   '2026-03-31'
    Returns:
        DataFrame dengan kolom: ['date', 'btc_open']
        Index: DatetimeIndex, frekuensi 'D'
    """
```

#### Modul `src/data/preprocessor.py`

```python
def merge_datasets(cbbi_df: pd.DataFrame,
                   btc_open_df: pd.DataFrame) -> pd.DataFrame:
    """
    Menggabungkan dataset CBBI (dari load_cbbi_xlsx) dengan btc_open
    (dari fetch_btc_open) berdasarkan DatetimeIndex.

    Langkah:
    1. Left join: cbbi_df sebagai base, btc_open_df sebagai tambahan
    2. Filter ke rentang 2012-01-01 – 2026-03-31
       (data CBBI dimulai 2011, tapi digunakan mulai 2012)
    3. Verifikasi tidak ada gap pada kolom btc_close dan btc_open

    Returns:
        DataFrame gabungan dengan semua kolom indikator + btc_open
    """

def apply_forward_fill(df: pd.DataFrame,
                        max_consecutive_fill: int = 7) -> pd.DataFrame:
    """
    Mengisi missing values dengan forward fill untuk kolom btc_open
    dan kolom indikator yang memiliki gap pada hari tertentu.
    Batas maksimum pengisian berturutan = max_consecutive_fill hari.
    Hari yang melebihi batas ditandai NaN dan dicatat dalam fill_log.csv.

    CRITICAL: Forward fill hanya menggunakan nilai masa lalu (T-1 ke belakang).
    Tidak ada backward fill yang diperbolehkan untuk mencegah lookahead bias.

    Catatan: Indikator CBBI dari file XLSX sudah dalam kondisi bersih.
    Forward fill terutama berlaku untuk kolom btc_open pada hari libur
    atau hari di mana data harga tidak tersedia.
    """

def validate_no_lookahead(df: pd.DataFrame) -> bool:
    """
    Validasi deterministik: memastikan tidak ada nilai future digunakan
    pada hari T untuk keputusan di hari T atau sebelumnya.
    Raises ValueError jika lookahead bias terdeteksi.
    """

def tag_phases(df: pd.DataFrame) -> pd.DataFrame:
    """
    Menambahkan kolom 'phase' ke dataset master:
    - 'in_sample'      : 2012-01-01 – 2020-12-31
    - 'out_of_sample'  : 2021-01-01 – 2026-03-31
    Kolom ini digunakan sebagai filter oleh modul optimisasi.
    Untuk Skenario 2, seluruh data digunakan tanpa memandang tag fase.
    """

def build_master_dataset(
    cbbi_xlsx_path: str = "data/raw/CBBI_dataset.xlsx",
    start_date: str = "2012-01-01",
    end_date: str = "2026-03-31"
) -> pd.DataFrame:
    """
    Fungsi orkestrasi utama Komponen 1.
    Memanggil secara berurutan:
      1. load_cbbi_xlsx()       — muat dan parse file XLSX
      2. fetch_btc_open()       — ambil btc_open dari yfinance
      3. merge_datasets()       — gabungkan kedua sumber
      4. apply_forward_fill()   — tangani gap minimal
      5. validate_no_lookahead() — gate validasi
      6. tag_phases()           — tambahkan label IS/OOS
    Simpan hasil akhir ke 'data/processed/master_dataset.parquet'.
    """
```

### 2.4 Skema Dataset Master

**File:** `data/processed/master_dataset.parquet`

| Kolom | Asal | Tipe | Deskripsi |
| :--- | :--- | :--- | :--- |
| `date` | XLSX | `datetime64[ns]` | Index utama, frekuensi harian |
| `btc_close` | XLSX (`Price`) | `float64` | Harga penutupan BTC (USD) — digunakan untuk nilai sinyal hari T |
| `btc_open` | yfinance | `float64` | Harga pembukaan BTC (USD) — digunakan untuk eksekusi T+1 |
| `cbbi_confidence` | XLSX (`Confidence`) | `float64` | Composite CBBI Confidence Score [0–100] — **kolom sinyal utama** |
| `pi_cycle` | XLSX (`PiCycle`) | `float64` | Pi Cycle Top Indicator [0–100] |
| `rupl` | XLSX (`RUPL`) | `float64` | Relative Unrealized Profit/Loss [0–100] |
| `rhodl_ratio` | XLSX (`RHODL`) | `float64` | RHODL Ratio [0–100] |
| `puell_multiple` | XLSX (`Puell`) | `float64` | Puell Multiple [0–100] |
| `two_year_ma_mult` | XLSX (`2YMA`) | `float64` | 2-Year Moving Average Multiplier [0–100] |
| `trolololo` | XLSX (`Trolololo`) | `float64` | Logarithmic Regression / Rainbow Chart [0–100] |
| `mvrv_zscore` | XLSX (`MVRV`) | `float64` | MVRV Z-Score [0–100] |
| `reserve_risk` | XLSX (`ReserveRisk`) | `float64` | Reserve Risk [0–100] |
| `woobull` | XLSX (`Woobull`) | `float64` | Woobull NVT [0–100] |
| `fill_flag` | Derived | `bool` | True jika baris mengandung nilai hasil forward fill |
| `phase` | Derived | `str` | `"in_sample"` atau `"out_of_sample"` |

> **Catatan penting — Dua kolom harga BTC:**
> - `btc_close`: diambil dari kolom `Price` file XLSX, digunakan sebagai referensi harga dan verifikasi sinyal hari T.
> - `btc_open`: diambil dari `yfinance`, digunakan **eksklusif** sebagai harga eksekusi hari T+1 untuk mencegah lookahead bias.
> - Normalisasi tidak diperlukan karena seluruh indikator sudah dalam skala [0–100] yang disediakan oleh sistem CBBI resmi.
> - Kolom `cbbi_confidence` merupakan Composite CBBI Score resmi dan menjadi **kolom sinyal default** pada mesin optimisasi (Fase 3).

### 2.5 Struktur Direktori Komponen 1

```
cbbi-optimization/
├── data/
│   ├── raw/
│   │   ├── CBBI_dataset.xlsx    # File sumber utama — dari cbbi.info (sudah tersedia)
│   │   └── btc_open.parquet     # btc_open harian dari yfinance (di-fetch satu kali)
│   ├── processed/
│   │   └── master_dataset.parquet
│   └── metadata/
│       ├── source_notes.md      # Dokumentasi asal data dan periode cakupan
│       └── fill_log.csv         # Log baris yang terkena forward fill
└── src/
    └── data/
        ├── loader.py            # load_cbbi_xlsx() + fetch_btc_open()
        └── preprocessor.py     # merge, fill, validate, tag_phases, build_master_dataset()
```

### 2.6 Indikator Output Komponen 1

- File `CBBI_dataset.xlsx` berhasil di-parse: seluruh 12 kolom terbaca, nilai string persentase terkonversi ke float64, DatetimeIndex terurut ascending.
- Dataset master mencakup rentang 2012-01-01 hingga 2026-03-31 tanpa gap pada kolom `btc_close` dan `btc_open`.
- Kolom `btc_open` terisi dari yfinance dan berhasil di-join ke dataset CBBI berdasarkan tanggal.
- Tidak ada backward fill; forward fill (jika ada) tidak melampaui 7 hari berturutan.
- `validate_no_lookahead()` mengembalikan `True` tanpa exception.
- Kolom `phase` terisi dengan benar: `in_sample` untuk 2012–2020, `out_of_sample` untuk 2021–2026.
- File `source_notes.md` mendeskripsikan asal data, metode parsing, dan filter periode yang diterapkan.

---

## 3. KOMPONEN 2 — Seleksi Indikator & Analisis Statistik

### 3.1 Tujuan Komponen

Mengidentifikasi secara kuantitatif indikator CBBI mana yang memiliki korelasi statistik paling kuat dengan pergerakan harga Bitcoin pada berbagai lag waktu. Output fase ini menentukan indikator yang dijadikan basis sinyal pada Fase 3. Seluruh analisis dijalankan hanya pada data In-Sample untuk menghindari data leakage.

### 3.2 Spesifikasi Analisis

#### 3.2.1 Analisis Korelasi Spearman

Korelasi Spearman dipilih karena bersifat non-parametrik dan lebih robust terhadap distribusi non-normal yang umum pada data aset kripto.

```python
LAG_WINDOWS = [7, 14, 30, 60, 90]  # hari ke depan

def compute_forward_returns(price_series: pd.Series, lag: int) -> pd.Series:
    """
    Menghitung forward return: (P[t+lag] - P[t]) / P[t]

    CRITICAL: Hanya digunakan untuk analisis statistik (Komponen 2).
    TIDAK boleh digunakan dalam logika backtesting (Komponen 3).
    Penggunaan forward return di Komponen 3 merupakan bentuk lookahead bias.
    """
    return price_series.pct_change(lag).shift(-lag)

def spearman_correlation_analysis(df: pd.DataFrame,
                                   phase_filter: str = "in_sample") -> pd.DataFrame:
    """
    Untuk setiap indikator x setiap lag:
      1. Filter data hanya pada fase yang ditentukan
      2. Hitung forward return pada lag tersebut
      3. Hitung korelasi Spearman dengan nilai indikator
      4. Catat koefisien korelasi (rho) dan p-value

    Returns:
        DataFrame dengan kolom:
        ['indicator', 'lag_days', 'spearman_rho', 'p_value', 'significant']
        Kolom 'significant': True jika p_value < 0.05
    """
```

#### 3.2.2 Analisis Distribusi per Kondisi Pasar

```python
MARKET_CONDITIONS = {
    "accumulation": (0, 25),    # CBBI confidence 0–25
    "neutral":      (25, 60),   # CBBI confidence 25–60
    "distribution": (60, 80),   # CBBI confidence 60–80
    "euphoria":     (80, 100),  # CBBI confidence 80–100
}

def distribution_analysis(df: pd.DataFrame,
                            phase_filter: str = "in_sample") -> dict:
    """
    Untuk setiap indikator x setiap kondisi pasar:
      - Hitung mean, median, std, IQR nilai indikator
      - Lakukan Kruskal-Wallis test untuk perbedaan antar kondisi

    Returns:
        dict: {indicator_name: {condition: stats_dict}}
    """
```

#### 3.2.3 Pemeringkatan dan Seleksi Indikator

```python
def rank_indicators(correlation_df: pd.DataFrame,
                     distribution_results: dict) -> pd.DataFrame:
    """
    Composite score per indikator:
      score = 0.6 * abs(max_spearman_rho) + 0.4 * (1 - min_p_value_normalized)

    Returns:
        DataFrame terurut descending dengan kolom:
        ['indicator', 'composite_score', 'best_lag_days',
         'best_spearman_rho', 'best_p_value', 'selected']

    Kriteria seleksi: composite_score >= 0.4 DAN p_value < 0.05
    pada minimal satu lag window. Minimum 3 indikator harus terpilih.
    """
```

### 3.3 Output Komponen 2

| File | Format | Isi |
| :--- | :--- | :--- |
| `analysis/spearman_results.csv` | CSV | Korelasi semua indikator x semua lag |
| `analysis/distribution_stats.json` | JSON | Statistik distribusi per kondisi pasar |
| `analysis/indicator_ranking.csv` | CSV | Pemeringkatan final + flag `selected` |
| `analysis/selected_indicators.json` | JSON | List indikator terpilih untuk Komponen 3 |
| `reports/feature_selection_report.md` | Markdown | Narasi hasil analisis + referensi visualisasi |

**Visualisasi yang dihasilkan:**
- Heatmap korelasi Spearman (indikator x lag window)
- Box plot distribusi nilai per indikator per kondisi pasar
- Bar chart composite score pemeringkatan indikator
- Scatter plot indikator terpilih vs forward return 30/60/90 hari

### 3.4 Indikator Output Komponen 2

- Seluruh 9 indikator individual + `cbbi_confidence` (Composite Score resmi) telah dianalisis pada 5 lag window menggunakan data In-Sample.
- Minimal 3 indikator memenuhi ambang seleksi (composite score ≥ 0.4, p-value < 0.05).
- File `selected_indicators.json` tersimpan dan dapat dikonsumsi langsung oleh Fase 3.
- Laporan analisis menjelaskan secara naratif mengapa indikator tertentu lebih signifikan dari yang lain.

---

## 4. KOMPONEN 3 — Mesin Optimisasi Dua Skenario & Validasi

### 4.1 Tujuan Komponen

Menemukan kombinasi parameter optimal melalui Grid Search sebagai metode primer (dengan Bayesian Optimization sebagai fallback), dijalankan secara paralel untuk dua skenario penelitian yang berbeda. Hasil optimal kemudian divalidasi, dikomparasikan, dan diverifikasi secara manual.

### 4.2 Logika Eksekusi Strategi (Shared oleh Kedua Skenario)

```python
def run_backtest(
    df: pd.DataFrame,
    threshold_buy: int,
    threshold_sell: int,
    allocation_buy_pct: float,    # 0.01 – 0.25
    allocation_sell_pct: float,   # 0.01 – 0.25
    initial_cash: float = 100_000.0,
    signal_column: str = "cbbi_confidence"  # Default: Composite CBBI Score resmi dari XLSX
) -> dict:
    """
    Simulasi perdagangan harian berdasarkan nilai sinyal CBBI.

    ATURAN EKSEKUSI (wajib dipatuhi untuk mencegah lookahead bias):
    - Nilai sinyal hari T diambil dari signal_column[T] (btc_close hari T)
    - Keputusan dibuat berdasarkan signal[T]
    - Eksekusi menggunakan harga btc_open[T+1] (bukan close)
    - Tidak ada eksekusi ganda dalam satu hari

    LOGIKA SINYAL:
    - signal[T] < threshold_buy  -> BUY: gunakan (allocation_buy_pct x cash) untuk beli BTC
    - signal[T] > threshold_sell -> SELL: jual (allocation_sell_pct x btc_held) ke kas
    - threshold_buy <= signal[T] <= threshold_sell -> HOLD

    Returns dict dengan key:
    - 'portfolio_history': pd.DataFrame (date, cash, btc_held, portfolio_value)
    - 'trade_log': pd.DataFrame (date, action, signal_value, exec_price, amount, portfolio_value_after)
    - 'metrics': dict (total_return, max_drawdown, sharpe_ratio, win_rate, trade_count)
    """

def calculate_metrics(portfolio_history: pd.DataFrame,
                       trade_log: pd.DataFrame,
                       risk_free_rate: float = 0.04) -> dict:
    """
    Kalkulasi seluruh metrik evaluasi dari hasil backtest.

    - total_return    : (final_value - initial_value) / initial_value
    - max_drawdown    : max((peak - trough) / peak) sepanjang periode
    - sharpe_ratio    : (mean_daily_return - rf_daily) / std_daily_return x sqrt(252)
    - win_rate        : jumlah SELL dengan profit > 0 / total transaksi SELL
    - trade_count     : total jumlah transaksi (BUY + SELL)

    Risk-free rate default: 4% per tahun (annualized US Treasury approximation).
    Jika trade_count < 10, semua metrik tetap dihitung namun ditandai
    dengan flag 'low_sample_warning = True'.

    Catatan Desain: Batas minimum trade_count = 10 ditetapkan berdasarkan
    pertimbangan bahwa metrik statistik (Win Rate, Sharpe Ratio) tidak
    representatif pada sampel transaksi yang sangat kecil. Nilai ini bersifat
    konservatif dan dapat disesuaikan berdasarkan temuan eksplorasi awal data.
    Distribusi frekuensi sinyal per nilai threshold wajib dilaporkan sebagai
    bagian dari analisis deskriptif untuk memberikan konteks yang memadai.
    """
```

### 4.3 Fungsi Objektif Optimisasi

Tiga fungsi objektif dijalankan secara independen untuk setiap skenario:

| Kode Objektif | Fungsi Objektif | Arah |
| :--- | :--- | :--- |
| `max_return` | Maksimalkan `total_return` | Maximize |
| `min_drawdown` | Minimalisasi `max_drawdown` | Minimize |
| `max_sharpe` | Maksimalkan `sharpe_ratio` | Maximize |

Total kombinasi eksekusi: 2 skenario x 3 objektif = **6 run optimisasi** untuk Grid Search, ditambah 6 run untuk algoritma heuristik jika Grid Search tidak selesai tepat waktu.

### 4.4 Skenario 1 — Pendekatan Validasi Akademis

```python
def run_scenario_1(
    df: pd.DataFrame,
    objective: str,           # "max_return" | "min_drawdown" | "max_sharpe"
    algorithm: str = "grid_search",
    min_trade_count: int = 10,
    n_jobs: int = -1
) -> dict:
    """
    Skenario 1: Optimisasi eksklusif pada data In-Sample (2012–2020),
    diikuti Forward Test pada data Out-of-Sample (2021–2026).

    Langkah eksekusi:
    1. Filter df: gunakan hanya baris dengan phase == 'in_sample'
    2. Jalankan algoritma optimisasi pada df_in_sample
    3. Ambil parameter optimal berdasarkan objective
    4. Filter df: gunakan hanya baris dengan phase == 'out_of_sample'
    5. Jalankan run_backtest dengan parameter optimal pada df_out_of_sample
    6. Hitung degradasi kinerja IS vs OOS per metrik

    CRITICAL: df_out_of_sample tidak boleh diakses pada langkah 1-3.
    Isolasi data OOS dijaga secara programatik melalui filter phase.

    Returns:
        {
          'in_sample_optimal': {params, metrics},
          'out_of_sample_result': {params, metrics},
          'degradation': {per_metric: pct_change},
          'trial_log': pd.DataFrame
        }
    """
```

**Interpretasi degradasi kinerja:**

| Tingkat Degradasi | Kategori | Implikasi |
| :--- | :--- | :--- |
| < 20% | Robust | Strategi menggeneralisasi dengan baik |
| 20% – 40% | Moderat | Perlu analisis lanjutan per kondisi pasar |
| > 40% | Indikasi overfitting | Temuan penting — wajib dibahas dalam laporan |

> **Catatan:** Frekuensi sinyal yang sangat rendah pada periode OOS bukan merupakan kegagalan sistem, melainkan cerminan karakteristik CBBI sebagai indikator makro siklus. Kondisi ini wajib dilaporkan secara eksplisit sebagai temuan substantif.

### 4.5 Skenario 2 — Pendekatan Eksplorasi Maksimal

```python
def run_scenario_2(
    df: pd.DataFrame,
    objective: str,
    algorithm: str = "grid_search",
    min_trade_count: int = 10,
    n_jobs: int = -1
) -> dict:
    """
    Skenario 2: Optimisasi menggunakan seluruh dataset (2012–2026)
    sebagai satu kesatuan tanpa pemisahan IS/OOS.

    DISCLOSURE WAJIB: Skenario ini secara sadar menggunakan lookahead bias
    dalam proses optimisasi — seluruh data historis digunakan sekaligus.
    Konsekuensinya, hasil optimal yang ditemukan merepresentasikan
    konfigurasi terbaik secara retrospektif, bukan prediksi yang valid.
    Tujuannya adalah memetakan batas potensi absolut indikator CBBI,
    bukan menghasilkan sistem perdagangan yang dapat digunakan secara
    forward-looking.

    Langkah eksekusi:
    1. Gunakan seluruh df tanpa filter phase
    2. Jalankan algoritma optimisasi pada full dataset
    3. Catat parameter optimal dan seluruh metrik

    Returns:
        {
          'full_dataset_optimal': {params, metrics},
          'trial_log': pd.DataFrame
        }
    """
```

### 4.6 Algoritma Pencarian

#### 4.6.1 Grid Search (Metode Primer)

```python
def run_grid_search(
    df: pd.DataFrame,
    objective: str,
    min_trade_count: int = 10,
    n_jobs: int = -1
) -> pd.DataFrame:
    """
    Iterasi exhaustive seluruh kombinasi parameter:
    - threshold_buy   : range(1, 46)    -> 45 nilai
    - threshold_sell  : range(55, 101)  -> 46 nilai
    - allocation_buy  : range(1, 26)    -> 25 nilai
    - allocation_sell : range(1, 26)    -> 25 nilai
    Total kombinasi: 45 x 46 x 25 x 25 = 1,293,750 percobaan

    Paralelisasi menggunakan joblib.Parallel.
    Progress dilaporkan via tqdm setiap 10,000 percobaan.
    Hasil disimpan secara incremental setiap 50,000 percobaan
    untuk mencegah kehilangan data jika proses terhenti.

    Percobaan dengan trade_count < min_trade_count dieksklusi dari ranking
    namun tetap dicatat dengan flag excluded_low_trades = True.
    """
```

> **Estimasi Durasi Grid Search:**
> Asumsi ~500 backtest/detik (single core) dengan paralelisasi 8 core (~4,000/detik):
> 1,293,750 trial / 4,000 = **sekitar 5–6 menit per run**.
> Dengan 6 run total (2 skenario x 3 objektif): estimasi **30–40 menit** total.
> Jika satu run melebihi 120 menit pada hardware yang digunakan, aktifkan fallback Bayesian Optimization untuk run tersebut.

#### 4.6.2 Bayesian Optimization via Optuna (Fallback)

```python
def run_bayesian_optimization(
    df: pd.DataFrame,
    objective: str,
    n_trials: int = 2000,
    timeout_seconds: int = 1800,
    min_trade_count: int = 10
) -> pd.DataFrame:
    """
    Menggunakan Optuna dengan sampler TPE (Tree-structured Parzen Estimator).
    Search space identik dengan Grid Search (integer ranges).
    Pruning: MedianPruner.

    Output format identik dengan Grid Search untuk interoperabilitas penuh.
    """
```

#### 4.6.3 Genetic Algorithm (Alternatif Heuristik)

```python
def run_genetic_algorithm(
    df: pd.DataFrame,
    objective: str,
    population_size: int = 100,
    n_generations: int = 200,
    mutation_rate: float = 0.1,
    crossover_rate: float = 0.7,
    min_trade_count: int = 10
) -> pd.DataFrame:
    """
    Algoritma heuristik berbasis evolusi untuk pencarian parameter optimal.
    Digunakan sebagai alternatif ketiga apabila:
    - Grid Search melampaui batas waktu yang dapat diterima, DAN
    - Bayesian Optimization belum menghasilkan konvergensi yang memuaskan.

    Representasi kromosom: [threshold_buy, threshold_sell,
                             allocation_buy_pct, allocation_sell_pct]
    Search space identik dengan Grid Search (integer ranges).

    Operator seleksi : Tournament selection
    Operator crossover: Single-point crossover
    Operator mutasi  : Gaussian mutation dengan batas nilai yang dijaga

    Output format identik dengan Grid Search untuk interoperabilitas penuh.
    Percobaan dengan trade_count < min_trade_count dieksklusi dari ranking
    namun tetap dicatat dengan flag excluded_low_trades = True.
    """
```

> **Prioritas Algoritma Pencarian:**
> 1. **Grid Search** — metode primer, exhaustive, deterministik.
> 2. **Bayesian Optimization (Optuna)** — fallback jika satu run Grid Search melebihi 120 menit.
> 3. **Genetic Algorithm** — alternatif heuristik apabila Bayesian Optimization belum konvergen atau ruang pencarian terlalu besar untuk kedua metode di atas.

### 4.7 Skema Pencatatan Hasil

#### 4.7.1 Trial Log (Log Lengkap)

**File:** `results/trial_log/{scenario}_{algorithm}_{objective}.parquet`

| Kolom | Tipe | Deskripsi |
| :--- | :--- | :--- |
| `trial_id` | `int64` | ID unik percobaan |
| `scenario` | `str` | `"scenario_1"` atau `"scenario_2"` |
| `algorithm` | `str` | `"grid_search"` atau `"bayesian"` |
| `objective` | `str` | `"max_return"`, `"min_drawdown"`, `"max_sharpe"` |
| `phase` | `str` | `"in_sample"`, `"out_of_sample"`, atau `"full_dataset"` |
| `threshold_buy` | `int16` | Nilai threshold beli |
| `threshold_sell` | `int16` | Nilai threshold jual |
| `allocation_buy_pct` | `float32` | Persentase alokasi beli |
| `allocation_sell_pct` | `float32` | Persentase alokasi jual |
| `total_return` | `float32` | Total return (desimal) |
| `max_drawdown` | `float32` | Maximum drawdown (desimal) |
| `sharpe_ratio` | `float32` | Sharpe ratio |
| `win_rate` | `float32` | Win rate (desimal) |
| `trade_count` | `int32` | Total jumlah transaksi |
| `low_sample_warning` | `bool` | True jika trade_count < 10 |
| `excluded_low_trades` | `bool` | True jika dieksklusi dari ranking |
| `timestamp` | `datetime64` | Waktu percobaan dieksekusi |

#### 4.7.2 Summary Hasil Optimal

**File:** `results/optimal_params_summary.json`

```json
{
  "metadata": {
    "generated_at": "2026-XX-XX",
    "total_trials_per_run": 1293750
  },
  "scenario_1": {
    "algorithm_used": "grid_search",
    "in_sample": {
      "max_return":    {"threshold_buy": 0, "threshold_sell": 0, "allocation_buy_pct": 0.0,
                        "allocation_sell_pct": 0.0, "total_return": 0.0,
                        "max_drawdown": 0.0, "sharpe_ratio": 0.0,
                        "win_rate": 0.0, "trade_count": 0},
      "min_drawdown":  {"...": "..."},
      "max_sharpe":    {"...": "..."}
    },
    "out_of_sample": {
      "max_return":    {"...": "..."},
      "min_drawdown":  {"...": "..."},
      "max_sharpe":    {"...": "..."}
    },
    "degradation": {
      "max_return": {
        "return_degradation_pct":   0.0,
        "drawdown_degradation_pct": 0.0,
        "sharpe_degradation_pct":   0.0,
        "trade_count_oos":          0,
        "low_sample_warning":       false
      }
    }
  },
  "scenario_2": {
    "algorithm_used": "grid_search",
    "disclosure": "Hasil ini menggunakan seluruh data historis dalam proses optimisasi. Konfigurasi ini tidak dapat digunakan sebagai sinyal prediktif. Tujuannya adalah memetakan batas potensi maksimal indikator CBBI secara historis.",
    "full_dataset": {
      "max_return":    {"...": "..."},
      "min_drawdown":  {"...": "..."},
      "max_sharpe":    {"...": "..."}
    }
  },
  "buy_and_hold_benchmark": {
    "in_sample":    {"total_return": 0.0, "max_drawdown": 0.0, "sharpe_ratio": 0.0},
    "out_of_sample":{"total_return": 0.0, "max_drawdown": 0.0, "sharpe_ratio": 0.0},
    "full_dataset": {"total_return": 0.0, "max_drawdown": 0.0, "sharpe_ratio": 0.0}
  }
}
```

### 4.8 Verifikasi Backtesting Manual

Verifikasi dilakukan pada minimal 20 titik transaksi representatif yang mencakup kondisi pasar bull, bear, dan sideways, dipilih dari hasil kedua skenario.

```python
def manual_verification_report(
    params: dict,
    df: pd.DataFrame,
    sample_dates: list[str]
) -> pd.DataFrame:
    """
    Untuk setiap tanggal dalam sample_dates:
      1. Ambil nilai sinyal hari T: cbbi_composite[T]
      2. Tentukan aksi berdasarkan threshold
      3. Hitung eksekusi: btc_open[T+1] x jumlah unit
      4. Verifikasi saldo kas dan BTC setelah transaksi
      5. Bandingkan dengan nilai yang dihasilkan sistem otomatis

    Kriteria lulus: abs(manual_value - system_value) < 1e-6
    untuk seluruh titik verifikasi.
    """
```

### 4.9 Indikator Output Komponen 3

- Grid Search selesai untuk seluruh 6 kombinasi (2 skenario x 3 objektif) pada data masing-masing.
- Trial log tersimpan lengkap dalam format Parquet; summary optimal tersimpan dalam JSON dengan field `disclosure` pada Skenario 2.
- Analisis degradasi kinerja IS vs OOS Skenario 1 terkuantifikasi per objektif.
- Komparasi Skenario 1 vs Skenario 2 vs Buy and Hold tersedia untuk ketiga periode (IS, OOS, full).
- Verifikasi manual: seluruh 20 titik sampel mengembalikan `match = True`, dengan sampel yang mencakup minimal 5 titik per kondisi pasar (bull, bear, sideways) dari masing-masing skenario.
- File `reports/optimization_report.md` mendokumentasikan seluruh temuan termasuk diskusi frekuensi sinyal OOS.

---

## 5. KOMPONEN 4 — Aplikasi Web Interaktif

### 5.1 Tujuan Komponen

Membangun dan men-deploy aplikasi web publik dengan dua fungsi yang secara konseptual berbeda namun terintegrasi dalam satu platform: (1) simulator backtesting bebas untuk eksplorasi mandiri pengguna, dan (2) halaman hasil penelitian yang menampilkan kedua skenario secara berdampingan dengan framing yang tepat.

### 5.2 Target Pengguna

| Dimensi | Investor Ritel (Non-teknis) | Peneliti / Akademisi |
| :--- | :--- | :--- |
| Fitur utama | Simulator dengan preset profil risiko | Kontrol parameter penuh + ekspor data |
| Terminologi | Bahasa awam (Agresif/Moderat/Konservatif) | Terminologi teknis (Sharpe, MDD, dll.) |
| Kebutuhan khusus | Tooltip penjelasan setiap indikator | Tabel trial log yang dapat difilter |
| Halaman hasil | Ringkasan naratif | Tabel metrik lengkap + analisis degradasi |

### 5.3 Arsitektur Aplikasi

```
+--------------------------------------------------+
|                  Frontend UI                      |
|    (Streamlit / Dash / Framework TBD)             |
+---------------------+----------------------------+
                       | Function Call
+---------------------v----------------------------+
|               Backend Logic                       |
|  backtest_engine.py  |  metrics_calculator.py    |
|  data_loader.py      |  chart_builder.py         |
|  results_loader.py   |  disclaimer_manager.py    |
+---------------------+----------------------------+
                       | Read
+---------------------v----------------------------+
|                 Data Layer                        |
|  master_dataset.parquet  | optimal_params.json   |
|  trial_log/*.parquet     | scalers/              |
+--------------------------------------------------+
```

> **Catatan Framework:** Rekomendasi berdasarkan prioritas: (1) **Streamlit** — paling cepat untuk deploy, native Python, cocok untuk solo developer; (2) **Dash** — lebih fleksibel untuk layout kompleks. Pilihan final ditentukan pada awal Fase 4.

### 5.4 Spesifikasi Halaman dan Komponen

#### 5.4.1 Halaman 1 — Simulator Backtesting Bebas

Simulator ini bersifat **independen dari kedua skenario penelitian**. Pengguna menentukan sendiri seluruh parameter dan rentang tanggal. Tidak ada klaim prediktif — ini adalah alat eksplorasi historis murni.

**Komponen Input:**

```
Panel Kiri (Konfigurasi Parameter):
+-- [Preset Profil Risiko]       Dropdown: Konservatif / Moderat / Agresif / Custom
+-- [Threshold Beli]             Slider: 1 - 45 (default: 20)
+-- [Threshold Jual]             Slider: 55 - 100 (default: 75)
+-- [Alokasi per Pembelian]      Slider: 1% - 25% (default: 10%)
+-- [Alokasi per Penjualan]      Slider: 1% - 25% (default: 10%)
+-- [Periode Simulasi]           Date range slider: 2012-01-01 s/d 2026-03-31
|                                (Pengguna bebas menentukan rentang tanggal)
+-- [Modal Awal (USD)]           Number input (default: 100,000)
+-- [Tombol "Jalankan Simulasi"] Primary CTA

Preset profil risiko:
  Konservatif : buy=10, sell=85, alloc_buy=5%,  alloc_sell=5%
  Moderat     : buy=20, sell=75, alloc_buy=10%, alloc_sell=10%
  Agresif     : buy=30, sell=65, alloc_buy=20%, alloc_sell=20%
```

**Komponen Output:**

```
Panel Kanan (Hasil Simulasi):
+-- [Kartu Metrik Ringkasan]
|   +-- Total Return (%)
|   +-- Maximum Drawdown (%)
|   +-- Sharpe Ratio
|   +-- Win Rate (%) | Trade Count
|   +-- [Badge peringatan jika trade_count < 10]
|
+-- [Grafik Kurva Ekuitas]
|   +-- Area chart: Nilai portofolio strategi
|   +-- Line: Benchmark Buy and Hold
|   +-- Axis sekunder: Harga BTC
|   +-- Markers: Titik BUY (segitiga hijau) dan SELL (segitiga merah)
|
+-- [Grafik CBBI Composite Score]
|   +-- Line: Nilai CBBI harian
|   +-- Garis putus-putus merah: threshold_buy
|   +-- Garis putus-putus hijau: threshold_sell
|
+-- [Tabel Log Transaksi]
    +-- Kolom: Tanggal | Aksi | Nilai CBBI | Harga Eksekusi | Jumlah | Nilai Portofolio
```

#### 5.4.2 Halaman 2 — Hasil Penelitian

Halaman ini menampilkan hasil dari Fase 3 secara read-only. Pengguna tidak dapat mengubah parameter di sini.

```
Konten:
+-- [Banner Penjelasan Dua Skenario]
|   Narasi singkat perbedaan tujuan Skenario 1 (validasi ilmiah)
|   dan Skenario 2 (eksplorasi potensi maksimal)
|
+-- [Panel Skenario 1 — Hasil Validasi Akademis]
|   +-- Tabel: Parameter optimal per objektif (Max Return | Min Drawdown | Max Sharpe)
|       Kolom: Buy | Sell | Alloc Buy | Alloc Sell | IS Return | OOS Return | Degradasi | vs B&H
|   +-- Grafik: Kurva ekuitas IS vs OOS untuk parameter optimal terpilih
|   +-- Grafik: Bar chart degradasi kinerja per metrik per objektif
|
+-- [Panel Skenario 2 — Hasil Eksplorasi Maksimal]
|   +-- [Disclaimer Box — wajib tampil sebelum angka]
|   |   "Hasil berikut diperoleh dari optimisasi yang menggunakan seluruh data historis
|   |    2012–2026. Konfigurasi ini tidak dapat digunakan sebagai sinyal prediktif.
|   |    Tujuannya adalah memetakan batas potensi historis absolut indikator CBBI."
|   +-- Tabel: Parameter optimal per objektif
|       Kolom: Buy | Sell | Alloc Buy | Alloc Sell | Full Return | Full MDD | Sharpe | Trade Count | vs B&H
|   +-- Grafik: Kurva ekuitas full dataset untuk parameter optimal terpilih
|
+-- [Panel Komparasi]
|   +-- Tabel berdampingan: Skenario 1 OOS vs Skenario 2 Full vs Buy and Hold
|   +-- Heatmap sensitivitas: Total Return sebagai fungsi threshold_buy x threshold_sell
|       (terpisah untuk Skenario 1 IS, Skenario 1 OOS, dan Skenario 2 Full)
|
+-- [Panel Ekspor]
    +-- Download: optimal_params_summary.json
    +-- Download: trial_log Skenario 1 (filtered CSV, top-N)
    +-- Download: trial_log Skenario 2 (filtered CSV, top-N)
```

#### 5.4.3 Halaman 3 — Dokumentasi & Disclaimer

```
Konten:
+-- Penjelasan indikator CBBI (per komponen, bahasa awam + teknis)
+-- Panduan interpretasi metrik (Total Return, MDD, Sharpe Ratio, Win Rate)
+-- Penjelasan perbedaan In-Sample, Out-of-Sample, dan Full Dataset
+-- Penjelasan mengapa Skenario 2 tidak prediktif
+-- Disclaimer investasi (hasil historis bukan jaminan kinerja masa depan)
+-- Keterbatasan penelitian (akses data, jumlah siklus, frekuensi sinyal)
+-- Referensi metodologi dan sumber data
```

### 5.5 Spesifikasi API Internal

```python
def load_dataset(start_date: str, end_date: str) -> pd.DataFrame:
    """Load slice dari master_dataset.parquet sesuai rentang tanggal."""

def execute_simulation(params: dict) -> SimulationResult:
    """
    Wrapper utama yang dipanggil frontend setiap kali pengguna
    menekan tombol 'Jalankan Simulasi' pada Halaman 1.

    Args:
        params: {
            threshold_buy, threshold_sell,
            allocation_buy_pct, allocation_sell_pct,
            start_date, end_date, initial_cash
        }
    Returns:
        SimulationResult dataclass dengan:
        - portfolio_history : pd.DataFrame
        - trade_log         : pd.DataFrame
        - metrics           : dict
        - benchmark_metrics : dict
        - low_sample_warning: bool
    """

def get_research_results() -> dict:
    """
    Load dan return optimal_params_summary.json.
    Digunakan oleh Halaman 2 untuk menampilkan hasil penelitian.
    """

def get_trial_log_top_n(scenario: str, objective: str,
                         phase: str, top_n: int = 100) -> pd.DataFrame:
    """
    Return top-N trial dari trial log berdasarkan metrik objektif.
    Digunakan untuk tabel ekspor pada Halaman 2.
    """

def build_equity_chart(simulation_result: SimulationResult,
                        show_phase_shading: bool = False) -> go.Figure:
    """
    Return Plotly Figure kurva ekuitas + benchmark + trade markers.
    show_phase_shading: True pada Halaman 2 untuk memberi shading IS vs OOS.
    """

def build_cbbi_chart(df: pd.DataFrame, params: dict) -> go.Figure:
    """Return Plotly Figure CBBI score + threshold lines."""

def build_sensitivity_heatmap(scenario: str, objective: str,
                               phase: str) -> go.Figure:
    """
    Return Plotly heatmap sensitivitas parameter dari trial log.
    threshold_buy (x-axis) vs threshold_sell (y-axis),
    nilai = metrik objektif pada alokasi optimal.
    """

def build_degradation_chart(scenario_1_results: dict) -> go.Figure:
    """
    Return Plotly bar chart degradasi kinerja IS vs OOS
    untuk ketiga objektif Skenario 1.
    """
```

### 5.6 Spesifikasi Deployment

| Aspek | Spesifikasi |
| :--- | :--- |
| Platform target | Streamlit Community Cloud (primer) / Railway (alternatif) |
| Runtime | Python 3.11+ |
| Memory requirement | Minimum 512 MB RAM; trial log Parquet di-load on-demand, bukan saat startup |
| Dataset storage | File Parquet di-commit ke repository atau GitHub LFS / Hugging Face Datasets |
| Environment variables | `GLASSNODE_API_KEY`, `COINMETRICS_API_KEY` (tidak diekspos ke frontend) |
| CI/CD | Auto-deploy dari branch `main` via GitHub integration |
| Caching | Master dataset di-cache setelah load pertama; trial log di-load on-demand per permintaan ekspor |
| Cold start tolerance | Maksimum 30 detik; progress indicator ditampilkan selama loading |

### 5.7 Kriteria Keberhasilan Fase 4

- Aplikasi dapat diakses melalui URL publik tanpa login.
- Simulasi Halaman 1 dengan parameter apapun selesai dalam kurang dari 5 detik.
- Hasil simulasi identik dengan pipeline Fase 3 untuk parameter yang sama (toleransi: abs delta < 1e-6).
- Halaman 2 menampilkan hasil kedua skenario secara berdampingan; disclaimer Skenario 2 tampil sebelum angka.
- Tiga halaman berfungsi penuh tanpa error pada browser modern (Chrome, Firefox, Safari).
- Ekspor CSV dan JSON menghasilkan file yang dapat dibuka langsung.
- Tampilan responsif pada layar desktop (lebih dari 1280px lebar) dan tablet (lebih dari 768px lebar).

---

## 6. Ringkasan Deliverable Per Fase

| Fase | Deliverable Utama | Kriteria Selesai |
| :---: | :--- | :--- |
| **1** | `master_dataset.parquet`, pipeline preprocessing, `source_limitations.md` | Dataset bersih, tervalidasi, bebas lookahead bias pada level preprocessing |
| **2** | Laporan seleksi indikator, `selected_indicators.json`, visualisasi korelasi | Minimal 3 indikator terpilih dengan kriteria statistik terpenuhi |
| **3** | Trial log 6 run, `optimal_params_summary.json`, laporan validasi OOS, dokumen verifikasi manual | Verifikasi manual 100% match; degradasi OOS terkuantifikasi; disclosure Skenario 2 terdokumentasi |
| **4** | Aplikasi web live di URL publik, dokumentasi teknis | Simulator berfungsi dalam 5 detik; Halaman 2 menampilkan kedua skenario dengan disclaimer yang tepat |

---

## 7. Dependensi dan Stack Teknologi

### 7.1 Data & Processing
- `openpyxl` — Membaca file CBBI_dataset.xlsx
- `yfinance` — Pengambilan data `btc_open` harian untuk eksekusi T+1
- `requests` — (opsional) Konsumsi API tambahan jika diperlukan di masa mendatang
- `pandas`, `numpy` — Manipulasi dan komputasi data
- `pyarrow` / `fastparquet` — Serialisasi Parquet
- `scikit-learn` — Analisis statistik (Fase 2)
- `scipy` — Korelasi Spearman, Kruskal-Wallis test

### 7.2 Optimisasi
- `joblib` — Paralelisasi Grid Search multi-core
- `tqdm` — Progress bar komputasi
- `optuna` — Bayesian Optimization (fallback)
- Implementasi kustom Genetic Algorithm (alternatif heuristik untuk ruang pencarian besar)

### 7.3 Visualisasi
- `plotly` — Chart interaktif (ekuitas, heatmap, CBBI, degradasi)
- `matplotlib`, `seaborn` — Chart statis untuk laporan penelitian

### 7.4 Aplikasi Web
- TBD: Streamlit (primer) atau Dash — ditentukan awal Fase 4
- `plotly` — Visualisasi interaktif dalam web

### 7.5 Environment & Versioning
- **Python:** 3.11+
- **Environment management:** `venv` atau `conda`
- **Versioning:** Git + GitHub — satu repository monorepo
- **Branching strategy:** `main` (production) → `develop` → `feature/*`
- **Dependency management:** `requirements.txt` dengan versi yang di-pin
- **Notebook:** Jupyter Notebook untuk eksplorasi — disimpan di `notebooks/`
- **Secrets management:** `.env` file (tidak di-commit) + environment variables pada platform deploy

### 7.6 Struktur Repositori Final

```
cbbi-optimization/
├── data/
│   ├── raw/
│   ├── processed/
│   └── metadata/
├── src/
│   ├── data/
│   │   ├── loader.py             # load_cbbi_xlsx() + fetch_btc_open()
│   │   └── preprocessor.py      # merge, fill, validate, tag_phases, build_master_dataset()
│   ├── analysis/
│   │   └── feature_selector.py
│   ├── optimization/
│   │   ├── backtest_engine.py    # Logika run_backtest() dan calculate_metrics()
│   │   ├── grid_search.py        # run_grid_search()
│   │   ├── bayesian_optimizer.py # run_bayesian_optimization()
│   │   ├── genetic_algorithm.py  # run_genetic_algorithm() — alternatif heuristik
│   │   ├── scenario_1.py         # run_scenario_1() — IS/OOS split
│   │   ├── scenario_2.py         # run_scenario_2() — full dataset
│   │   └── metrics.py
│   └── web/
│       ├── app.py                # Entry point aplikasi web
│       ├── pages/
│       │   ├── simulator.py      # Halaman 1: Simulator Backtesting Bebas
│       │   ├── results.py        # Halaman 2: Hasil Penelitian (dua skenario)
│       │   └── documentation.py  # Halaman 3: Dokumentasi & Disclaimer
│       └── components/
│           ├── charts.py
│           ├── metrics_cards.py
│           └── disclaimer.py     # Komponen disclaimer Skenario 2
├── results/
│   ├── trial_log/
│   │   ├── scenario_1_grid_search_max_return.parquet
│   │   ├── scenario_1_grid_search_min_drawdown.parquet
│   │   ├── scenario_1_grid_search_max_sharpe.parquet
│   │   ├── scenario_2_grid_search_max_return.parquet
│   │   ├── scenario_2_grid_search_min_drawdown.parquet
│   │   └── scenario_2_grid_search_max_sharpe.parquet
│   ├── optimal_params_summary.json
│   └── reports/
│       ├── feature_selection_report.md
│       ├── optimization_report.md
│       └── manual_verification_report.md
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_feature_selection.ipynb
│   ├── 03_scenario_1_analysis.ipynb
│   ├── 04_scenario_2_analysis.ipynb
│   └── 05_manual_verification.ipynb
├── tests/
│   ├── test_backtest_engine.py   # Unit test lookahead bias & kalkulasi metrik
│   ├── test_scenario_isolation.py # Validasi isolasi data OOS Skenario 1
│   └── test_metrics.py
├── .env.example
├── requirements.txt
└── README.md
```

---

## 8. Kontribusi yang Diharapkan

Penelitian ini merumuskan kerangka kerja optimisasi terstruktur yang menghubungkan analisis metrik on-chain Bitcoin dengan praktik perdagangan kuantitatif berbasis data. Secara spesifik, penelitian ini berkontribusi pada:

| Dimensi | Deskripsi |
| :--- | :--- |
| **Metodologis** | Penyediaan kerangka pengujian parametrik yang sistematis dan dapat direproduksi untuk strategi berbasis CBBI, mencakup dua skenario komplementer yang masing-masing melayani tujuan ilmiah dan tujuan eksplorasi yang berbeda namun saling memperkuat. |
| **Praktis** | Penyediaan antarmuka web interaktif yang memberikan alat bantu fungsional bagi investor ritel dalam melakukan simulasi strategi sesuai profil risiko masing-masing, sekaligus menyajikan hasil penelitian secara transparan dan dapat diakses publik. |
| **Akademis** | Penyumbangan referensi metodologi yang empiris bagi studi lanjutan di bidang optimisasi strategi perdagangan aset digital, khususnya yang berlandaskan pada indikator siklus on-chain dengan karakteristik frekuensi sinyal rendah. |

---

## 9. Risiko dan Mitigasi

| Risiko | Strategi Mitigasi | Implementasi di PRD |
| :--- | :--- | :--- |
| **Kendala waktu komputasi pada Grid Search** | Penerapan paralelisasi komputasi menggunakan multi-core CPU via `joblib`. Transisi ke algoritma heuristik (Bayesian → Genetic Algorithm) apabila durasi komputasi melampaui batas yang dapat diterima. | §4.6.1, §4.6.2, §4.6.3 |
| **Frekuensi sinyal sangat rendah pada OOS Skenario 1** | Kondisi ini diperlakukan sebagai temuan yang valid dan dilaporkan secara eksplisit. Skenario 2 dijalankan sebagai konteks komplementer untuk menunjukkan kinerja pada jendela waktu yang lebih panjang. | §4.2 (`low_sample_warning`), §4.4, §4.9 |
| **Kesalahpahaman interpretasi hasil Skenario 2** | Framing yang eksplisit dalam laporan dan aplikasi web: Skenario 2 adalah batas referensi eksplorasi historis, bukan bukti validitas prediktif. Disclaimer wajib ditampilkan pada setiap visualisasi hasil Skenario 2. | §4.5 (`DISCLOSURE WAJIB`), §4.7.2, §5.4.2 |
| **Overfitting terhadap data historis** | Penerapan Forward Test pada Skenario 1 dengan data Out-of-Sample yang sepenuhnya terisolasi. Analisis degradasi kinerja dikuantifikasi sebagai indikator overfitting dengan skala kategori yang jelas. | §4.4, §4.9 |
| **Keterbatasan akses data indikator CBBI** | Penggunaan data proksi yang transparan dan terdokumentasi. Seluruh keterbatasan dicatat dalam `source_limitations.md` sebagai bagian dari limitasi penelitian dalam laporan akhir. | §2.2.2, §2.6 |
| **Lookahead bias dalam logika eksekusi** | Penerapan aturan T+1 eksekusi secara ketat (sinyal dari `close[T]`, eksekusi di `open[T+1]`). Fungsi `validate_no_lookahead()` dijalankan sebagai gate wajib sebelum pipeline dilanjutkan. | §2.3, §4.2, §2.6 |
| **Keterbatasan representasi siklus pasar** | Penggunaan data sejak 2012 yang mencakup empat siklus halving penuh. Transparansi mengenai keterbatasan jumlah siklus historis yang tersedia dicantumkan dalam limitasi penelitian. | §2.2.1 |

---

## 10. Estimasi Jadwal Implementasi

| Bulan | Minggu | Target Kegiatan | Luaran |
| :---: | :---: | :--- | :--- |
| **1** | 1 | Studi literatur: CBBI, metrik on-chain, optimisasi parameter perdagangan kuantitatif. | Ringkasan 5–7 referensi akademis yang relevan. |
| | 2 | Eksplorasi dan pengumpulan data historis BTC (2012–2026) dan indikator CBBI dari seluruh sumber yang tersedia. | Dataset mentah tersimpan; dokumentasi sumber dan keterbatasan akses data (`source_limitations.md`). |
| | 3 | Prapemrosesan data: alignment, forward fill, normalisasi, dan verifikasi urutan kronologis. | Pipeline preprocessing tervalidasi; `master_dataset.parquet` siap analisis. |
| | 4 | Seleksi fitur: analisis korelasi Spearman, distribusi per kondisi pasar, pemeringkatan indikator. | Laporan analisis signifikansi statistik per indikator; `selected_indicators.json`. |
| **2** | 5 | Perancangan lingkungan simulasi, logika eksekusi sinyal beli/jual, dan mekanisme pencatatan percobaan untuk kedua skenario. | Skrip dasar sistem backtesting beroperasi dan terverifikasi. |
| | 6 | Implementasi Grid Search pada tiga fungsi objektif (Total Return, MDD, Sharpe Ratio). | Modul Grid Search terintegrasi; hasil percobaan awal tersimpan. |
| | 7 | Implementasi Bayesian Optimization (Optuna) dan Genetic Algorithm sebagai fallback dan alternatif heuristik. | Modul optimisasi heuristik terintegrasi. |
| | 8 | Uji coba awal komputasi untuk memastikan seluruh modul berjalan tanpa error dan pencatatan hasil berfungsi. | Sistem pipeline end-to-end tervalidasi. |
| **3** | 9 | Eksekusi komputasi Skenario 1: optimisasi In-Sample (2012–2020); pencatatan seluruh hasil percobaan. | Kumpulan data riwayat percobaan In-Sample; parameter optimal Skenario 1 teridentifikasi. |
| | 10 | Pelaksanaan Forward Test Skenario 1 (2021–2026); analisis degradasi kinerja IS vs OOS; komparasi dengan Buy and Hold. | Dokumen validasi kinerja Skenario 1; tabel perbandingan degradasi. |
| | 11 | Eksekusi komputasi Skenario 2: optimisasi full dataset (2012–2026); komparasi hasil dengan Skenario 1 dan Buy and Hold. | Kumpulan data riwayat percobaan Skenario 2; analisis komparatif kedua skenario. |
| | 12 | Verifikasi backtesting manual pada sampel transaksi representatif (20 titik, mencakup bull/bear/sideways); validasi nihilnya lookahead bias. | Dokumen verifikasi deterministik sebagai lampiran teknis. |
| **4** | 13 | Pengembangan antarmuka pengguna: Simulator Backtesting Bebas dan Halaman Hasil Penelitian (kedua skenario berdampingan). | Purwarupa aplikasi fungsional dengan fitur input parameter, visualisasi kinerja, dan disclaimer skenario. |
| | 14 | Pengujian dan penyempurnaan aplikasi web; integrasi komparasi kedua skenario; penambahan disclaimer pada visualisasi Skenario 2. | Aplikasi web siap demonstrasi. |
| | 15 | Penyusunan laporan akhir: metodologi, hasil Skenario 1, hasil Skenario 2, analisis komparatif, dan diskusi. | Draf laporan final (Bab 1–5). |
| | 16 | Finalisasi laporan, penyusunan materi presentasi, dan review pembimbing. | Laporan final dan materi presentasi siap disampaikan. |
