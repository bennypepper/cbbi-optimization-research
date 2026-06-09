# Audit Manual Komprehensif: Fase 1 hingga Fase 3 (Optimisasi CBBI)

Dokumen ini merupakan panduan audit manual yang mendetail dan menyeluruh untuk memverifikasi setiap aspek krusial dari penelitian "Optimalisasi Parameter Trading Bitcoin Menggunakan Grid Search pada Tiga Metrik Evaluasi Berbasis Indikator Logarithmic Regression". 

Pastikan setiap poin diuji dan divalidasi sebelum melanjutkan ke Fase 4 (Aplikasi Web).

---

## 🔍 FASE 1: Verifikasi Integritas Data (Data Pipeline)

Fase 1 adalah fondasi. Data yang kotor atau bias akan menghasilkan kesimpulan yang tidak valid pada fase selanjutnya (Garbage In, Garbage Out).

### 1.1. Batas Garis Waktu (IS vs OOS)
*   **Tujuan:** Memastikan pemisahan data In-Sample (IS) dan Out-of-Sample (OOS) tepat sesuai spesifikasi desain penelitian.
*   **Tindakan:**
    *   Buka file data hasil proses: `data/processed/master_dataset.parquet`. (Gunakan Jupyter Notebook atau Python script sementara untuk inspeksi).
    *   **Periksa titik pisah:** Pastikan data tepat pada tanggal **31 Desember 2020** dan sebelumnya berlabel `phase = "in_sample"`.
    *   **Periksa titik mulai OOS:** Pastikan data yang dimulai pada **1 Januari 2021** (sampai akhir dataset) berlabel `phase = "out_of_sample"`.

### 1.2. Pengecekan Kebocoran Harga (Anti-Lookahead Bias pada Pipeline)
*   **Tujuan:** Membuktikan secara deterministik bahwa tidak ada data harga (Open/Close) masa depan yang ditarik atau tercampur ke baris data masa lalu saat preprocessing.
*   **Tindakan:**
    *   Ambil 5 tanggal acak (misal: saat bull run 2017, crash 2020, dan sideway 2019) dari `master_dataset.parquet`.
    *   Bandingkan nilai `btc_close` (harga penutupan hari T dari sumber XLSX) dan `btc_open` (harga pembukaan hari T+1 dari yfinance) dengan data mentah `yfinance` pada hari yang spesifik.
    *   Pastikan baris `btc_open` pada tanggal T memang benar-benar nilai pembukaan tanggal T. (Konfirmasi bahwa algoritma tidak tidak sengaja men-_shift_ data terlalu awal yang berpotensi membocorkan data).

### 1.3. Penanganan Gap dan Fill Flag
*   **Tujuan:** Memastikan pengisian kekosongan data (*missing values*) via forward fill dilakukan sesuai batasan tanpa mencederai aturan *no lookahead*.
*   **Tindakan:**
    *   Cek file `data/metadata/fill_log.csv`.
    *   Pastikan tidak ada data yang difill mundur (*backward fill*).
    *   Pastikan *forward fill* tidak lebih dari 7 hari berturut-turut.

---

## 📊 FASE 2: Verifikasi Basis Statistik dan Pemilihan "Trolololo"

Fase 2 mendikte arah pemilihan indikator. Kita tidak menembak parameter buta, melainkan bersandar pada landasan Spearman Rank.

### 2.1. Validasi Angka Signifikansi Spearman (Trolololo Dominance)
*   **Tujuan:** Memverifikasi alasan pemilihan "Trolololo" sebagai indikator paling signifikan yang dioptimasi.
*   **Tindakan:**
    *   Buka laporan: `reports/feature_selection_report.md`.
    *   Buka file output data: `analysis/spearman_results.csv` atau `analysis/indicator_ranking.csv`
    *   **Fokus Audit:** Periksa tabel atau angka korelasi untuk "Trolololo". Apakah koefisien Spearman ($\rho$) menunjukkan angka negatif yang kuat dan konsisten?
    *   **Fokus Audit (Crucial):** Apakah p-Value untuk Trolololo tercatat sangat dekat dengan nol (misal: 0.0000 atau di bawah 0.05) pada lag waktu utama (misal 30/60 hari)? **Ini adalah argumen utama untuk sidang.**

### 2.2. Bukti Visual Distribusi (Boxplot Analysis)
*   **Tujuan:** Mengonfirmasi secara visual bahwa "Trolololo" mampu membedakan jenis kondisi pasar (accumulation, neutral, distribution, euphoria).
*   **Tindakan:**
    *   Akses direktori: `reports/charts/` (atau nama folder tempat gambar disimpan).
    *   Buka grafik Boxplot distribusi untuk "Trolololo".
    *   **Kriteria Lulus:** Dengan mata telanjang, Anda harus dapat melihat rentang distribusi/median "Trolololo" *berbeda* dan memiliki *kesejangan* (gap/gradasi) jelas di setiap zona (akumulasi hingga euforia), dibandingkan indikator lain yang mungkin kotak distribusinya tumpang tindih (*overlap*).

