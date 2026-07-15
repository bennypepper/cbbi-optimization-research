"""
src/analysis/feature_selector.py
=================================
Fase 2 — Seleksi Indikator & Analisis Statistik

Tujuan: Mengidentifikasi indikator CBBI dengan korelasi statistik paling kuat
terhadap pergerakan harga Bitcoin, sebagai fondasi sinyal pada Fase 3.

PENTING: Seluruh analisis dijalankan HANYA pada data In-Sample (2012–2020)
         untuk mencegah data leakage ke proses optimisasi Fase 3.

Output:
  analysis/spearman_results.csv         — korelasi 10 indikator × 5 lag
  analysis/distribution_stats.json      — statistik distribusi per kondisi pasar
  analysis/indicator_ranking.csv        — pemeringkatan + flag selected
  analysis/selected_indicators.json     — list indikator terpilih → input Fase 3
  reports/feature_selection_report.md   — narasi hasil analisis
  reports/charts/spearman_heatmap.png
  reports/charts/distribution_boxplot.png
  reports/charts/indicator_ranking_bar.png
  reports/charts/scatter_top_indicators.png

Referensi PRD: §3.2 (Spesifikasi Analisis), §3.3 (Output), §3.4 (Kriteria Keberhasilan)
Referensi Riset: §Metodologi §3 (Seleksi Fitur dan Analisis Signifikansi Statistik)
"""

import json
import logging
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # non-interactive backend untuk server/script
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT_DIR      = Path(__file__).resolve().parents[2]
PARQUET_PATH  = ROOT_DIR / "data" / "processed" / "master_dataset.parquet"
ANALYSIS_DIR  = ROOT_DIR / "analysis"
REPORTS_DIR   = ROOT_DIR / "reports"
CHARTS_DIR    = REPORTS_DIR / "charts"

# ── Konstanta analisis ────────────────────────────────────────────────────────
LAG_WINDOWS = [7, 14, 30, 60, 90]   # hari ke depan untuk forward return

INDICATOR_COLS = [
    "cbbi_confidence",
    "pi_cycle",
    "rupl",
    "rhodl_ratio",
    "puell_multiple",
    "two_year_ma_mult",
    "trolololo",
    "mvrv_zscore",
    "reserve_risk",
    "woobull",
]

# Label tampilan untuk setiap indikator
INDICATOR_LABELS = {
    "cbbi_confidence":  "Composite Index",
    "pi_cycle":         "Pi Cycle Top",
    "rupl":             "RUPL",
    "rhodl_ratio":      "RHODL Ratio",
    "puell_multiple":   "Puell Multiple",
    "two_year_ma_mult": "2Y MA Multiplier",
    "trolololo":        "Logarithmic Regression",
    "mvrv_zscore":      "MVRV Z-Score",
    "reserve_risk":     "Reserve Risk",
    "woobull":          "Woobull NVT",
}

# Kondisi pasar berdasarkan cbbi_confidence (sesuai PRD §3.2.2)
MARKET_CONDITIONS = {
    "accumulation": (0,   25),
    "neutral":      (25,  60),
    "distribution": (60,  80),
    "euphoria":     (80, 100),
}

# Threshold seleksi indikator (sesuai PRD §3.2.3)
SELECTION_COMPOSITE_THRESHOLD = 0.4
SELECTION_PVALUE_THRESHOLD    = 0.05
MIN_SELECTED_INDICATORS       = 3


# ─────────────────────────────────────────────────────────────────────────────
# 1. Forward Return
# ─────────────────────────────────────────────────────────────────────────────

def compute_forward_returns(price_series: pd.Series, lag: int) -> pd.Series:
    """
    Menghitung forward return: (P[t+lag] - P[t]) / P[t]

    ⚠️  CRITICAL: Hanya digunakan untuk analisis statistik Fase 2.
    TIDAK boleh digunakan dalam logika backtesting Fase 3.
    Penggunaan forward return di Fase 3 merupakan bentuk lookahead bias.

    Parameters
    ----------
    price_series : pd.Series — harga harian (btc_close)
    lag          : jumlah hari ke depan

    Returns
    -------
    pd.Series — forward return per hari, NaN untuk lag hari terakhir
    """
    return price_series.pct_change(lag).shift(-lag)


