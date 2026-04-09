# Catatan Metodologi — Fase 3: Mesin Optimisasi & Asumsi Kuantitatif

**Dokumen ini mendokumentasikan spesifikasi teknis dan penyesuaian metodologi akhir yang diimplementasikan pada Fase 3 (Mesin Optimisasi), atas persetujuan dan konfirmasi yang dilakukan sebelum penulisan mesin sistem.** Tujuannya adalah untuk memberikan transparansi penuh agar tidak terjadi *hidden methodology* atau asumsi tersembunyi ketika mempresentasikan laporan kepada dosen pembimbing.

---

## 1. Implementasi Arsitektur Backtesting: Optimisasi *Numba JIT*
Dalam PRD awal, optimisasi Grid Search (*brute-force* parameter kombinasi sebanyak 1.293.750 probabilitas) diestimasi akan memakan waktu 30-40 menit karena berencana menggunakan *iterative loops* biasa (`Pandas` dan `Joblib`). 

**Penyesuaian Metodologi:**
Sistem backtesting telah dirancang ulang menggunakan konversi fungsi dan array *NumPy* serta di-compile memakai **Numba JIT (Just-In-Time Compiler)**. 
- **Presisi Akurasi:** Tidak ada yang dikorbankan. Akurasi penjaminan kualitas backtesting (T+1 pelaksanaan harga *Open*, dll) dieksekusi identik dan 100% deterministik. Numba bertugas melakukan kompilasi logika Python ini menjadi bahasa mesin tingkat rendah (setara performanya dengan instruksi C++).
- **Efisiensi:** Rangkaian loop raksasa yang tadinya memakan puluhan menit kini bisa dicapai dalam hitungan puluhan **detik** saja, merampingkan siklus litbang (*R&D*) untuk eksplorasi parameter yang lebih leluasa.

---

## 2. Parameter Annualized Volatility: Basis `365` Hari (Cerminan Aset Kripto)
Di dalam instrumen konvensional (Pasar Saham/Forex), perhitungan volatilitas pada *Sharpe Ratio* umumnya dikalikan dengan `sqrt(252)` yang merepresentasikan total estimasi hari buka bursa selama setahun.

**Penyesuaian Metodologi:**
Berhubung pada Fase 1 (*Data Pipeline*) kita membangun dataset Bitcoin yang temporalitasnya penuh secara harian (karena Kripto berjalan 24 jam sehari, 7 hari seminggu tanpa akhir pekan)—sistem mengganti standar kalibrasi tersebut agar sesuai secara hakikat statistik dan empiris, yaitu dengan **`sqrt(365)`**.
Penggunaan `365` memperbolehkan kita memberikan analisis volatilitas *risk-reward* yang sesuai dengan durasi sirkulasi asli aset Bitcoin, bukan sekadar penyerupaan (imitasi) terhadap instrumen ekuitas.

---

## 3. Realisme Kinerja: Penerapan Trading Fee Terukur (0.1%)
Mendesain backtest tanpa gesekan modal/biaya tersembunyi memungkinkan adanya probabilitas margin simulasi yang melebih-lebihkan keadaan sebenarnya. Di PRD awal belum ada perlakuan terhadap biaya (*transaction fees* / slippage).

**Penyesuaian Metodologi:**
Agar presentasi riset di atas kertas terlihat kredibel, adil, dan logis di level akademis, seluruh transaksi pemindahan aset di dalam simulasi (baik `Pembelian BTC` maupun `Penjualan BTC`) akan otomatis dipotong _administrative spot fee_ pertukaran. 
- **Tarif Flat yang Digunakan:** `0.1%` (0.001) per transaksi. 
- **Justifikasi:** Tarif ini adalah representasi konstan atas struktur *fee spot market* (Taker / Maker) yang berlaku rata-rata secara dominan pada bursa kelas dunia saat ini seperti Binance. Hal ini menjamin kalkulasi `Maximum Drawdown` dan laba (`Total Return`) berpotensi jauh lebih realistis tanpa membebani profit hingga margin merugikan.

---

Dengan ketiga poin landasan kuantitatif ini, proses validasi dan operasional Fase 3 untuk Skenario 1 (Validasi IS/OOS) serta Skenario 2 (Full Data Historical Exploration) kini dinyatakan tertutup rapat (*watertight*) dari kelemahan sistem logis maupun asumtif (*lookahead bias*).