---

## ⚙️ FASE 3: Audit Mesin Simulasi (Sangat Krusial)

Fase ini membuktikan bahwa tidak ada "Magic Math" dari program (Anti-Lookahead Bias tingkat eksekusi) dan sistem berjalan realistis. **Gunakan simulator CLI (`verify_manual.py`) untuk tahap ini.**

### 3.1. Kepatuhan Pelaksanaan Eksekusi T+1 (Anti-Lookahead Eksekusi)
*   **Tujuan:** Memastikan mesin mengeksekusi pembelian pada saat market baru buka pada H+1 karena menuruti sinyal dari Harga Penutupan H, bukan memanfaatkan bocoran harga masa depan / low price masa kini.
*   **Tindakan:**
    *   Jalankan terminal CLI Simulator: `python -m src.optimization.verify_manual` (lihat panduan shortcut di bawah).
    *   Cari atau paksa satu transaksi Buy/Sell yang terjadi (Misal: Sinyal muncul di log pada tanggal **28 April** saat close).
    *   **Audit Cek:** Periksa harga pada log pencatatan portofolionya. Harga yang digunakan *WAJIB* adalah rasio harga Open dari tanggal **29 April** (keesokan harinya).
    *   Croscheck dengan internet: Cari harga btc_open pada "29 April" di data historis web. Jika angkanya cocok sempurna: LULUS.

### 3.2. Uji Kalkulator: Ketepatan Pemotongan Biaya (0.1% Spot Fee)
*   **Tujuan:** Memastikan *trading fee* (Slippage/taker fee) dihitung presisi untuk menambah realisme keuntungan. (Sesuai `phase3_methodology_notes.md`)
*   **Tindakan:**
    *   Ambil Kalkulator fisik/HP Anda.
    *   Ambil 1 contoh transaksi Buy dari log terminal Simulator.
    *   **Skenario Bukti:** Modal kas misal \$25,000. Sistem mengalokasikan 100% kas untuk pembelian (atau sekian persen).
    *   **Rumus Verifikasi:** 
        *   Hitungan Kas Kotor: \$25,000
        *   Fee 0.1% = \$25,000 * 0.001 = \$25
        *   Sisa Kas Bersih untuk Eksekusi: \$24,975.
        *   Total Koin yang Diberikan: \$24,975 / Btc_Open_T+1
    *   Jika jumlah BTC yang tertera pada balance sesudah trade _persis sama_ dengan hasil kalkulator Anda: LULUS.

### 3.3. Penyeimbangan Metrik Sharpe Berbasis Volatilitas Kripto (\sqrt{365})
*   **Tujuan:** Memvalidasi klaim penyesuaian perhitungan alam Kripto sesuai dokumen catatan metodologi.
*   **Tindakan:**
    *   Bedah file code fungsi objektif pada folder src. (Misalnya `src/optimization/metrics_calculator.py` atau sejenisnya).
    *   Cari fungsi komputasi `sharpe_ratio`.
    *   Pastikan akar pengalinya adalah *square root* dari **365**, bukan angka 252 (standar hari bursa saham).

### 3.4. Investigasi Puncak dan Valim Parameter (Analisis Degradasi)
*   **Tujuan:** Memastikan ada cerita dan temuan koheren yang bisa dinarasikan terkait mengapa sebuah setelan optimal dapat gagal, serta mengkonfirmasi pemaparan overfitting.
*   **Tindakan:**
    *   Buka file rekap kinerja: `results/optimal_params_summary.json` (atau direktori yang ekuivalen nantinya).
    *   Bandingkan kinerja model dari grup *Skenario 1 - In Sample* vs kinerjanya saat diuji coba ke data *Out of Sample* (tahun 2021-2026).
    *   Soroti persentase pada _sub-key_ **`degradation`**.
    *   **Skrip Narasi Anda:** Amati dan bangun argumen yang logis (contoh: "Model yang memaksimalkan return gila-gilaan pada tahun 2017 [IS] ternyata mengalami degradasi sampai -45% di OOS akibat tak ada bull market yang setara. Sementara itu, model yang difokuskan pada meminimalisasi Drawdown [Keamanan], degradasinya sangat minimal, membuatnya jadi parameter paling *robust*").

---

## 🚀 Shortcut & Command Eksekusi Terminal (Cheatsheet)

