# Panduan Penelitian: Optimisasi Strategi Perdagangan Kripto Berbasis Indikator CBBI

---

## Judul Penelitian

**"Optimisasi Parameter Threshold dan Alokasi Aset Berbasis Indikator CBBI untuk Memaksimalkan Kinerja Portofolio Bitcoin"**

---

## Latar Belakang

Indikator Crypto Bull and Bear Index (CBBI) telah mendapatkan adopsi yang luas di kalangan komunitas kripto sebagai alat bantu keputusan investasi. Indeks ini mengintegrasikan sejumlah metrik on-chain dan metrik harga historis Bitcoin ke dalam satu nilai komposit berskala 0 hingga 100, yang merepresentasikan kondisi siklus pasar secara agregat. Penggunaannya di kalangan praktisi selama ini masih bertumpu pada nilai threshold yang bersifat intuitif dan tidak terstandarisasi, sehingga menghasilkan kinerja yang bervariasi antar pengguna.

Penelitian ini berfokus pada pengembangan kerangka kerja optimisasi kuantitatif untuk menemukan kombinasi parameter perdagangan yang paling ideal berdasarkan data historis. Parameter yang dioptimasi mencakup penentuan batas picu (threshold) beli dan jual, serta manajemen persentase alokasi aset pada setiap eksekusi transaksi. Pendekatan ini memungkinkan evaluasi yang lebih sistematis dan empiris terhadap potensi aktual indikator CBBI sebagai fondasi strategi perdagangan terstruktur.

Penelitian ini menjalankan dua skenario pengujian yang saling melengkapi: Skenario 1 mengikuti kaidah validasi akademis melalui pemisahan data In-Sample dan Out-of-Sample, sementara Skenario 2 mengeksplorasi batas potensi maksimal indikator menggunakan seluruh rentang data historis. Kombinasi dua sudut pandang ini menghasilkan analisis yang berbobot secara ilmiah sekaligus informatif secara praktis. Hasil akhir dari penelitian ini juga mencakup penyediaan aplikasi interaktif berbasis web yang memungkinkan pengguna akhir untuk melakukan simulasi pengujian secara mandiri sesuai dengan profil risiko masing-masing.

---

## Rumusan Masalah

1. Indikator spesifik mana yang memiliki tingkat signifikansi statistik tertinggi sebagai dasar pembuatan sinyal eksekusi perdagangan?
2. Berapa nilai batas picu beli dan jual beserta persentase alokasi aset yang paling optimal untuk menghasilkan metrik Total Return tertinggi?
3. Bagaimana konfigurasi parameter yang diperlukan untuk menghasilkan risiko terendah berdasarkan metrik Maximum Drawdown, serta tingkat pengembalian yang disesuaikan dengan risiko berdasarkan metrik Sharpe Ratio?
4. Seberapa besar selisih degradasi kinerja yang terjadi antara fase In-Sample dan Out-of-Sample pada Skenario 1, dan sejauh mana perbedaannya terhadap potensi kinerja historis maksimal yang ditemukan pada Skenario 2?

---

## Tinjauan Pustaka

Penelitian ini berlandaskan pada sejumlah kerangka konseptual dan referensi empiris yang relevan, antara lain:

- Literatur mengenai metrik on-chain Bitcoin sebagai indikator siklus pasar, mencakup MVRV Z-Score, NUPL, Puell Multiple, dan Reserve Risk.
- Studi mengenai optimisasi parameter pada sistem perdagangan algoritmik menggunakan metode Grid Search, Bayesian Optimization, dan Genetic Algorithm.
- Literatur backtesting kuantitatif pada pasar aset kripto, khususnya terkait penghindaran lookahead bias dan validasi berbasis walk-forward testing.
- Referensi metodologi pemisahan data In-Sample dan Out-of-Sample dalam konteks pengembangan strategi perdagangan yang robust.
- Kajian mengenai karakteristik siklus makro aset kripto dan implikasinya terhadap frekuensi sinyal perdagangan berbasis indikator on-chain.

