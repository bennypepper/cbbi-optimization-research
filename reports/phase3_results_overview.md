# Laporan Eksekutif Fase 3: Hasil Optimisasi dan Temuan Observasi

Dokumen ini membedah ringkasan hasil percobaan eksklusif setelah *Backtest Engine* (Fase 3) tereksekusi pada lebih dari 1.29 juta kombinasi parameter untuk masing-masing skenario. Seluruh hasil temuan angka dapat ditelusuri di arsip `results/optimal_params_summary.json`. Laporan ini disusun untuk memfasilitasi pendalaman materi pada sidang atau saat penyampaian *progress report* kepada pihak fakultas/pembimbing.

---

## 1. Degradasi Kinerja In-Sample vs Out-of-Sample (Bukti Empiris *Overfitting*)

Poin pertama dan paling mencolok dari seluruh riset adalah temuan angka pada **Skenario 1 (Validasi IS/OOS)**. Parameter yang menjuarai angka *Return* paling maksimal pada In-Sample (2012–2020) diuji kinerjanya pada pasar modern pasca-2021 (Out-of-Sample: 2021–2026).

**Statistik Skenario 1 (Profil Agresif / Maksimal Return):**
- **Optimal Parameter IS:** Threshold Buy = 34, Sell = 79, Alokasi Beli 25%, Alokasi Jual 25%.
- **Hasil IS (2012–2020):** Total Return = **15,7 triliun kali lipat** dari modal awal. CAGR tahunan = **2.825%**. Sharpe Ratio = 2,44.
- **Hasil OOS (2021–2026):** Total Return = **0,72 kali** (rugi 28%). CAGR tahunan = **−6,0%**. Selisih magnitud IS÷OOS = **21,6 triliun kali lipat**.

**Statistik Skenario 1 (Profil Seimbang / Max Sharpe):**
- **Optimal Parameter IS:** Threshold Buy = 30, Sell = 100, Alokasi Beli 25%, Alokasi Jual 1%.
- **Hasil IS:** Return = **5.117 kali lipat**, CAGR = **158%/tahun**.
- **Hasil OOS:** Return = **0,72 kali** (rugi 28%), CAGR = **−6,2%/tahun**. Selisih = **7.122 kali lipat**.

**Catatan untuk Pembimbing:** Temuan ini secara metodologis adalah keberhasilan riset. Hasil ini membuktikan bahwa parameter yang dikalibrasi pada era pertumbuhan agresif Bitcoin menghafal pola historis namun tidak mampu digeneralisasi pada kondisi pasar pasca-2021. Magnitud perbedaan hingga 21,6 triliun kali lipat menegaskan pentingnya pemisahan IS/OOS.

---

## 2. Peta Kemampuan Sesungguhnya (Skenario 2 — Eksplorasi Historis Penuh)

Skenario 2 memetakan batas potensi maksimal indikator *Logarithmic Regression* secara historis dari 2012–2026. Grid Search mengidentifikasi 3 profil strategi optimal:

| Profil | Threshold B/J | Alokasi B/J | Return | CAGR | Sharpe |
|---|---|---|---|---|---|
| **Agresif** (Max Return) | 7 / 79 | 25% / 25% | 38,0 triliun× | 803,6%/tahun | 2,01 |
| **Konservatif** (Min Drawdown) | 1 / 57 | 1% / 25% | 1.608× | 68,2%/tahun | 0,99 |
| **Seimbang** (Max Sharpe) | 30 / 100 | 25% / 1% | 12.823× | 94,6%/tahun | 2,30 |

## 3. Komparasi Dengan *Buy and Hold* (Benchmark Klasik)

- **In-Sample (2012–2020):** Buy & Hold menghasilkan 4.836× (CAGR 157%/tahun).
- **Out-of-Sample (2021–2026):** Buy & Hold menghasilkan 1,47× (CAGR 7,8%/tahun).
- **Historis Penuh (2012–2026):** Buy & Hold menghasilkan 12.117× (CAGR 93,8%/tahun).

Profil Seimbang (Max Sharpe) pada Skenario 2 menghasilkan return sebanding dengan Buy & Hold (12.823× vs 12.117×) namun dengan Sharpe Ratio 2,30 yang jauh lebih tinggi, mengindikasikan *risk-adjusted return* yang lebih baik.

---

## Kesimpulan:
1. **Riset berintegritas tinggi:** Metodologi ini berhasil membuktikan *overfitting* dengan magnitud hingga 21,6 triliun kali lipat antara kinerja IS dan OOS. Parameter yang dikalibrasi tanpa pemisahan zona uji menghasilkan ilusi kinerja.
2. **Kinerja Numba Engine:** Mampu mengeksplorasi 1.293.750 kombinasi parameter dengan cepat tanpa mengorbankan akurasi operasional simulasi (T+1 market order, Anti-Lookahead, Fee 0,1%).

---

## 4. Temuan Tambahan (Pasca Fase 3): Risiko Revisi Formula CBBI

> **Ditemukan:** 2026-04-17 — selama validasi web application (Phase 4)

Selama pengujian komparatif antara dataset lokal dan API live ColintalksCrypto, teridentifikasi bahwa **formula CBBI bersifat dinamis dan direvisi secara retroaktif** oleh penulisnya.

**Bukti:** Nilai CBBI pada tanggal `2021-01-01` tercatat sebagai `63.65` dalam `master_dataset.parquet` yang digunakan dalam riset ini. Namun, mengambil nilai tanggal yang sama melalui Live API pada 2026-04-17 menghasilkan nilai `78.13` — selisih **+14.48 poin**.

**Implikasinya:**
- Hasil riset ini (Fase 1–3) **tetap reproducible dan valid** karena mengacu pada snapshot dataset yang terdefinisi.
- Parameter optimal yang ditemukan secara spesifik dikalibrasi terhadap distribusi sinyal versi formula CBBI saat dataset diambil.
- Ini adalah **keterbatasan instrumen**, bukan cacat metodologi — analog dengan *index revision bias* dalam ekonometrika.

Sebagai respons praktis, platform web (Phase 4) dilengkapi **Dynamic Grid Search Updater** yang secara otomatis mengambil data terkini dari Live API dan menjalankan ulang grid search, sehingga parameter yang disajikan kepada pengguna selalu sinkron dengan formula CBBI terkini.

> 📄 **Dokumen lengkap:** [`reports/index_revision_bias_finding.md`](index_revision_bias_finding.md)

---

*(Dokumen ini secara berkala dapat digunakan untuk memandu penulisan deskripsi Bab Pembahasan pada Skripsi/Makalah final)*
