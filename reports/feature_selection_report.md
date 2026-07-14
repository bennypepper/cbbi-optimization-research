# Laporan Seleksi Fitur — Fase 2

**Dibuat:** 2026-07-15 00:40:04
**Filter data:** In-Sample (2012-01-01 – 2020-12-31)
**Metode:** Korelasi Spearman × 5 lag window + Distribusi Kruskal-Wallis

---

## Ringkasan Metode

Fase 2 menganalisis **10 indikator CBBI** (termasuk Composite Confidence Score)
menggunakan dua pendekatan komplementer:

1. **Korelasi Spearman** — mengukur kekuatan dan arah hubungan rank antara setiap
   indikator dengan forward return Bitcoin pada 5 window waktu: 7, 14, 30, 60, 90 hari.
   Dipilih karena non-parametrik dan robust terhadap distribusi non-normal aset kripto.

2. **Distribusi per Kondisi Pasar** — membandingkan distribusi nilai indikator
   di 4 rezim pasar (*accumulation*, *neutral*, *distribution*, *euphoria*) menggunakan
   Kruskal-Wallis test untuk memverifikasi diskriminasi antar kondisi.

**Formula composite score:**
```
score = 0.6 × abs(max Spearman ρ) + 0.4 × (1 − normalized min p-value)
```

**Kriteria seleksi:** composite_score ≥ 0.4 DAN p_value < 0.05
pada minimal satu lag window. Minimum 3 indikator terpilih.

---

## Tabel Ranking Lengkap

| Rank | Indikator | Composite Score | Best Lag | Spearman ρ | p-value | Selected |
|---|---|---|---|---|---|---|
| 1 | Trolololo (LogReg) | 0.6819 | 90d | -0.4698 | 0.0000 | ✅ |
| 2 | Reserve Risk | 0.5062 | 90d | -0.1770 | 0.0000 | ✅ |
| 3 | RUPL | 0.4680 | 90d | +0.1133 | 0.0000 | ✅ |
| 4 | RHODL Ratio | 0.4601 | 90d | -0.1001 | 0.0000 | ✅ |
| 5 | Pi Cycle Top | 0.4598 | 90d | +0.0997 | 0.0000 | ✅ |
| 6 | MVRV Z-Score | 0.4509 | 90d | +0.0848 | 0.0000 | ✅ |
| 7 | CBBI Confidence | 0.4419 | 90d | -0.0700 | 0.0001 | ✅ |
| 8 | Puell Multiple | 0.4418 | 7d | +0.0697 | 0.0001 | ✅ |
| 9 | Woobull NVT | 0.4301 | 90d | -0.0523 | 0.0031 | ✅ |
| 10 | 2Y MA Multiplier | 0.4264 | 7d | +0.0481 | 0.0059 | ✅ |


---

## Indikator Terpilih untuk Fase 3

Sebanyak **10 indikator** memenuhi kriteria seleksi:


### Trolololo (LogReg)

- **Composite Score:** 0.6819
- **Korelasi terkuat:** Spearman ρ = -0.4698 pada lag **90 hari** (p = 0.0000)
- **Arah korelasi:** negatif — ketika indikator tinggi (overbought), harga cenderung turun ke depan
- **Distribusi antar kondisi pasar:** Kruskal-Wallis H=1314.55, p=0.0000 (signifikan)


### Reserve Risk

- **Composite Score:** 0.5062
- **Korelasi terkuat:** Spearman ρ = -0.1770 pada lag **90 hari** (p = 0.0000)
- **Arah korelasi:** negatif — ketika indikator tinggi (overbought), harga cenderung turun ke depan
- **Distribusi antar kondisi pasar:** Kruskal-Wallis H=2135.95, p=0.0000 (signifikan)


### RUPL

- **Composite Score:** 0.4680
- **Korelasi terkuat:** Spearman ρ = +0.1133 pada lag **90 hari** (p = 0.0000)
- **Arah korelasi:** positif — ketika indikator tinggi, harga cenderung naik ke depan
- **Distribusi antar kondisi pasar:** Kruskal-Wallis H=2275.59, p=0.0000 (signifikan)