Target kajian pustaka pada fase awal penelitian adalah merangkum minimal 5 hingga 7 referensi akademis yang mencakup topik-topik di atas sebagai fondasi argumentasi metodologis.

---

## Ruang Lingkup dan Batasan Parameter

Pencarian konfigurasi optimal dibatasi pada rentang nilai yang logis berdasarkan karakteristik siklus pasar kripto, guna menjaga efisiensi komputasi dan relevansi hasil.

- **Data Utama:** Data historis harga Bitcoin (BTC) periode 2012 hingga Maret 2026, bersumber dari Yahoo Finance (via `yfinance`) atau CoinGecko API sebagai alternatif.
- **Sumber Indikator CBBI:** Indikator-indikator penyusun CBBI diperoleh melalui berbagai sumber dengan tingkat aksesibilitas yang berbeda, sebagaimana diuraikan pada bagian Pengumpulan Data.
- **Threshold Buy (Skala 1–100):** Rentang pengujian dari nilai 1 hingga 45 dengan interval 1, mewakili asumsi pembelian pada fase konsolidasi atau akumulasi pasar.
- **Threshold Sell (Skala 1–100):** Rentang pengujian dari nilai 55 hingga 100 dengan interval 1, mewakili asumsi penjualan pada saat pasar menunjukkan indikasi jenuh beli.
- **Alokasi Buy (% dari Saldo Kas):** Rentang 1% hingga 25% dengan interval 1%, digunakan untuk evaluasi strategi pembelian bertahap.
- **Alokasi Sell (% dari Saldo BTC):** Rentang 1% hingga 25% dengan interval 1%, digunakan untuk evaluasi strategi pengambilan keuntungan secara bertahap.
- **Periode Skenario 1 — In-Sample:** 2012 hingga akhir 2020, digunakan secara eksklusif untuk proses optimisasi parameter.
- **Periode Skenario 1 — Out-of-Sample:** 2021 hingga Maret 2026, digunakan secara eksklusif untuk validasi dan forward test.
- **Periode Skenario 2 — Full Dataset:** 2012 hingga Maret 2026, digunakan sebagai satu kesatuan tanpa pemisahan untuk keperluan eksplorasi potensi maksimal.

---

## Metodologi

### Alur Penelitian

```
Pengumpulan Data Historis BTC + Indikator CBBI (2012-2026)
                            |
              Prapemrosesan Data (Forward Fill, Alignment)
                            |
               Seleksi Fitur & Analisis Signifikansi Statistik
                            |
         Perancangan Mesin Optimisasi (Logika Eksekusi & Skenario)
                            |
              +-------------+------------------+
              |                                |
   SKENARIO 1                            SKENARIO 2
   Pendekatan Validasi Akademis           Pendekatan Eksplorasi Maksimal
   Optimisasi In-Sample (2012-2020)       Optimisasi Full Dataset (2012-2026)
   [Grid Search | Bayesian | Genetic]     [Grid Search | Bayesian | Genetic]
              |                                |
   Forward Test OOS (2021-2026)          Tidak ada forward test
   Analisis Degradasi IS vs OOS           Pemetaan Potensi Historis Absolut
              |                                |
              +-------------+------------------+
                            |
         Pencatatan Seluruh Hasil Percobaan (Parquet / CSV / JSON)
                            |
       Komparasi Skenario 1 vs Skenario 2 vs Benchmark Buy and Hold
                            |
              Verifikasi Backtesting Manual (Deterministik)
                            |
         Pengembangan Aplikasi Web Interaktif (Dasbor Simulasi)
                            |
                Penyusunan Laporan Akhir & Presentasi
```

---

### Detail Setiap Tahap

#### 1. Pengumpulan Data

Data yang digunakan dalam penelitian ini bersumber dari beberapa platform dengan tingkat aksesibilitas yang berbeda-beda:

- **Harga Bitcoin Historis:** Yahoo Finance via `yfinance` (gratis, dapat diandalkan untuk data harian sejak 2012) atau CoinGecko API sebagai alternatif.
- **Indikator CBBI — Sumber per Komponen:**
  - *Glassnode (free tier):* MVRV Z-Score, NUPL (Net Unrealized Profit/Loss), Reserve Risk.
  - *CoinMetrics (free tier):* Puell Multiple, RHODL Ratio (approximation).
  - *Kalkulasi manual berbasis data harga historis:* Pi Cycle Top Indicator, 2-Year Moving Average Multiplier, Bitcoin Rainbow Chart.
  - *Catatan keterbatasan:* Tidak semua indikator tersedia secara lengkap dan gratis melalui API publik. Keterbatasan ini akan didokumentasikan secara transparan sebagai limitasi penelitian, dan data proksi yang digunakan akan dijelaskan secara eksplisit dalam laporan akhir.
- **Cakupan Data:** 2012 hingga Maret 2026, mencakup empat siklus halving penuh, memberikan representasi yang memadai atas dinamika siklus pasar Bitcoin.

#### 2. Prapemrosesan Data

- Penyelarasan seluruh indikator ke daily timeframe yang seragam.
- Penanganan nilai yang kosong (missing values) menggunakan metode forward fill, guna mempertahankan kesinambungan data tanpa menggunakan informasi masa depan.
- Verifikasi urutan kronologis data untuk memastikan tidak ada inversi temporal yang dapat mengkontaminasi proses komputasi.
- Normalisasi indikator ke skala [0, 100] sesuai format CBBI asli, untuk menjaga konsistensi interpretasi threshold.

#### 3. Seleksi Fitur dan Analisis Signifikansi Statistik

Tahap ini bertujuan mengidentifikasi indikator CBBI individual yang memiliki korelasi dan daya prediktif tertinggi terhadap pergerakan harga Bitcoin, sebelum digunakan sebagai basis sinyal pada mesin optimisasi. Proses yang dilakukan meliputi:

- Analisis korelasi Spearman antara setiap indikator dengan return Bitcoin pada berbagai lag waktu (7, 14, 30, 60, dan 90 hari).
- Analisis distribusi nilai indikator pada kondisi pasar yang berbeda (bull market, bear market, sideways).
- Pemeringkatan indikator berdasarkan nilai signifikansi statistik (p-value) dan koefisien korelasi.
- Dokumentasi indikator terpilih yang akan menjadi fondasi kalkulasi sinyal pada fase optimisasi.

#### 4. Optimisasi Algoritma Pencarian Parameter

Penelitian ini mengeksplorasi penggunaan beberapa metode pencarian untuk menemukan parameter optimal pada tiga fungsi objektif: memaksimalkan Total Return, meminimalkan Maximum Drawdown, dan memaksimalkan Sharpe Ratio. Algoritma yang diuji meliputi Grid Search sebagai metode primer yang memberikan hasil deterministik dan exhaustive, Bayesian Optimization via Optuna sebagai fallback apabila durasi komputasi Grid Search melampaui batas yang dapat diterima, serta Genetic Algorithm sebagai alternatif heuristik untuk ruang pencarian berukuran besar.

Ketiga algoritma di atas dijalankan secara identik untuk dua skenario berikut:

**Skenario 1 — Pendekatan Validasi Akademis (Split In-Sample / Out-of-Sample)**

Tujuan skenario ini adalah memenuhi standar ilmiah penelitian dengan membuktikan ketangguhan strategi di luar data yang digunakan dalam proses optimisasi. Algoritma dioptimalkan secara eksklusif menggunakan data In-Sample (2012 hingga akhir 2020). Parameter terbaik yang ditemukan kemudian diuji pada data Out-of-Sample (2021 hingga Maret 2026) yang sepenuhnya terisolasi dari proses optimisasi. Skenario ini merupakan tolok ukur validitas ilmiah penelitian.

Perlu dicatat bahwa indikator CBBI merupakan indikator makro yang bergerak lambat dan hanya mencapai nilai ekstrem beberapa kali dalam satu siklus halving. Apabila sistem sangat jarang membuka posisi pada periode Out-of-Sample akibat karakteristik ini, kondisi tersebut tetap merupakan temuan yang valid dan harus dilaporkan secara eksplisit, bukan disembunyikan atau dikecualikan dari pembahasan.