# ─────────────────────────────────────────────────────────────────────────────
# 2. Spearman Correlation Analysis
# ─────────────────────────────────────────────────────────────────────────────

def spearman_correlation_analysis(
    df: pd.DataFrame,
    phase_filter: str = "in_sample",
) -> pd.DataFrame:
    """
    Analisis korelasi Spearman antara setiap indikator CBBI dengan
    forward return Bitcoin pada 5 lag window.

    Korelasi Spearman dipilih karena bersifat non-parametrik dan lebih
    robust terhadap distribusi non-normal yang umum pada data aset kripto.
    (Referensi: PRD §3.2.1, Riset §Metodologi §3)

    Parameters
    ----------
    df           : DataFrame master dari Fase 1
    phase_filter : Filter fase yang digunakan ('in_sample' wajib)

    Returns
    -------
    pd.DataFrame dengan kolom:
      ['indicator', 'lag_days', 'spearman_rho', 'p_value', 'significant']
    """
    logger.info("Menjalankan analisis korelasi Spearman (phase=%s)...", phase_filter)

    # Filter fase
    df_filtered = df[df["phase"] == phase_filter].copy()
    max_date = df_filtered.index.max()
    logger.info(
        "  Data: %d baris | %s → %s",
        len(df_filtered), df_filtered.index.min().date(), max_date.date(),
    )

    # Guard: pastikan hanya memakai data IS
    if phase_filter == "in_sample" and max_date > pd.Timestamp("2020-12-31"):
        raise ValueError(
            f"[LOOKAHEAD] Data In-Sample berakhir di {max_date.date()} "
            "— melebihi 2020-12-31. Hentikan proses."
        )

    results = []
    price_series = df_filtered["btc_close"].astype(float)

    for lag in LAG_WINDOWS:
        fwd_ret = compute_forward_returns(price_series, lag)

        for col in INDICATOR_COLS:
            indicator_vals = df_filtered[col]

            # Buang baris dengan NaN (forward return hari-hari terakhir)
            mask = indicator_vals.notna() & fwd_ret.notna()
            x = indicator_vals[mask]
            y = fwd_ret[mask]

            if len(x) < 30:
                logger.warning(
                    "  Melewati %s lag=%d: hanya %d sampel valid (min 30)",
                    col, lag, len(x),
                )
                continue

            rho, pval = stats.spearmanr(x, y)
            results.append({
                "indicator":    col,
                "lag_days":     lag,
                "spearman_rho": round(float(rho), 6),
                "p_value":      round(float(pval), 6),
                "significant":  pval < SELECTION_PVALUE_THRESHOLD,
                "n_samples":    len(x),
            })

    corr_df = pd.DataFrame(results)
    logger.info("  Analisis Spearman selesai: %d pasang indikator×lag", len(corr_df))
    return corr_df


# ─────────────────────────────────────────────────────────────────────────────
# 3. Distribusi per Kondisi Pasar
# ─────────────────────────────────────────────────────────────────────────────