### RHODL Ratio

- **Composite Score:** 0.4601
- **Korelasi terkuat:** Spearman ρ = -0.1001 pada lag **90 hari** (p = 0.0000)
- **Arah korelasi:** negatif — ketika indikator tinggi (overbought), harga cenderung turun ke depan
- **Distribusi antar kondisi pasar:** Kruskal-Wallis H=1956.99, p=0.0000 (signifikan)


### Pi Cycle Top

- **Composite Score:** 0.4598
- **Korelasi terkuat:** Spearman ρ = +0.0997 pada lag **90 hari** (p = 0.0000)
- **Arah korelasi:** positif — ketika indikator tinggi, harga cenderung naik ke depan
- **Distribusi antar kondisi pasar:** Kruskal-Wallis H=2217.34, p=0.0000 (signifikan)


### MVRV Z-Score

- **Composite Score:** 0.4509
- **Korelasi terkuat:** Spearman ρ = +0.0848 pada lag **90 hari** (p = 0.0000)
- **Arah korelasi:** positif — ketika indikator tinggi, harga cenderung naik ke depan
- **Distribusi antar kondisi pasar:** Kruskal-Wallis H=2365.39, p=0.0000 (signifikan)


### CBBI Confidence

- **Composite Score:** 0.4419
- **Korelasi terkuat:** Spearman ρ = -0.0700 pada lag **90 hari** (p = 0.0001)
- **Arah korelasi:** negatif — ketika indikator tinggi (overbought), harga cenderung turun ke depan
- **Distribusi antar kondisi pasar:** Kruskal-Wallis H=2600.87, p=0.0000 (signifikan)


### Puell Multiple

- **Composite Score:** 0.4418
- **Korelasi terkuat:** Spearman ρ = +0.0697 pada lag **7 hari** (p = 0.0001)
- **Arah korelasi:** positif — ketika indikator tinggi, harga cenderung naik ke depan
- **Distribusi antar kondisi pasar:** Kruskal-Wallis H=2062.15, p=0.0000 (signifikan)


### Woobull NVT

- **Composite Score:** 0.4301
- **Korelasi terkuat:** Spearman ρ = -0.0523 pada lag **90 hari** (p = 0.0031)
- **Arah korelasi:** negatif — ketika indikator tinggi (overbought), harga cenderung turun ke depan
- **Distribusi antar kondisi pasar:** Kruskal-Wallis H=2484.52, p=0.0000 (signifikan)


### 2Y MA Multiplier

- **Composite Score:** 0.4264
- **Korelasi terkuat:** Spearman ρ = +0.0481 pada lag **7 hari** (p = 0.0059)
- **Arah korelasi:** positif — ketika indikator tinggi, harga cenderung naik ke depan
- **Distribusi antar kondisi pasar:** Kruskal-Wallis H=2545.77, p=0.0000 (signifikan)



---

## Implikasi untuk Fase 3

Indikator terpilih berikut akan dijadikan kandidat `signal_column` pada
mesin optimisasi Fase 3:

```json
[
  "trolololo",
  "reserve_risk",
  "rupl",
  "rhodl_ratio",
  "pi_cycle",
  "mvrv_zscore",
  "cbbi_confidence",
  "puell_multiple",
  "woobull",
  "two_year_ma_mult"
]
```

> **Catatan:** `cbbi_confidence` (Composite CBBI Score resmi) tetap menjadi
> `signal_column` **default** dan utama pada mesin optimisasi Fase 3.
> Indikator individual terpilih di atas tersedia sebagai opsi eksploratif.

---

## Referensi Visualisasi

- `charts/spearman_heatmap.png` — Heatmap korelasi Spearman semua indikator × lag
- `charts/distribution_boxplot.png` — Distribusi nilai per kondisi pasar (top-6)
- `charts/indicator_ranking_bar.png` — Bar chart composite score semua indikator
- `charts/scatter_top_indicators.png` — Scatter top indikator vs forward return 30/60/90d

---

*Dokumen ini di-generate secara otomatis oleh `src/analysis/feature_selector.py`*