**Skenario 2 — Pendekatan Eksplorasi Maksimal (Full Dataset)**

Tujuan skenario ini adalah memetakan batas potensi absolut dari indikator CBBI sepanjang sejarah data yang tersedia. Algoritma dioptimalkan menggunakan seluruh rentang data historis (2012 hingga Maret 2026) sebagai satu kesatuan tanpa pemisahan. Pendekatan ini secara sadar mengabaikan risiko lookahead bias dalam proses optimisasinya. Fakta ini wajib dinyatakan secara eksplisit dalam laporan sebagai limitasi yang disadari, bukan sebagai kelemahan yang tersembunyi.

Skenario 2 menjamin algoritma memiliki jendela waktu yang cukup panjang untuk memicu banyak sinyal transaksi, sehingga metrik evaluasi memiliki dasar statistik yang lebih kuat. Hasil akhirnya menjawab pertanyaan: "Bagaimana wujud konfigurasi parameter yang paling menguntungkan sepanjang sejarah berdirinya Bitcoin?"

Dengan menjalankan dua skenario ini secara berdampingan, bab hasil dan pembahasan dapat menyajikan analisis dari sudut pandang pembuktian ilmiah (Skenario 1) sekaligus dari sudut pandang pencarian potensi maksimal (Skenario 2). Selisih antara kedua hasil tersebut merupakan bahan diskusi yang bernilai tinggi dalam konteks evaluasi indikator makro berbasis siklus.

#### 5. Pencatatan Hasil Percobaan

Sistem akan merekam seluruh komputasi percobaan ke dalam format file Parquet untuk trial log bervolume besar, serta CSV dan JSON untuk ringkasan hasil optimal. Atribut data yang dicatat mencakup:

| Atribut | Keterangan |
| :--- | :--- |
| `trial_id` | Nomor percobaan unik |
| `scenario` | Identifikasi skenario: `scenario_1` atau `scenario_2` |
| `algorithm` | Algoritma pencarian yang digunakan |
| `phase` | `in_sample`, `out_of_sample`, atau `full_dataset` |
| `date_start` / `date_end` | Tanggal mulai dan selesai periode simulasi |
| `initial_capital` | Modal awal yang digunakan |
| `threshold_buy` | Nilai batas picu beli |
| `threshold_sell` | Nilai batas picu jual |
| `allocation_buy_pct` | Persentase alokasi pembelian |
| `allocation_sell_pct` | Persentase alokasi penjualan |
| `final_portfolio_value` | Nilai akhir portofolio |
| `total_return_pct` | Persentase total keuntungan |
| `max_drawdown_pct` | Persentase penurunan nilai maksimum |
| `sharpe_ratio` | Rasio Sharpe |
| `win_rate` | Persentase transaksi menguntungkan |
| `trade_count` | Total jumlah transaksi yang terpicu |
| `excluded_low_trades` | Penanda percobaan dengan jumlah transaksi di bawah minimum validitas |

#### 6. Validasi Kinerja Out-of-Sample (Skenario 1)

Parameter optimal yang ditemukan pada fase In-Sample Skenario 1 diuji kembali secara eksklusif menggunakan data Out-of-Sample (2021 hingga Maret 2026) yang sepenuhnya terisolasi. Tahap ini bertujuan untuk membuktikan ketangguhan strategi pada kondisi pasar yang belum pernah dilihat oleh algoritma, mengidentifikasi dan mengkuantifikasi tingkat overfitting melalui analisis selisih degradasi kinerja, serta memberikan estimasi kinerja yang lebih realistis terhadap kondisi pasar nyata.

Interpretasi degradasi kinerja menggunakan skala berikut: degradasi di bawah 20% dikategorikan sebagai robust, antara 20% hingga 40% dikategorikan sebagai moderat, dan di atas 40% dikategorikan sebagai indikasi overfitting.

#### 7. Metrik Evaluasi dan Pembanding (Benchmark)

Kinerja seluruh strategi pada kedua skenario dievaluasi menggunakan empat metrik utama:

- **Total Return:** Persentase pertumbuhan total nilai portofolio dari modal awal.
- **Maximum Drawdown (MDD):** Penurunan nilai portofolio terbesar dari puncak ke titik terendah, sebagai representasi risiko sisi bawah.
- **Sharpe Ratio:** Rasio antara kelebihan imbal hasil terhadap volatilitas, sebagai ukuran efisiensi pengembalian yang disesuaikan dengan risiko.
- **Win Rate:** Persentase transaksi jual yang menghasilkan keuntungan positif terhadap total transaksi jual.

Seluruh hasil dari kedua skenario dikomparasikan secara langsung dengan kinerja strategi pasif Buy and Hold pada periode waktu yang setara. Khusus untuk Skenario 1, evaluasi menyoroti tingkat degradasi kinerja antar fase sebagai indikator robustness. Untuk Skenario 2, hasil dikomunikasikan sebagai referensi batas potensi historis, disertai pernyataan eksplisit mengenai ketidakmampuannya sebagai sinyal prediktif.

#### 8. Penanganan Distribusi Sinyal

Distribusi sinyal beli dan jual yang dihasilkan oleh threshold CBBI berpotensi tidak seimbang secara temporal. Kondisi pasar yang ekstrem (nilai CBBI sangat rendah atau sangat tinggi) secara alamiah lebih jarang terjadi dibandingkan kondisi konsolidasi, terutama pada periode Out-of-Sample Skenario 1 yang hanya mencakup satu siklus halving. Kondisi ini berimplikasi pada jumlah transaksi yang sangat terbatas untuk threshold yang terlalu ekstrem, sehingga metrik Win Rate dan Sharpe Ratio menjadi kurang representatif secara statistik.

Mitigasi yang diterapkan mencakup pencatatan jumlah transaksi sebagai atribut setiap percobaan dengan penetapan minimum trade count sebagai syarat validitas, pelaporan distribusi frekuensi sinyal per nilai threshold sebagai bagian dari analisis deskriptif, dan interpretasi metrik kinerja yang selalu disertai jumlah transaksi yang mendasarinya. Pada Skenario 2, jumlah transaksi yang lebih tinggi secara alamiah menjadi salah satu justifikasi metodologis penggunaan full dataset.

#### 9. Verifikasi Backtesting Manual

Tahap verifikasi dilakukan dengan mengambil parameter optimal hasil algoritma dan menjalankan simulasi ulang secara manual, langkah demi langkah, untuk tanggal-tanggal transaksi yang dipilih secara representatif dari kedua skenario. Proses ini bertujuan untuk memvalidasi akurasi perhitungan sistem secara deterministik, memastikan nihilnya lookahead bias dalam logika eksekusi program, dan mendokumentasikan setiap langkah kalkulasi sebagai lampiran teknis dalam laporan akhir.

#### 10. Pengembangan Aplikasi Web Interaktif

Tahap akhir mencakup pembuatan dasbor interaktif berbasis web dengan dua bagian utama:

**Simulator Backtesting Bebas:** Pengguna dapat mengatur seluruh parameter (threshold beli, threshold jual, alokasi, dan rentang tanggal) secara mandiri melalui slider dan kontrol interaktif. Rentang tanggal mencakup seluruh dataset 2012 hingga 2026 dan dapat diatur bebas oleh pengguna. Simulator ini bersifat independen dari kedua skenario penelitian dan tidak membuat klaim prediktif. Fitur ini melayani baik investor ritel yang ingin mencoba konfigurasi sesuai profil risiko, maupun peneliti yang ingin melakukan eksplorasi parameter tambahan.

**Halaman Hasil Penelitian:** Menampilkan parameter optimal dan metrik kinerja dari Skenario 1 dan Skenario 2 secara berdampingan, disertai komparasi terhadap benchmark Buy and Hold. Halaman ini dilengkapi disclaimer yang menjelaskan perbedaan interpretasi antara kedua skenario secara eksplisit, sehingga pengguna memahami bahwa hasil Skenario 2 tidak dapat digunakan sebagai sinyal prediktif.