def distribution_analysis(
    df: pd.DataFrame,
    phase_filter: str = "in_sample",
) -> dict:
    """
    Analisis distribusi nilai setiap indikator pada kondisi pasar berbeda,
    dibedakan berdasarkan nilai cbbi_confidence.

    Kondisi pasar (sesuai PRD §3.2.2):
      accumulation : cbbi_confidence  0 – 25
      neutral      : cbbi_confidence 25 – 60
      distribution : cbbi_confidence 60 – 80
      euphoria     : cbbi_confidence 80 – 100

    Kruskal-Wallis test digunakan untuk menguji perbedaan distribusi
    antar kondisi (non-parametrik, tidak mengasumsikan normalitas).

    Returns
    -------
    dict: {
        indicator_name: {
            "conditions": {condition: {mean, median, std, iqr, n}},
            "kruskal_wallis": {H_stat, p_value, significant}
        }
    }
    """
    logger.info("Menjalankan analisis distribusi per kondisi pasar (phase=%s)...", phase_filter)

    df_filtered = df[df["phase"] == phase_filter].copy()

    # Assign label kondisi pasar ke setiap baris
    def _assign_condition(val: float) -> str:
        for cond, (lo, hi) in MARKET_CONDITIONS.items():
            if lo <= val < hi:
                return cond
        if val >= 80:
            return "euphoria"
        return "unknown"

    df_filtered["market_condition"] = df_filtered["cbbi_confidence"].apply(_assign_condition)

    # Log distribusi kondisi pasar
    cond_counts = df_filtered["market_condition"].value_counts()
    logger.info("  Distribusi kondisi pasar pada data IS:")
    for cond, cnt in cond_counts.items():
        logger.info("    %-14s: %d baris (%.1f%%)", cond, cnt, 100 * cnt / len(df_filtered))

    results = {}

    for col in INDICATOR_COLS:
        col_results = {"conditions": {}, "kruskal_wallis": {}}
        groups = []

        for cond in MARKET_CONDITIONS:
            mask = df_filtered["market_condition"] == cond
            vals = df_filtered.loc[mask, col].dropna()
            n = len(vals)

            if n > 0:
                q1, q3 = np.percentile(vals, [25, 75])
                col_results["conditions"][cond] = {
                    "mean":   round(float(vals.mean()), 4),
                    "median": round(float(vals.median()), 4),
                    "std":    round(float(vals.std()), 4),
                    "iqr":    round(float(q3 - q1), 4),
                    "min":    round(float(vals.min()), 4),
                    "max":    round(float(vals.max()), 4),
                    "n":      int(n),
                }
                if n >= 5:
                    groups.append(vals.values)
            else:
                col_results["conditions"][cond] = {"n": 0}

        # Kruskal-Wallis test (memerlukan min 2 grup dengan data)
        valid_groups = [g for g in groups if len(g) >= 5]
        if len(valid_groups) >= 2:
            H, p = stats.kruskal(*valid_groups)
            col_results["kruskal_wallis"] = {
                "H_stat":     round(float(H), 4),
                "p_value":    round(float(p), 6),
                "significant": bool(p < SELECTION_PVALUE_THRESHOLD),
            }
        else:
            col_results["kruskal_wallis"] = {
                "H_stat": None, "p_value": None, "significant": False,
            }

        results[col] = col_results

    logger.info("  Analisis distribusi selesai untuk %d indikator", len(results))
    return results


# ─────────────────────────────────────────────────────────────────────────────
# 4. Pemeringkatan dan Seleksi Indikator
# ─────────────────────────────────────────────────────────────────────────────

