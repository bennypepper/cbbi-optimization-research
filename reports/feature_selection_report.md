# Laporan Seleksi Fitur — Fase 2

**Dibuat:** 2026-04-09 20:30:57
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
| 1 | Trolololo (LogReg) | 0.6557 | 90d | -0.4261 | 0.0000 | ✅ |
| 2 | CBBI Confidence | 0.5779 | 14d | -0.2965 | 0.0000 | ✅ |
| 3 | Woobull NVT | 0.5753 | 14d | -0.2922 | 0.0000 | ✅ |
| 4 | Puell Multiple | 0.5722 | 14d | -0.2870 | 0.0000 | ✅ |
| 5 | 2Y MA Multiplier | 0.5606 | 14d | -0.2677 | 0.0000 | ✅ |
| 6 | MVRV Z-Score | 0.5595 | 14d | -0.2658 | 0.0000 | ✅ |
| 7 | Reserve Risk | 0.5586 | 14d | -0.2643 | 0.0000 | ✅ |
| 8 | RUPL | 0.5571 | 14d | -0.2618 | 0.0000 | ✅ |
| 9 | Pi Cycle Top | 0.5492 | 14d | -0.2487 | 0.0000 | ✅ |
| 10 | RHODL Ratio | 0.5082 | 14d | -0.1803 | 0.0000 | ✅ |


---

## Indikator Terpilih untuk Fase 3

Sebanyak **10 indikator** memenuhi kriteria seleksi:


### Trolololo (LogReg)

- **Composite Score:** 0.6557
- **Korelasi terkuat:** Spearman ρ = -0.4261 pada lag **90 hari** (p = 0.0000)
- **Arah korelasi:** negatif — ketika indikator tinggi (overbought), harga cenderung turun ke depan
- **Distribusi antar kondisi pasar:** Kruskal-Wallis H=1362.26, p=0.0000 (signifikan)


### CBBI Confidence

- **Composite Score:** 0.5779
- **Korelasi terkuat:** Spearman ρ = -0.2965 pada lag **14 hari** (p = 0.0000)
- **Arah korelasi:** negatif — ketika indikator tinggi (overbought), harga cenderung turun ke depan
- **Distribusi antar kondisi pasar:** Kruskal-Wallis H=2600.87, p=0.0000 (signifikan)


### Woobull NVT

- **Composite Score:** 0.5753
- **Korelasi terkuat:** Spearman ρ = -0.2922 pada lag **14 hari** (p = 0.0000)
- **Arah korelasi:** negatif — ketika indikator tinggi (overbought), harga cenderung turun ke depan
- **Distribusi antar kondisi pasar:** Kruskal-Wallis H=2484.52, p=0.0000 (signifikan)


### Puell Multiple

- **Composite Score:** 0.5722
- **Korelasi terkuat:** Spearman ρ = -0.2870 pada lag **14 hari** (p = 0.0000)
- **Arah korelasi:** negatif — ketika indikator tinggi (overbought), harga cenderung turun ke depan
- **Distribusi antar kondisi pasar:** Kruskal-Wallis H=2062.15, p=0.0000 (signifikan)


### 2Y MA Multiplier

- **Composite Score:** 0.5606
- **Korelasi terkuat:** Spearman ρ = -0.2677 pada lag **14 hari** (p = 0.0000)
- **Arah korelasi:** negatif — ketika indikator tinggi (overbought), harga cenderung turun ke depan
- **Distribusi antar kondisi pasar:** Kruskal-Wallis H=2545.77, p=0.0000 (signifikan)


### MVRV Z-Score

- **Composite Score:** 0.5595
- **Korelasi terkuat:** Spearman ρ = -0.2658 pada lag **14 hari** (p = 0.0000)
- **Arah korelasi:** negatif — ketika indikator tinggi (overbought), harga cenderung turun ke depan
- **Distribusi antar kondisi pasar:** Kruskal-Wallis H=2365.39, p=0.0000 (signifikan)


### Reserve Risk

- **Composite Score:** 0.5586
- **Korelasi terkuat:** Spearman ρ = -0.2643 pada lag **14 hari** (p = 0.0000)
- **Arah korelasi:** negatif — ketika indikator tinggi (overbought), harga cenderung turun ke depan
- **Distribusi antar kondisi pasar:** Kruskal-Wallis H=2135.95, p=0.0000 (signifikan)


### RUPL

- **Composite Score:** 0.5571
- **Korelasi terkuat:** Spearman ρ = -0.2618 pada lag **14 hari** (p = 0.0000)
- **Arah korelasi:** negatif — ketika indikator tinggi (overbought), harga cenderung turun ke depan
- **Distribusi antar kondisi pasar:** Kruskal-Wallis H=2275.59, p=0.0000 (signifikan)


### Pi Cycle Top

- **Composite Score:** 0.5492
- **Korelasi terkuat:** Spearman ρ = -0.2487 pada lag **14 hari** (p = 0.0000)
- **Arah korelasi:** negatif — ketika indikator tinggi (overbought), harga cenderung turun ke depan
- **Distribusi antar kondisi pasar:** Kruskal-Wallis H=2217.34, p=0.0000 (signifikan)


### RHODL Ratio

- **Composite Score:** 0.5082
- **Korelasi terkuat:** Spearman ρ = -0.1803 pada lag **14 hari** (p = 0.0000)
- **Arah korelasi:** negatif — ketika indikator tinggi (overbought), harga cenderung turun ke depan
- **Distribusi antar kondisi pasar:** Kruskal-Wallis H=1956.99, p=0.0000 (signifikan)



---

## Implikasi untuk Fase 3

Indikator terpilih berikut akan dijadikan kandidat `signal_column` pada
mesin optimisasi Fase 3:

```json
[
  "trolololo",
  "cbbi_confidence",
  "woobull",
  "puell_multiple",
  "two_year_ma_mult",
  "mvrv_zscore",
  "reserve_risk",
  "rupl",
  "pi_cycle",
  "rhodl_ratio"
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