---

## Risiko dan Mitigasi

| Risiko | Mitigasi |
| :--- | :--- |
| **Kendala waktu komputasi pada Grid Search** | Penerapan paralelisasi komputasi menggunakan multi-core CPU. Transisi ke algoritma heuristik (Bayesian atau Genetic Algorithm) apabila durasi komputasi melampaui batas yang dapat diterima. |
| **Frekuensi sinyal sangat rendah pada OOS Skenario 1** | Kondisi ini diperlakukan sebagai temuan yang valid dan dilaporkan secara eksplisit. Skenario 2 dijalankan sebagai konteks komplementer untuk menunjukkan kinerja pada jendela waktu yang lebih panjang dan lebih banyak siklus. |
| **Kesalahpahaman interpretasi hasil Skenario 2** | Framing yang eksplisit dalam laporan dan aplikasi web: Skenario 2 adalah batas referensi eksplorasi historis, bukan bukti validitas prediktif. Disclaimer wajib ditampilkan pada setiap visualisasi hasil Skenario 2. |
| **Overfitting terhadap data historis** | Penerapan Forward Test pada Skenario 1 dengan data Out-of-Sample yang sepenuhnya terisolasi. Analisis degradasi kinerja dikuantifikasi sebagai indikator overfitting. |
| **Keterbatasan akses data indikator CBBI** | Penggunaan data proksi yang transparan dan terdokumentasi. Seluruh keterbatasan dicatat sebagai bagian dari limitasi penelitian dalam laporan akhir. |
| **Lookahead bias dalam logika eksekusi** | Penerapan verifikasi backtesting manual secara deterministik. Seluruh keputusan didasarkan hanya pada data yang tersedia hingga hari sebelum eksekusi (T-1). |
| **Keterbatasan representasi siklus pasar** | Penggunaan data sejak 2012 yang mencakup empat siklus halving. Transparansi mengenai keterbatasan jumlah siklus historis yang tersedia untuk analisis dicantumkan dalam limitasi penelitian. |

---

## Kontribusi yang Diharapkan

Penelitian ini merumuskan kerangka kerja optimisasi terstruktur yang menghubungkan analisis metrik on-chain Bitcoin dengan praktik perdagangan kuantitatif berbasis data. Secara spesifik, penelitian ini berkontribusi pada:

- **Kontribusi metodologis:** Penyediaan kerangka pengujian parametrik yang sistematis dan dapat direproduksi untuk strategi berbasis CBBI, mencakup dua skenario komplementer yang masing-masing melayani tujuan ilmiah dan tujuan eksplorasi yang berbeda namun saling memperkuat.
- **Kontribusi praktis:** Penyediaan antarmuka web interaktif yang memberikan alat bantu fungsional bagi investor ritel dalam melakukan simulasi strategi sesuai profil risiko masing-masing, sekaligus menyajikan hasil penelitian secara transparan dan dapat diakses publik.
- **Kontribusi akademis:** Penyumbangan referensi metodologi yang empiris bagi studi lanjutan di bidang optimisasi strategi perdagangan aset digital, khususnya yang berlandaskan pada indikator siklus on-chain dengan karakteristik frekuensi sinyal rendah.

---

## Estimasi Jadwal Penelitian