def rank_indicators(
    correlation_df: pd.DataFrame,
    distribution_results: dict,
) -> pd.DataFrame:
    """
    Pemeringkatan indikator berdasarkan composite score.

    Formula (sesuai PRD §3.2.3):
      score = 0.6 × abs(max_spearman_rho) + 0.4 × (1 − normalized_min_p_value)

    Normalisasi p-value: p-value dinormalisasi ke [0, 1] menggunakan
    min-max dari semua p-value dalam analisis.

    Kriteria seleksi:
      composite_score >= 0.4 DAN p_value < 0.05 pada minimal satu lag window.
      Minimum 3 indikator terpilih (fallback: top-3 jika kurang dari 3 memenuhi kriteria).

    Returns
    -------
    pd.DataFrame terurut descending dengan kolom:
      ['indicator', 'label', 'composite_score', 'best_lag_days',
       'best_spearman_rho', 'best_p_value', 'kruskal_significant',
       'n_significant_lags', 'selected']
    """
    logger.info("Menghitung composite score dan ranking indikator...")

    # Normalisasi p-value secara global
    all_pvals = correlation_df["p_value"].values
    pval_min, pval_max = all_pvals.min(), all_pvals.max()
    pval_range = pval_max - pval_min if pval_max > pval_min else 1.0

    rows = []
    for col in INDICATOR_COLS:
        sub = correlation_df[correlation_df["indicator"] == col]
        if sub.empty:
            continue

        # Best lag: lag dengan |rho| tertinggi
        best_idx   = sub["spearman_rho"].abs().idxmax()
        best_row   = sub.loc[best_idx]
        max_rho    = float(best_row["spearman_rho"].item() if hasattr(best_row["spearman_rho"], "item") else best_row["spearman_rho"])
        min_pval   = float(sub["p_value"].min())
        best_lag   = int(best_row["lag_days"])

        # Composite score
        norm_pval      = (min_pval - pval_min) / pval_range
        composite_score = 0.6 * abs(max_rho) + 0.4 * (1 - norm_pval)

        # Kruskal-Wallis
        kw_sig = distribution_results.get(col, {}).get(
            "kruskal_wallis", {}
        ).get("significant", False)

        # Jumlah lag yang signifikan
        n_sig = int(sub["significant"].sum())

        rows.append({
            "indicator":           col,
            "label":               INDICATOR_LABELS.get(col, col),
            "composite_score":     round(composite_score, 4),
            "best_lag_days":       best_lag,
            "best_spearman_rho":   round(max_rho, 4),
            "best_p_value":        round(min_pval, 6),
            "kruskal_significant": bool(kw_sig),
            "n_significant_lags":  n_sig,
            "selected":            False,  # akan diisi di bawah
        })

    ranking_df = pd.DataFrame(rows).sort_values(
        "composite_score", ascending=False
    ).reset_index(drop=True)

    # Tentukan yang selected
    criteria_mask = (
        (ranking_df["composite_score"] >= SELECTION_COMPOSITE_THRESHOLD) &
        (ranking_df["best_p_value"] < SELECTION_PVALUE_THRESHOLD)
    )
    ranking_df.loc[criteria_mask, "selected"] = True

    n_selected = criteria_mask.sum()
    logger.info("  Indikator memenuhi kriteria seleksi: %d", n_selected)

    # Fallback: pastikan minimal 3 terpilih
    if n_selected < MIN_SELECTED_INDICATORS:
        logger.warning(
            "  Hanya %d indikator memenuhi kriteria — fallback: ambil top-%d",
            n_selected, MIN_SELECTED_INDICATORS,
        )
        ranking_df.iloc[:MIN_SELECTED_INDICATORS, ranking_df.columns.get_loc("selected")] = True

    logger.info("  Total indikator terpilih: %d", ranking_df["selected"].sum())
    for _, row in ranking_df.iterrows():
        status = "✓ SELECTED" if row["selected"] else "  —"
        logger.info(
            "  %s %-22s score=%.4f rho=%.4f p=%.4f lag=%dh",
            status, row["label"], row["composite_score"],
            row["best_spearman_rho"], row["best_p_value"], row["best_lag_days"],
        )

    return ranking_df


# ─────────────────────────────────────────────────────────────────────────────
# 5. Visualisasi
# ─────────────────────────────────────────────────────────────────────────────

