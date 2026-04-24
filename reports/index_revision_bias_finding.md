# Temuan Tambahan: Risiko Revisi Indeks CBBI (Index Recalculation Bias)

**Ditemukan:** 2026-04-17  
**Konteks:** Ditambahkan pasca-validasi web application (Phase 4), selama sesi uji komparatif antara dataset lokal (`master_dataset.parquet`) dan API live ColintalksCrypto.

---

## Ringkasan Temuan

Selama pengujian simulator interaktif (Phase 4 — Web App), teridentifikasi bahwa **algoritma CBBI bersifat dinamis**: Colin Talks Crypto secara berkala merevisi formula indeksnya (contoh: menghapus metrik Stock-to-Flow dari komposisi) dan **perhitungan ulang tersebut berlaku retroaktif** terhadap seluruh histori data yang tersedia di API.

### Bukti Empiris

| Tanggal Historis | Nilai di `master_dataset.parquet` (snapshot riset) | Nilai via Live API (2026-04-17) | Selisih |
|---|---|---|---|
| 2021-01-01 | `63.65` | `78.13` | **+14.48 poin** |

Drift sebesar ~14 poin ini bukan anomali — ini adalah hasil revisi metodologi resmi dari pihak CBBI.

---

## Implikasi terhadap Hasil Riset

### Apa yang TIDAK berubah:
- **Seluruh hasil riset (Fase 1–3) tetap valid dan reproducible.** Dataset yang digunakan adalah snapshot tetap (`master_dataset.parquet`) yang tercatat waktu pengambilannya.
- Parameter optimal yang ditemukan (buy/sell threshold, alokasi aset) adalah **optimal terhadap dataset yang dipelajari** — ini adalah standar akademik yang benar.
- Metodologi anti-lookahead bias, pemisahan IS/OOS, dan mekanisme engine sudah tervalidasi penuh (lihat `audit_results/`).

### Apa yang perlu dikontekstualisasikan dalam laporan:
- Parameter optimal hasil riset ini dikalibrasi terhadap **versi formula CBBI per periode pengambilan data**.
- Apabila diterapkan pada API live (yang menggunakan formula terkini), performa aktual mungkin berbeda karena distribusi sinyal telah bergeser.
- Ini adalah **keterbatasan inheren dari instrumen**, bukan cacat metodologi.

---

## Framing Akademis: Ini Adalah Temuan, Bukan Kelemahan

Fenomena ini identik dengan konsep yang mapan dalam literatur ekonometrika: **Index Revision Bias** — bias yang timbul ketika sebuah indeks ekonomi (contoh: GDP, CPI) direvisi retroaktif setelah data awal dipublikasikan.

Dalam konteks riset ini:
> *"Strategi yang dioptimasi pada snapshot CBBI tertentu akan mengalami parameter drift apabila formula CBBI diperbarui, karena distribusi sinyal historis berubah secara retroaktif."*

Ini adalah **kontribusi riset yang valid**: mendeskripsikan dan mendokumentasikan risiko structural CBBI sebagai instrumen yang tidak statis.

---

## Respons Praktis: Arsitektur Dynamic Grid Search Updater (Phase 4)

Sebagai jawaban praktis atas keterbatasan ini, aplikasi web (Phase 4) dirancang dengan fitur **Dynamic Grid Search Updater**:

- Mengambil data historis terkini langsung dari Live CBBI API
- Menjalankan ulang grid search (~1.29 juta kombinasi, selesai dalam hitungan detik via Numba)
- Menghasilkan `live_optimal_params.json` yang selalu sinkron dengan formula CBBI terkini

Ini memastikan simulator web selalu menyajikan parameter yang dikalibrasi terhadap "kebenaran saat ini", bukan snapshot statis dari periode riset.

---

## Narasi untuk Laporan PKL (Draft Bab Keterbatasan / Limitasi)

**Keterbatasan Penelitian — Dinamika Revisi Formula CBBI:**

Penelitian ini menggunakan dataset CBBI yang diambil pada periode [tanggal pengambilan data], yang merepresentasikan komposisi formula CBBI pada saat itu. Perlu diketahui bahwa indeks CBBI bersifat dinamis: penulis Colin Talks Crypto secara berkala memperbarui bobot dan komponen formula indeks, dan pembaruan tersebut berlaku retroaktif pada seluruh histori data yang disajikan melalui API resmi.

Konsekuensinya, parameter threshold dan alokasi aset yang diidentifikasi sebagai optimal dalam penelitian ini secara spesifik optimal terhadap distribusi sinyal versi formula CBBI yang digunakan saat penelitian. Apabila diterapkan langsung pada versi API terkini (yang mungkin telah mengalami revisi formula), performa aktual berpotensi berbeda.

Fenomena ini sejalan dengan konsep *index revision bias* dalam literatur ekonometrika, di mana revisi retroaktif pada suatu indeks dapat mempengaruhi validitas model yang dikalibrasi pada versi sebelumnya. Sebagai respons praktis, platform simulasi interaktif (Phase 4) dilengkapi fitur pembaruan parameter otomatis yang mengambil data terkini dari API dan menjalankan ulang proses optimasi, sehingga parameter yang disajikan kepada pengguna selalu relevan dengan kondisi formula CBBI terkini.

---

*Dokumen ini merupakan addendum resmi terhadap laporan riset PKL dan harus dibaca bersama `reports/phase3_results_overview.md` dan `reports/phase3_methodology_notes.md`.*