| Bulan | Minggu | Target Kegiatan | Luaran |
| :---: | :---: | :--- | :--- |
| **1** | 1 | Studi literatur: CBBI, metrik on-chain, optimisasi parameter perdagangan kuantitatif. | Ringkasan 5–7 referensi akademis yang relevan. |
| | 2 | Eksplorasi dan pengumpulan data historis BTC (2012–2026) dan indikator CBBI dari seluruh sumber yang tersedia. | Dataset mentah tersimpan; dokumentasi sumber dan keterbatasan akses data. |
| | 3 | Prapemrosesan data: alignment, forward fill, normalisasi, dan verifikasi urutan kronologis. | Pipeline preprocessing tervalidasi; dataset bersih siap analisis. |
| | 4 | Seleksi fitur: analisis korelasi Spearman, distribusi per kondisi pasar, dan pemeringkatan indikator. | Laporan analisis signifikansi statistik per indikator; daftar indikator terpilih. |
| **2** | 5 | Perancangan lingkungan simulasi, logika eksekusi sinyal beli/jual, dan mekanisme pencatatan percobaan untuk kedua skenario. | Skrip dasar sistem backtesting beroperasi dan terverifikasi. |
| | 6 | Implementasi Grid Search pada tiga fungsi objektif (Total Return, MDD, Sharpe Ratio). | Modul Grid Search terintegrasi; hasil percobaan awal tersimpan. |
| | 7 | Implementasi Bayesian Optimization (Optuna) dan Genetic Algorithm sebagai fallback. | Modul optimisasi heuristik terintegrasi. |
| | 8 | Uji coba awal komputasi untuk memastikan seluruh modul berjalan tanpa error dan pencatatan hasil berfungsi. | Sistem pipeline end-to-end tervalidasi. |
| **3** | 9 | Eksekusi komputasi Skenario 1: optimisasi In-Sample (2012–2020); pencatatan seluruh hasil percobaan. | Kumpulan data riwayat percobaan In-Sample; parameter optimal Skenario 1 teridentifikasi. |
| | 10 | Pelaksanaan Forward Test Skenario 1 (2021–2026); analisis degradasi kinerja IS vs OOS; komparasi dengan Buy and Hold. | Dokumen validasi kinerja Skenario 1; tabel perbandingan degradasi. |
| | 11 | Eksekusi komputasi Skenario 2: optimisasi full dataset (2012–2026); komparasi hasil dengan Skenario 1 dan Buy and Hold. | Kumpulan data riwayat percobaan Skenario 2; analisis komparatif kedua skenario. |
| | 12 | Verifikasi backtesting manual pada sampel transaksi representatif dari kedua skenario; validasi nihilnya lookahead bias. | Dokumen verifikasi deterministik sebagai lampiran teknis. |
| **4** | 13 | Pengembangan antarmuka pengguna: Simulator Backtesting Bebas dan Halaman Hasil Penelitian (kedua skenario berdampingan). | Purwarupa aplikasi fungsional dengan fitur input parameter, visualisasi kinerja, dan disclaimer skenario. |
| | 14 | Pengujian dan penyempurnaan aplikasi web; integrasi komparasi kedua skenario; penambahan disclaimer pada visualisasi Skenario 2. | Aplikasi web siap demonstrasi. |
| | 15 | Penyusunan laporan akhir: metodologi, hasil Skenario 1, hasil Skenario 2, analisis komparatif, dan diskusi. | Draf laporan final (Bab 1–5). |
| | 16 | Finalisasi laporan, penyusunan materi presentasi, dan review pembimbing. | Laporan final dan materi presentasi siap disampaikan. |

---

## Alat dan Lingkungan Kerja

- **Pengelolaan Data:** `yfinance`, `requests` (CoinGecko / Glassnode API), `pandas`, `numpy`
- **Optimisasi dan Pemodelan:** `Optuna` (Bayesian Optimization), implementasi kustom Genetic Algorithm, `scikit-learn` (analisis statistik dan seleksi fitur), `joblib` (paralelisasi Grid Search)
- **Backtesting:** Implementasi manual berbasis `pandas` untuk kontrol penuh atas logika eksekusi dan penghindaran lookahead bias
- **Visualisasi Data:** `plotly`, `matplotlib`, `seaborn`
- **Kerangka Aplikasi Web:** Streamlit atau Dash (ditentukan pada awal Fase 4)
- **Environment Kerja:** Jupyter Notebook untuk eksplorasi dan pengembangan iteratif; modul final dikemas dalam file `.py` terstruktur
- **Versioning Kode:** Git dan GitHub — seluruh skrip, konfigurasi eksperimen, dan catatan revisi dikelola dalam satu repositori terpusat
- **Format Penyimpanan Hasil:** Parquet untuk trial log bervolume besar; CSV dan JSON untuk ringkasan dan konsumsi frontend