Jalankan perintah ini di VSCode/Terminal dari _root directory_ repositori Anda.

| Tujuan Uji Coba | Command Eksekusi |
| :--- | :--- |
| **Menjalankan CLI Simulator (Interaktif)** | `python -m src.optimization.verify_manual` |
| **Menjalankan Ulang Data Pipeline** *(Opsional, hanya jika data dirasa corrupt)* | `python -m src.data.preprocessor` (atau modul pipeline utama) |
| **Menjalankan Ulang Fase Seleksi (Spearman)** *(Opsional)* | `python -m src.analysis.feature_selector` |
| **Jalankan Ulang Full Backtest Grid Search Skenario 1 & 2** | *Terlampir dari skrip run utama jika ada, cth:* `python -m src.optimization.runner` |

**Tips Praktikal di CLI Simulator:**
Saat Anda ditanya di CLI, pastikan Anda mencoba meng-input data agresif (Alokasi 100%) dan data konservatif untuk menekan ujung-ujung perhitungan kalkulator.

---

## 🌐 FASE 4: Verifikasi Aplikasi Web & Temuan Index Revision Bias

> **Status:** Selesai — 2026-04-17

Fase ini mencakup validasi platform simulasi interaktif (Phase 4 — Web App) dan mendokumentasikan temuan penting yang muncul selama proses tersebut.

### 4.1. Paritas Engine IS/OOS antara CLI dan Web App

*   **Tujuan:** Memastikan engine di web app (pada repository web app `core/engine.py`) identik secara matematis dengan CLI prototype (`src/optimization/verify_manual.py`).
*   **Hasil:** ✅ **LULUS** — Kedua engine menghasilkan jumlah trade identik (465 transaksi) dan return identik (+141.2%) pada parameter dan rentang tanggal yang sama, menggunakan data Historical CSV.

### 4.2. Pengecekan Scaling API

*   **Tujuan:** Memastikan data dari Live CBBI API diskalakan dengan benar sebelum dimasukkan ke engine.
*   **Temuan & Perbaikan:** API Live ColintalksCrypto mengembalikan nilai Confidence sebagai desimal (`0.0–1.0`), sementara engine mengasumsikan skala persentase (`0–100`). Diperbaiki di repositori web app (`core/data_loader.py`) dengan mengalikan nilai ingest Live API dengan `× 100.0`.
*   **Hasil:** ✅ **DIPERBAIKI** — Engine sekarang memproses sinyal dengan benar dari kedua sumber data.

### 4.3. Investigasi & Dokumentasi: CBBI Index Revision Bias ⚠️

*   **Tujuan:** Menjelaskan mengapa penggunaan Live CBBI API dengan parameter optimal hasil riset menghasilkan performa yang berbeda dari backtest berbasis snapshot.
*   **Temuan:**

    | Aspek | Detail |
    |---|---|
    | **Fenomena** | API Live ColintalksCrypto melakukan recalculation retroaktif atas seluruh histori indeks setiap formula direvisi |
    | **Bukti empiris** | Nilai `2021-01-01`: snapshot riset = `63.65` vs Live API (2026-04-17) = `78.13` → drift **+14.48 poin** |
    | **Dampak praktis** | Parameter optimal dikalibrasi terhadap distribusi sinyal lama → misfit dengan distribusi sinyal baru → performa berbeda |
    | **Klasifikasi** | *Index Revision Bias* — keterbatasan instrumen, bukan cacat metodologi |

*   **Status riset Fase 1–3:** ✅ **TETAP VALID** — Semua hasil dapat direproduksi terhadap snapshot dataset yang terdefinisi.
*   **Respons praktis (Phase 4):** Dynamic Grid Search Updater — mengambil data Live API → menjalankan ulang grid search → menghasilkan `live_optimal_params.json` yang selalu sinkron.

*   📄 **Dokumentasi lengkap:** [`reports/index_revision_bias_finding.md`](reports/index_revision_bias_finding.md)

### 4.4. Audit Batas Penelitian vs Platform Deployment

*   **Tujuan:** Memisahkan secara eksplisit apa yang merupakan lingkup riset dan apa yang merupakan ekstensi platform.

    | Komponen | Lingkup |
    |---|---|
    | `master_dataset.parquet` + Fase 1–3 results | **Riset akademik** — tidak berubah, reproducible |
    | Simulator dengan Historical CSV | **Riset akademik** — alat verifikasi parameter |
    | Dynamic Grid Search Updater | **Platform praktis** — di luar lingkup riset akademik, sebagai "Future Work" |
    | Live API comparison | **Temuan riset tambahan** — didokumentasikan sebagai keterbatasan |

---

*Audit Fase 4 selesai. Seluruh checkpoint telah didokumentasikan.*