def generate_visualizations(
    df_is: pd.DataFrame,
    corr_df: pd.DataFrame,
    dist_results: dict,
    ranking_df: pd.DataFrame,
) -> None:
    """
    Menghasilkan 4 visualisasi untuk laporan Fase 2.

    Plot 1: Heatmap korelasi Spearman (indikator × lag window)
    Plot 2: Box plot distribusi nilai per kondisi pasar
    Plot 3: Bar chart composite score dengan highlight selected
    Plot 4: Scatter plot top-3 indikator vs forward return 30/60/90 hari
    """
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid")
    colors = sns.color_palette("husl", 4)

    # ── Plot 1: Heatmap Spearman ──────────────────────────────────────────────
    logger.info("  Membuat Plot 1: Heatmap Spearman...")
    pivot = corr_df.pivot(index="indicator", columns="lag_days", values="spearman_rho")
    pivot.index = [INDICATOR_LABELS.get(i, i) for i in pivot.index]
    pivot.columns = [f"{c}d" for c in pivot.columns]

    fig, ax = plt.subplots(figsize=(10, 7))
    sns.heatmap(
        pivot, annot=True, fmt=".3f", cmap="RdYlGn",
        center=0, vmin=-1, vmax=1, linewidths=0.5,
        annot_kws={"size": 9}, ax=ax,
    )
    ax.set_title(
        "Korelasi Spearman: Indikator On-Chain vs Forward Return BTC\n"
        "(Data In-Sample 2012–2020)",
        fontsize=13, fontweight="bold", pad=15,
    )
    ax.set_xlabel("Lag Window", fontsize=11)
    ax.set_ylabel("Indikator On-Chain", fontsize=11)
    plt.tight_layout()
    out1 = CHARTS_DIR / "spearman_heatmap.png"
    fig.savefig(out1, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("    Tersimpan: %s", out1)

    # ── Plot 2: Box Plot Distribusi ───────────────────────────────────────────
    logger.info("  Membuat Plot 2: Box Plot Distribusi...")
    top6 = ranking_df.head(6)["indicator"].tolist()
    n_cols = 3
    n_rows = 2

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 8))
    axes = axes.flatten()

    cond_order = ["accumulation", "neutral", "distribution", "euphoria"]
    cond_colors = dict(zip(cond_order, colors))

    df_plot = df_is.copy()
    def _assign_cond(v):
        for c, (lo, hi) in MARKET_CONDITIONS.items():
            if lo <= v < hi:
                return c
        return "euphoria" if v >= 80 else "unknown"
    df_plot["market_condition"] = df_plot["cbbi_confidence"].apply(_assign_cond)

    for idx, col in enumerate(top6):
        ax = axes[idx]
        data_by_cond = [
            df_plot.loc[df_plot["market_condition"] == cond, col].dropna().values
            for cond in cond_order
        ]
        bp = ax.boxplot(
            data_by_cond, tick_labels=[c.capitalize() for c in cond_order],
            patch_artist=True,
            medianprops={"color": "black", "linewidth": 2},
        )
        for patch, cond in zip(bp["boxes"], cond_order):
            patch.set_facecolor(cond_colors[cond])
            patch.set_alpha(0.7)

        label = INDICATOR_LABELS.get(col, col)
        row_in_ranking = ranking_df[ranking_df["indicator"] == col]
        sel = bool(row_in_ranking["selected"].values[0]) if not row_in_ranking.empty else False
        title_suffix = " [SELECTED]" if sel else ""
        ax.set_title(f"{label}{title_suffix}", fontsize=10, fontweight="bold")
        ax.set_ylabel("Nilai [0–100]", fontsize=9)
        ax.tick_params(labelsize=8)

    # Sembunyikan subplot kosong jika ada
    for i in range(len(top6), len(axes)):
        axes[i].axis("off")

    patches = [mpatches.Patch(color=cond_colors[c], alpha=0.7, label=c.capitalize())
               for c in cond_order]
    fig.legend(handles=patches, loc="lower center", ncol=4, fontsize=10, title="Kondisi Pasar")
    fig.suptitle(
        "Distribusi Nilai Indikator On-Chain per Kondisi Pasar\n"
        "(Top-6 Indikator | Data In-Sample 2012–2020)",
        fontsize=13, fontweight="bold", y=1.01,
    )
    plt.tight_layout()
    out2 = CHARTS_DIR / "distribution_boxplot.png"
    fig.savefig(out2, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("    Tersimpan: %s", out2)

    # ── Plot 3: Bar Chart Ranking ─────────────────────────────────────────────
    logger.info("  Membuat Plot 3: Bar Chart Composite Score...")
    fig, ax = plt.subplots(figsize=(10, 6))

    bar_colors = [
        "#2ecc71" if sel else "#95a5a6"
        for sel in ranking_df["selected"]
    ]
    bars = ax.barh(
        ranking_df["label"][::-1],
        ranking_df["composite_score"][::-1],
        color=bar_colors[::-1], edgecolor="white", linewidth=0.5,
    )
    ax.axvline(SELECTION_COMPOSITE_THRESHOLD, color="red", linestyle="--",
               linewidth=1.5, label=f"Threshold seleksi ({SELECTION_COMPOSITE_THRESHOLD})")
    ax.set_xlabel("Composite Score", fontsize=11)
    ax.set_title(
        "Pemeringkatan Indikator On-Chain: Composite Score\n"
        "(0.6 × |max Spearman ρ| + 0.4 × (1 − norm p-value))",
        fontsize=12, fontweight="bold",
    )
    ax.legend(fontsize=10)

    # Annotasi nilai score
    for bar, score in zip(bars[::-1], ranking_df["composite_score"]):
        ax.text(
            score + 0.005, bar.get_y() + bar.get_height() / 2,
            f"{score:.4f}", va="center", ha="left", fontsize=9,
        )

    sel_patch  = mpatches.Patch(color="#2ecc71", label="Terpilih")
    nosel_patch = mpatches.Patch(color="#95a5a6", label="Tidak terpilih")
    ax.legend(handles=[sel_patch, nosel_patch], loc="lower right", fontsize=9)

    plt.tight_layout()
    out3 = CHARTS_DIR / "indicator_ranking_bar.png"
    fig.savefig(out3, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("    Tersimpan: %s", out3)

    # ── Plot 4: Scatter Top-3 vs Forward Return ───────────────────────────────
    logger.info("  Membuat Plot 4: Scatter Top-3 Indikator vs Forward Return...")
    top3 = ranking_df[ranking_df["selected"]].head(3)["indicator"].tolist()
    if not top3:
        top3 = ranking_df.head(3)["indicator"].tolist()

    price_series = df_is["btc_close"].astype(float)
    scatter_lags = [30, 60, 90]

    fig, axes = plt.subplots(len(top3), len(scatter_lags), figsize=(14, 4 * len(top3)))
    if len(top3) == 1:
        axes = np.array([axes])

    for ri, col in enumerate(top3):
        for ci, lag in enumerate(scatter_lags):
            ax = axes[ri][ci]
            fwd = compute_forward_returns(price_series, lag)
            mask = df_is[col].notna() & fwd.notna()
            x = df_is.loc[mask, col]
            y = fwd[mask] * 100  # persen

            ax.scatter(x, y, alpha=0.3, s=12, color=sns.color_palette("tab10")[ri])

            # Regression line
            m, b, r, p, _ = stats.linregress(x, y)
            xline = np.linspace(x.min(), x.max(), 100)
            ax.plot(xline, m * xline + b, color="red", linewidth=1.5,
                    label=f"r={r:.3f}, p={p:.3f}")

            label = INDICATOR_LABELS.get(col, col)
            ax.set_title(f"{label} vs {lag}d Return", fontsize=9, fontweight="bold")
            ax.set_xlabel(label, fontsize=8)
            ax.set_ylabel(f"Forward Return {lag}d (%)", fontsize=8)
            ax.legend(fontsize=7)
            ax.tick_params(labelsize=7)

    fig.suptitle(
        "Top Indikator CBBI vs Forward Return BTC (30/60/90 hari)\n"
        "(Data In-Sample 2012–2020)",
        fontsize=12, fontweight="bold",
    )
    plt.tight_layout()
    out4 = CHARTS_DIR / "scatter_top_indicators.png"
    fig.savefig(out4, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("    Tersimpan: %s", out4)

    logger.info("  ✓ Semua visualisasi berhasil disimpan ke: %s", CHARTS_DIR)


# ─────────────────────────────────────────────────────────────────────────────
# 6. Laporan Naratif
# ─────────────────────────────────────────────────────────────────────────────

def generate_report(
    ranking_df: pd.DataFrame,
    corr_df: pd.DataFrame,
    dist_results: dict,
    selected_indicators: list,
) -> None:
    """
    Menulis laporan naratif feature_selection_report.md secara otomatis.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    n_is_rows = len(corr_df["n_samples"].unique())

    # Tabel ranking
    tabel_ranking = "| Rank | Indikator | Composite Score | Best Lag | Spearman ρ | p-value | Selected |\n"
    tabel_ranking += "|---|---|---|---|---|---|---|\n"
    for rank, (_, row) in enumerate(ranking_df.iterrows(), 1):
        sel_icon = "✅" if row["selected"] else "—"
        tabel_ranking += (
            f"| {rank} | {row['label']} | {row['composite_score']:.4f} "
            f"| {row['best_lag_days']}d | {row['best_spearman_rho']:+.4f} "
            f"| {row['best_p_value']:.4f} | {sel_icon} |\n"
        )

    # Narasi indikator terpilih
    narasi_selected = ""
    for col in selected_indicators:
        row = ranking_df[ranking_df["indicator"] == col].iloc[0]
        label = row["label"]
        rho   = row["best_spearman_rho"]
        lag   = row["best_lag_days"]
        pval  = row["best_p_value"]
        score = row["composite_score"]

        # Arah korelasi
        arah = "positif" if rho > 0 else "negatif"
        interpretasi = (
            "ketika indikator tinggi, harga cenderung naik ke depan"
            if rho > 0
            else "ketika indikator tinggi (overbought), harga cenderung turun ke depan"
        )

        # Kruskal-Wallis
        kw = dist_results.get(col, {}).get("kruskal_wallis", {})
        kw_text = (
            f"Kruskal-Wallis H={kw.get('H_stat', 'N/A'):.2f}, p={kw.get('p_value', 'N/A'):.4f} "
            f"({'signifikan' if kw.get('significant') else 'tidak signifikan'})"
            if kw.get("H_stat") is not None
            else "Kruskal-Wallis: tidak dapat dihitung (data tidak cukup)"
        )

        narasi_selected += f"""
### {label}

- **Composite Score:** {score:.4f}
- **Korelasi terkuat:** Spearman ρ = {rho:+.4f} pada lag **{lag} hari** (p = {pval:.4f})
- **Arah korelasi:** {arah} — {interpretasi}
- **Distribusi antar kondisi pasar:** {kw_text}

"""

    report_content = f"""# Laporan Seleksi Fitur — Fase 2

**Dibuat:** {now}
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

**Kriteria seleksi:** composite_score ≥ {SELECTION_COMPOSITE_THRESHOLD} DAN p_value < {SELECTION_PVALUE_THRESHOLD}
pada minimal satu lag window. Minimum {MIN_SELECTED_INDICATORS} indikator terpilih.

---

## Tabel Ranking Lengkap

{tabel_ranking}

---

## Indikator Terpilih untuk Fase 3

Sebanyak **{len(selected_indicators)} indikator** memenuhi kriteria seleksi:

{narasi_selected}

---

## Implikasi untuk Fase 3

Indikator terpilih berikut akan dijadikan kandidat `signal_column` pada
mesin optimisasi Fase 3:

```json
{json.dumps(selected_indicators, indent=2)}
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
"""

    report_path = REPORTS_DIR / "feature_selection_report.md"
    report_path.write_text(report_content, encoding="utf-8")
    logger.info("  Laporan tersimpan ke: %s", report_path)


# ─────────────────────────────────────────────────────────────────────────────
# 7. Orkestrasi Utama
# ─────────────────────────────────────────────────────────────────────────────

def run_feature_selection() -> dict:
    """
    Fungsi orkestrasi utama Fase 2.

    Urutan:
      1. Load dataset master dari Fase 1
      2. Filter data In-Sample
      3. Analisis Spearman (10 indikator × 5 lag)
      4. Analisis distribusi per kondisi pasar
      5. Ranking & seleksi indikator
      6. Simpan semua output file
      7. Generate visualisasi
      8. Generate laporan naratif

    Returns
    -------
    dict dengan key: 'selected_indicators', 'ranking_df', 'corr_df'
    """
    logger.info("=" * 60)
    logger.info("FASE 2: Seleksi Indikator & Analisis Statistik — MULAI")
    logger.info("=" * 60)

    # ── Step 1: Load data ─────────────────────────────────────────────────────
    logger.info("\n[Step 1/7] Load dataset master dari Fase 1")
    if not PARQUET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset master tidak ditemukan: {PARQUET_PATH}\n"
            "Jalankan Fase 1 terlebih dahulu: python -m src.data.preprocessor"
        )
    df = pd.read_parquet(PARQUET_PATH)
    logger.info("  Dataset dimuat: %d baris | kolom: %s", len(df), df.columns.tolist())

    # Filter hanya In-Sample
    df_is = df[df["phase"] == "in_sample"].copy()
    logger.info(
        "  Data In-Sample: %d baris | %s → %s",
        len(df_is), df_is.index.min().date(), df_is.index.max().date(),
    )

    # ── Step 2: Spearman ─────────────────────────────────────────────────────
    logger.info("\n[Step 2/7] Analisis Korelasi Spearman")
    corr_df = spearman_correlation_analysis(df_is, phase_filter="in_sample")

    # ── Step 3: Distribusi ────────────────────────────────────────────────────
    logger.info("\n[Step 3/7] Analisis Distribusi per Kondisi Pasar")
    dist_results = distribution_analysis(df_is, phase_filter="in_sample")

    # ── Step 4: Ranking ───────────────────────────────────────────────────────
    logger.info("\n[Step 4/7] Pemeringkatan dan Seleksi Indikator")
    ranking_df = rank_indicators(corr_df, dist_results)
    selected_indicators = ranking_df[ranking_df["selected"]]["indicator"].tolist()

    # ── Step 5: Simpan output CSV / JSON ─────────────────────────────────────
    logger.info("\n[Step 5/7] Menyimpan output analisis")
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    # Spearman results
    spearman_out = ANALYSIS_DIR / "spearman_results.csv"
    corr_df.to_csv(spearman_out, index=False)
    logger.info("  ✓ %s (%d baris)", spearman_out, len(corr_df))

    # Distribution stats
    dist_out = ANALYSIS_DIR / "distribution_stats.json"
    dist_out.write_text(json.dumps(dist_results, indent=2), encoding="utf-8")
    logger.info("  ✓ %s", dist_out)

    # Indicator ranking
    ranking_out = ANALYSIS_DIR / "indicator_ranking.csv"
    ranking_df.to_csv(ranking_out, index=False)
    logger.info("  ✓ %s (%d baris)", ranking_out, len(ranking_df))

    # Selected indicators
    selected_out = ANALYSIS_DIR / "selected_indicators.json"
    selected_payload = {
        "generated_at": datetime.now().isoformat(),
        "phase_used":   "in_sample",
        "date_range":   {
            "start": str(df_is.index.min().date()),
            "end":   str(df_is.index.max().date()),
        },
        "selection_criteria": {
            "composite_score_min": SELECTION_COMPOSITE_THRESHOLD,
            "p_value_max":         SELECTION_PVALUE_THRESHOLD,
            "min_indicators":      MIN_SELECTED_INDICATORS,
        },
        "selected_indicators":  selected_indicators,
        "default_signal_column": "cbbi_confidence",
        "ranking": ranking_df[
            ["indicator", "label", "composite_score",
             "best_lag_days", "best_spearman_rho", "best_p_value", "selected"]
        ].to_dict(orient="records"),
    }
    selected_out.write_text(json.dumps(selected_payload, indent=2), encoding="utf-8")
    logger.info("  ✓ %s — indikator terpilih: %s", selected_out, selected_indicators)

    # ── Step 6: Visualisasi ───────────────────────────────────────────────────
    logger.info("\n[Step 6/7] Membuat visualisasi")
    generate_visualizations(df_is, corr_df, dist_results, ranking_df)

    # ── Step 7: Laporan ───────────────────────────────────────────────────────
    logger.info("\n[Step 7/7] Membuat laporan naratif")
    generate_report(ranking_df, corr_df, dist_results, selected_indicators)

    # ── Ringkasan akhir ────────────────────────────────────────────────────────
    logger.info("\n" + "=" * 60)
    logger.info("FASE 2: Seleksi Indikator — SELESAI")
    logger.info("=" * 60)
    logger.info("  Indikator dianalisis  : %d", len(INDICATOR_COLS))
    logger.info("  Lag window            : %s", LAG_WINDOWS)
    logger.info("  Indikator terpilih    : %d — %s", len(selected_indicators), selected_indicators)
    logger.info("  Output:")
    logger.info("    analysis/spearman_results.csv")
    logger.info("    analysis/distribution_stats.json")
    logger.info("    analysis/indicator_ranking.csv")
    logger.info("    analysis/selected_indicators.json")
    logger.info("    reports/feature_selection_report.md")
    logger.info("    reports/charts/ (4 files)")
    logger.info("=" * 60)

    return {
        "selected_indicators": selected_indicators,
        "ranking_df":          ranking_df,
        "corr_df":             corr_df,
    }


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    result = run_feature_selection()
    print("\n=== HASIL SELEKSI INDIKATOR ===")
    print(f"Indikator terpilih ({len(result['selected_indicators'])}):")
    for ind in result["selected_indicators"]:
        label = INDICATOR_LABELS.get(ind, ind)
        row = result["ranking_df"][result["ranking_df"]["indicator"] == ind].iloc[0]
        print(f"  * {label:<25} score={row['composite_score']:.4f} rho={row['best_spearman_rho']:+.4f}")
    print()
    print("Ranking lengkap:")
    print(result["ranking_df"][
        ["label", "composite_score", "best_lag_days", "best_spearman_rho", "best_p_value", "selected"]
    ].to_string(index=False))
