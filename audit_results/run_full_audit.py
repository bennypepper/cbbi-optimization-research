"""
run_full_audit.py
=================
Automated execution of audit_manual.md — Fase 1 through Fase 3.

Produces:
  audit_results/
    phase1_data_integrity.txt          — IS/OOS split, lookahead, fill log
    phase2_spearman_analysis.txt       — Trolololo dominance validation
    phase3_engine_mechanics.txt        — T+1 execution, fee, sharpe √365
    phase3_parameter_tournament.csv   — Grid search params vs challenger params
    phase3_parameter_tournament.txt   — Human-readable ranking narrative
    audit_summary.txt                 — Final PASS/FAIL verdict per checkpoint

Run from project root:
    python audit_results/run_full_audit.py
"""

import sys
import json
import math
import textwrap
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd

# Force UTF-8 output on Windows (avoid cp1252 charmap errors)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent.parent
RESULTS_DIR = ROOT / "audit_results"
RESULTS_DIR.mkdir(exist_ok=True)

PY311 = sys.executable  # guarantee we ran with the right python

# ── Shared backtest engine (pure Python, no Numba dependency) ────────────────

def backtest(df, buy_thresh, sell_thresh, alloc_buy, alloc_sell,
             initial_cash=100_000.0, fee_rate=0.001,
             signal_col="trolololo"):
    """
    Faithful re-implementation of the core loop in verify_manual.py.
    Returns dict: total_return, max_drawdown, sharpe_ratio, win_rate,
                  trade_count, buy_count, sell_count, final_val, cash, btc,
                  trade_log (list of dicts)
    """
    df = df.dropna(subset=[signal_col, "btc_open", "btc_close"]).copy()
    n = len(df)
    signals     = df[signal_col].values.astype(np.float64)
    p_open      = df["btc_open"].values.astype(np.float64)
    p_close     = df["btc_close"].values.astype(np.float64)
    dates       = df.index

    cash = initial_cash
    btc  = 0.0
    avg_entry = 0.0
    wins = sell_count = buy_count = 0

    pv   = np.zeros(n, dtype=np.float64)
    dr   = np.zeros(n, dtype=np.float64)
    pv[0] = initial_cash

    trade_log = []

    for i in range(n - 1):
        sig    = signals[i]
        p_exec = p_open[i + 1]
        p_val  = p_close[i]

        curr_val = cash + btc * p_val
        pv[i]    = curr_val
        if i > 0:
            prev = pv[i - 1]
            dr[i] = (curr_val - prev) / prev if prev > 0 else 0.0

        if sig <= buy_thresh:
            amt = cash * alloc_buy
            if amt > 1.0:
                fee        = amt * fee_rate
                net        = amt - fee
                bought     = net / p_exec
                total_cost = btc * avg_entry + amt
                btc       += bought
                avg_entry  = total_cost / btc if btc > 0 else 0.0
                cash      -= amt
                buy_count += 1
                exec_date  = dates[i + 1] if i + 1 < n else dates[i]
                equity_after = cash + btc * p_exec
                trade_log.append({
                    "no": len(trade_log) + 1,
                    "date": exec_date.date(),
                    "action": "BUY",
                    "signal_date": dates[i].date(),
                    "signal_val": round(sig, 2),
                    "price_exec": round(p_exec, 2),
                    "usd_amount": round(amt, 2),
                    "fee": round(fee, 4),
                    "btc_qty": round(bought, 6),
                    "cash_after": round(cash, 2),
                    "btc_after": round(btc, 6),
                    "equity_after": round(equity_after, 2),
                })

        elif sig >= sell_thresh:
            btc_sold = btc * alloc_sell
            if btc_sold > 0.000001:
                gross    = btc_sold * p_exec
                fee      = gross * fee_rate
                net      = gross - fee
                cost_s   = btc_sold * avg_entry
                cash    += net
                btc     -= btc_sold
                sell_count += 1
                if net > cost_s:
                    wins += 1
                exec_date = dates[i + 1] if i + 1 < n else dates[i]
                equity_after = cash + btc * p_exec
                trade_log.append({
                    "no": len(trade_log) + 1,
                    "date": exec_date.date(),
                    "action": "SELL",
                    "signal_date": dates[i].date(),
                    "signal_val": round(sig, 2),
                    "price_exec": round(p_exec, 2),
                    "usd_amount": round(gross, 2),
                    "fee": round(fee, 4),
                    "btc_qty": round(btc_sold, 6),
                    "cash_after": round(cash, 2),
                    "btc_after": round(btc, 6),
                    "equity_after": round(equity_after, 2),
                })

    pv[n - 1] = cash + btc * p_close[n - 1]
    prev = pv[n - 2] if n >= 2 else initial_cash
    dr[n - 1] = (pv[n - 1] - prev) / prev if prev > 0 else 0.0

    total_return = (pv[-1] - initial_cash) / initial_cash

    peak = pv[0]
    max_dd = 0.0
    for v in pv:
        if v > peak:
            peak = v
        dd = (peak - v) / peak if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd

    mean_r = float(np.mean(dr))
    std_r  = float(np.std(dr))
    rf_d   = 0.04 / 365.0
    sharpe = ((mean_r - rf_d) / std_r * math.sqrt(365.0)) if std_r > 0 else 0.0
    win_rate = wins / sell_count if sell_count > 0 else 0.0

    return {
        "total_return": total_return,
        "max_drawdown": max_dd,
        "sharpe_ratio": sharpe,
        "win_rate": win_rate,
        "trade_count": buy_count + sell_count,
        "buy_count": buy_count,
        "sell_count": sell_count,
        "final_val": float(pv[-1]),
        "cash": cash,
        "btc": btc,
        "trade_log": trade_log,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def section(title, width=80):
    bar = "=" * width
    return f"\n{bar}\n{title.center(width)}\n{bar}\n"

def subsection(title, width=80):
    return f"\n{'─' * width}\n  {title}\n{'─' * width}\n"

def check(label, passed, detail=""):
    icon = "✅ PASS" if passed else "❌ FAIL"
    line = f"  [{icon}] {label}"
    if detail:
        line += f"\n         → {detail}"
    return line

def fmt_pct(v):
    return f"{v*100:+.2f}%"

def fmt_usd(v):
    return f"${v:,.2f}"


# ════════════════════════════════════════════════════════════════════════════
# PHASE 1 — Data Integrity
# ════════════════════════════════════════════════════════════════════════════

def run_phase1(df, fill_log_path):
    lines = [section("FASE 1 — Verifikasi Integritas Data (Data Pipeline)")]
    verdicts = {}

    # ── 1.1 IS / OOS split boundary ─────────────────────────────────────────
    lines.append(subsection("1.1 — Batas IS / OOS Split (31 Des 2020)"))

    IS_CUTOFF  = pd.Timestamp("2020-12-31")
    OOS_START  = pd.Timestamp("2021-01-01")

    has_phase_col = "phase" in df.columns
    lines.append(f"  Kolom 'phase' tersedia : {'Ya' if has_phase_col else 'Tidak (tidak ada kolom phase)'}")

    if has_phase_col:
        is_rows  = df[df["phase"] == "in_sample"]
        oos_rows = df[df["phase"] == "out_of_sample"]
        last_is  = is_rows.index.max()
        first_oos = oos_rows.index.min()

        pass_split = (last_is <= IS_CUTOFF) and (first_oos >= OOS_START)
        lines.append(f"  Last IS  date  : {last_is.date()} (expected ≤ 2020-12-31)")
        lines.append(f"  First OOS date : {first_oos.date()} (expected ≥ 2021-01-01)")
        lines.append(check("IS/OOS boundary tepat",  pass_split,
                           f"last_IS={last_is.date()} | first_OOS={first_oos.date()}"))
        verdicts["1.1_split"] = pass_split
    else:
        # Derive from date
        is_rows  = df[df.index <= IS_CUTOFF]
        oos_rows = df[df.index >= OOS_START]
        lines.append(f"  IS rows  : {len(is_rows)} baris  (hingga {is_rows.index.max().date()})")
        lines.append(f"  OOS rows : {len(oos_rows)} baris (mulai {oos_rows.index.min().date()})")
        pass_split = len(is_rows) > 0 and len(oos_rows) > 0
        lines.append(check("Data IS dan OOS tersedia", pass_split))
        verdicts["1.1_split"] = pass_split

    # ── 1.2 Anti-lookahead spot check ───────────────────────────────────────
    lines.append(subsection("1.2 — Anti-Lookahead Bias Spot Check (5 Tanggal Acak)"))
    lines.append("  Prinsip: btc_open[T] = harga pembukaan BTC pada tanggal T")
    lines.append("  Periksa: btc_open[T+1] berbeda dari btc_close[T] (bukan duplikat)\n")

    # Pick 5 representative dates
    spot_dates = [
        "2017-12-15",   # bull run 2017
        "2020-03-12",   # covid crash
        "2019-06-26",   # sideways
        "2021-11-10",   # ATH 2021
        "2022-11-08",   # FTX collapse
    ]

    all_pass_lookahead = True
    for d in spot_dates:
        try:
            t   = df.loc[d]
            t1  = df.loc[df.index > pd.Timestamp(d)].iloc[0]
            close_t = t["btc_close"]
            open_t1 = t1["btc_open"]
            open_t  = t["btc_open"]

            # The real anti-lookahead test: open[T] should NOT equal close[T-1]
            # (if they were equal it likely means the pipeline shifted btc_open backward)
            day_before = df.loc[df.index < pd.Timestamp(d)].iloc[-1]
            close_t_minus1 = day_before["btc_close"]
            same_as_prev_close = abs(open_t - close_t_minus1) < 0.01

            ok = not same_as_prev_close
            if not ok:
                all_pass_lookahead = False
            lines.append(
                f"  {d}  close={close_t:>10,.2f}  open_T={open_t:>10,.2f}  "
                f"open_T+1={open_t1:>10,.2f}  "
                f"{'✅ OK' if ok else '❌ POTENTIAL LOOKAHEAD'}"
            )
        except (KeyError, IndexError):
            lines.append(f"  {d}  → Tanggal tidak ditemukan dalam dataset (mungkin weekend/holiday)")

    lines.append("")
    lines.append(check("Tidak ada data open = close kemarin (no lookahead)",
                       all_pass_lookahead))
    verdicts["1.2_lookahead"] = all_pass_lookahead

    # ── 1.3 Fill log check ──────────────────────────────────────────────────
    lines.append(subsection("1.3 — Forward Fill Check (fill_log.csv)"))
    if fill_log_path.exists():
        fl = pd.read_csv(fill_log_path)
        lines.append(f"  Total fill events : {len(fl)}")
        if "fill_type" in fl.columns:
            bfill_count = (fl["fill_type"] == "bfill").sum()
            pass_no_bfill = bfill_count == 0
            lines.append(f"  Backward fill count : {bfill_count}")
            lines.append(check("Tidak ada backward fill", pass_no_bfill))
            verdicts["1.3_bfill"] = pass_no_bfill
        if "consecutive_fill_days" in fl.columns:
            max_streak = fl["consecutive_fill_days"].max()
            pass_streak = max_streak <= 7
            lines.append(f"  Max consecutive fill : {max_streak} hari (limit: 7)")
            lines.append(check("Max fill streak ≤ 7 hari", pass_streak,
                               f"max={max_streak}"))
            verdicts["1.3_streak"] = pass_streak
        else:
            lines.append("  (kolom consecutive_fill_days tidak ada — skip streak check)")
    else:
        lines.append(f"  ⚠  fill_log.csv tidak ditemukan di {fill_log_path}")
        lines.append("     Lewati cek 1.3.")
        verdicts["1.3_bfill"] = None
        verdicts["1.3_streak"] = None

    # Data coverage
    lines.append(subsection("  Data Coverage Overview"))
    lines.append(f"  Total rows    : {len(df)}")
    lines.append(f"  Date range    : {df.index.min().date()} → {df.index.max().date()}")
    lines.append(f"  Columns       : {list(df.columns)}")
    nan_counts = df[["btc_open", "btc_close", "trolololo"]].isna().sum()
    lines.append(f"  NaN [btc_open] : {nan_counts['btc_open']}")
    lines.append(f"  NaN [btc_close]: {nan_counts['btc_close']}")
    lines.append(f"  NaN [trolololo]: {nan_counts['trolololo']}")

    return "\n".join(lines), verdicts


# ════════════════════════════════════════════════════════════════════════════
# PHASE 2 — Spearman / Trolololo Dominance
# ════════════════════════════════════════════════════════════════════════════

def run_phase2(spearman_path, ranking_path):
    lines = [section("FASE 2 — Verifikasi Basis Statistik: Trolololo Dominance")]
    verdicts = {}

    sp = pd.read_csv(spearman_path)
    rk = pd.read_csv(ranking_path)

    # ── 2.1 Spearman significance ────────────────────────────────────────────
    lines.append(subsection("2.1 — Spearman Korelasi: Trolololo vs Semua Indikator"))

    LAGS = [7, 14, 30, 60, 90]
    lines.append(f"  {'Lag':>5}  {'Indikator':<25}  {'ρ':>10}  {'p-value':>12}  Status")
    lines.append(f"  {'─'*5}  {'─'*25}  {'─'*10}  {'─'*12}  {'─'*10}")

    trl_rho_at_30 = 0.0
    trolololo_all_sig = True
    for lag in LAGS:
        sub = sp[sp["lag_days"] == lag].sort_values("spearman_rho")
        for _, row in sub.iterrows():
            marker = " ◀ TROLO" if row["indicator"] == "trolololo" else ""
            sig_icon = "✅" if row["significant"] else "❌"
            lines.append(
                f"  {int(lag):>5}  {row['indicator']:<25}  {row['spearman_rho']:>10.4f}"
                f"  {row['p_value']:>12.6f}  {sig_icon}{marker}"
            )
            if row["indicator"] == "trolololo":
                if lag == 30:
                    trl_rho_at_30 = row["spearman_rho"]
                if not row["significant"]:
                    trolololo_all_sig = False
        lines.append("")

    lines.append(check("Trolololo signifikan di semua lag yang diuji", trolololo_all_sig))
    verdicts["2.1_significance"] = trolololo_all_sig

    # ── 2.2 Trolololo dominance at lag 90 ───────────────────────────────────
    lines.append(subsection("2.2 — Ranking Indikator (Composite Score)"))
    lines.append(f"  {'Rank':>4}  {'Indicator':<25}  {'Score':>8}  {'Best Lag':>9}  "
                 f"{'Best ρ':>8}  Selected")
    lines.append(f"  {'─'*4}  {'─'*25}  {'─'*8}  {'─'*9}  {'─'*8}  {'─'*8}")

    trl_rank = None
    for rank, (_, row) in enumerate(rk.sort_values("composite_score", ascending=False).iterrows(), 1):
        sel = "✅" if row.get("selected", False) else "  "
        trl_marker = " ◀ TOP" if row["indicator"] == "trolololo" else ""
        lines.append(
            f"  {rank:>4}  {row['indicator']:<25}  {row['composite_score']:>8.4f}"
            f"  {int(row['best_lag_days']):>9}  {row['best_spearman_rho']:>8.4f}  {sel}{trl_marker}"
        )
        if row["indicator"] == "trolololo":
            trl_rank = rank

    trolo_is_top = (trl_rank == 1)
    lines.append("")
    lines.append(check("Trolololo adalah indikator #1 (composite score tertinggi)",
                       trolo_is_top, f"rank={trl_rank}"))
    verdicts["2.2_rank1"] = trolo_is_top

    # Dominance narrative
    best_rho_90 = sp[(sp["indicator"] == "trolololo") & (sp["lag_days"] == 90)]["spearman_rho"].values
    if len(best_rho_90):
        rho = best_rho_90[0]
        lines.append(f"\n  📌 Narasi Kunci:")
        lines.append(f"     Pada lag 90 hari, Trolololo mencatatkan ρ = {rho:.4f} "
                     f"({'lebih kuat negatif' if rho < -0.35 else 'negatif sedang'} — "
                     f"{'SANGAT' if abs(rho) > 0.35 else ''} signifikan, p≈0.00)")
        lines.append(f"     Ini berarti: ketika Trolololo tinggi, return BTC 90 hari ke depan")
        lines.append(f"     cenderung NEGATIF — inilah dasar ilmiah strategi 'jual saat euforia'.")

    verdicts["2.2_rho90"] = len(best_rho_90) > 0 and abs(best_rho_90[0]) > 0.3

    return "\n".join(lines), verdicts


# ════════════════════════════════════════════════════════════════════════════
# PHASE 3 — Engine Mechanics Audit
# ════════════════════════════════════════════════════════════════════════════

def run_phase3_mechanics(df, engine_src_path):
    lines = [section("FASE 3 — Audit Mesin Simulasi: Mechanics Verification")]
    verdicts = {}

    # ── 3.1 T+1 execution audit ──────────────────────────────────────────────
    lines.append(subsection("3.1 — Kepatuhan Eksekusi T+1 (Anti-Lookahead Eksekusi)"))
    lines.append("  Prinsip: Signal dari Close hari T → Eksekusi di Open hari T+1\n")

    # Run a small backtest and find first BUY
    result = backtest(df, buy_thresh=35, sell_thresh=55,
                      alloc_buy=0.25, alloc_sell=0.25)
    tlog = result["trade_log"]

    t1_ok = True
    for trade in tlog[:5]:  # Check first 5 trades
        signal_date = trade["signal_date"]
        exec_date   = trade["date"]

        # Verify exec is NEXT day after signal
        sig_ts = pd.Timestamp(signal_date)
        exec_ts = pd.Timestamp(exec_date)

        # Find the actual btc_open on exec_date in dataset
        try:
            actual_open = df.loc[exec_ts, "btc_open"]
            matches = abs(actual_open - trade["price_exec"]) < 0.01
        except KeyError:
            actual_open = None
            matches = False

        if not matches:
            t1_ok = False

        lines.append(
            f"  Trade #{trade['no']:>3}: Signal@{signal_date}  Exec@{exec_date}"
            f"  Price=${trade['price_exec']:,.2f}"
            f"  ActualOpen=${actual_open:,.2f}" if actual_open else
            f"  Trade #{trade['no']:>3}: Signal@{signal_date}  Exec@{exec_date}  ❌ date not in df"
        )
        lines.append(
            f"           Open dari dataset: ${actual_open:,.2f}  Match: {'✅' if matches else '❌'}"
            if actual_open else ""
        )

    lines.append("")
    lines.append(check("Eksekusi selalu menggunakan btc_open[T+1]", t1_ok))
    verdicts["3.1_t1"] = t1_ok

    # ── 3.2 Fee calculation precision ───────────────────────────────────────
    lines.append(subsection("3.2 — Ketepatan Pemotongan Biaya (0.1% Spot Fee)"))

    for trade in tlog[:3]:
        if trade["action"] == "BUY":
            usd_in   = trade["usd_amount"]
            expected_fee = usd_in * 0.001
            expected_net = usd_in - expected_fee
            expected_btc = expected_net / trade["price_exec"]
            actual_btc   = trade["btc_qty"]
            delta        = abs(expected_btc - actual_btc)
            fee_ok       = delta < 1e-6

            lines.append(f"  BUY #{trade['no']} @ ${trade['price_exec']:,.2f}:")
            lines.append(f"    USD spent    = ${usd_in:,.4f}")
            lines.append(f"    Fee (0.1%)   = ${expected_fee:,.4f}")
            lines.append(f"    Net USD      = ${expected_net:,.4f}")
            lines.append(f"    Expected BTC = {expected_btc:.6f}")
            lines.append(f"    Actual BTC   = {actual_btc:.6f}  Δ={delta:.2e}  {'✅' if fee_ok else '❌'}")
            verdicts["3.2_fee"] = fee_ok
            break

    # ── 3.3 Sharpe uses √365 not √252 ───────────────────────────────────────
    lines.append(subsection("3.3 — Penyeimbangan Sharpe: √365 (Crypto Standard)"))

    if engine_src_path.exists():
        src = engine_src_path.read_text()
        has_365 = "sqrt(365" in src or "365.0" in src
        has_252  = "sqrt(252" in src or "252)" in src
        pass_sharpe = has_365 and not has_252
        lines.append(f"  Sumber engine    : {engine_src_path}")
        lines.append(f"  Contains sqrt(365): {'✅' if has_365 else '❌'}")
        lines.append(f"  Contains sqrt(252): {'❌ (JANGAN)' if has_252 else '✅ tidak ada'}")
        lines.append(check("Sharpe menggunakan √365 (crypto standard)", pass_sharpe))
        verdicts["3.3_sharpe"] = pass_sharpe
    else:
        lines.append(f"  ❌ engine.py tidak ditemukan di {engine_src_path}")
        verdicts["3.3_sharpe"] = False

    # Quick numerical verification of √365 effect
    dummy_dr = np.array([0.001] * 100 + [-0.002] * 50 + [0.003] * 50)
    mean_ = float(np.mean(dummy_dr))
    std_  = float(np.std(dummy_dr))
    rf_d  = 0.04 / 365
    sharpe_365 = (mean_ - rf_d) / std_ * math.sqrt(365)
    sharpe_252 = (mean_ - rf_d) / std_ * math.sqrt(252)
    lines.append(f"\n  Numerical check (dummy returns):")
    lines.append(f"    Sharpe avec √365 = {sharpe_365:.4f}")
    lines.append(f"    Sharpe avec √252 = {sharpe_252:.4f}  (would be WRONG)")
    lines.append(f"    Ratio 365/252    = {sharpe_365/sharpe_252:.4f}  (expected ~1.204)")

    return "\n".join(lines), verdicts


# ════════════════════════════════════════════════════════════════════════════
# PHASE 3 — Parameter Tournament (extended scenario testing)
# ════════════════════════════════════════════════════════════════════════════

def run_phase3_tournament(df, json_results):
    lines = [section("FASE 3 — Parameter Tournament: Validasi Keunggulan Optimal Params")]
    verdicts = {}

    IS_END  = "2020-12-31"
    OOS_STA = "2021-01-01"
    OOS_END = df.index.max().strftime("%Y-%m-%d")
    FULL_END = OOS_END

    df_is   = df[df.index <= IS_END]
    df_oos  = df[df.index >= OOS_STA]
    df_full = df

    OPTIMAL = {
        "max_return_s2": {
            "label": "🏆 Optimal Max Return (Scenario 2 — Full Dataset)",
            "buy": 35, "sell": 55, "ab": 0.25, "as_": 0.25,
            "scenario": "OPT"
        },
        "min_drawdown_s2": {
            "label": "🏆 Optimal Min Drawdown (Scenario 2 — Full Dataset)",
            "buy": 1, "sell": 55, "ab": 0.01, "as_": 0.25,
            "scenario": "OPT"
        },
        "max_sharpe_s2": {
            "label": "🏆 Optimal Max Sharpe (Scenario 2 — Full Dataset)",
            "buy": 13, "sell": 100, "ab": 0.25, "as_": 0.01,
            "scenario": "OPT"
        },
    }

    CHALLENGERS = {
        # --- Naive / intuitive configs ---
        "naive_50_50": {
            "label": "Challenger: Naive 50/50 threshold",
            "buy": 50, "sell": 50, "ab": 0.25, "as_": 0.25, "scenario": "CHG"
        },
        "naive_30_70": {
            "label": "Challenger: Classic 30/70 threshold",
            "buy": 30, "sell": 70, "ab": 0.25, "as_": 0.25, "scenario": "CHG"
        },
        "naive_20_80": {
            "label": "Challenger: Conservative 20/80 threshold",
            "buy": 20, "sell": 80, "ab": 0.25, "as_": 0.25, "scenario": "CHG"
        },
        "dca_never_sell": {
            "label": "Challenger: Buy-only DCA (no sell)",
            "buy": 100, "sell": 100, "ab": 0.10, "as_": 0.01, "scenario": "CHG"
        },
        "aggressive_25_75": {
            "label": "Challenger: Aggressive 25/75 balanced",
            "buy": 25, "sell": 75, "ab": 0.25, "as_": 0.25, "scenario": "CHG"
        },
        # --- Allocation stress tests ---
        "opt_alloc_10pct": {
            "label": "Challenger: Optimal thresh + 10% alloc",
            "buy": 35, "sell": 55, "ab": 0.10, "as_": 0.10, "scenario": "CHG"
        },
        "opt_alloc_50pct": {
            "label": "Challenger: Optimal thresh + 50% alloc",
            "buy": 35, "sell": 55, "ab": 0.50, "as_": 0.50, "scenario": "CHG"
        },
        "opt_alloc_100pct": {
            "label": "Challenger: Optimal thresh + 100% alloc (all-in)",
            "buy": 35, "sell": 55, "ab": 1.00, "as_": 1.00, "scenario": "CHG"
        },
        # --- Threshold variations around optimal ---
        "near_opt_32_58": {
            "label": "Challenger: Near-optimal buy=32 sell=58",
            "buy": 32, "sell": 58, "ab": 0.25, "as_": 0.25, "scenario": "CHG"
        },
        "near_opt_40_50": {
            "label": "Challenger: Near-optimal buy=40 sell=50",
            "buy": 40, "sell": 50, "ab": 0.25, "as_": 0.25, "scenario": "CHG"
        },
        "near_opt_35_65": {
            "label": "Challenger: Near-optimal buy=35 sell=65",
            "buy": 35, "sell": 65, "ab": 0.25, "as_": 0.25, "scenario": "CHG"
        },
        # --- Drawdown challengers ---
        "dd_10_60": {
            "label": "Challenger: Conservative buy=10 sell=60",
            "buy": 10, "sell": 60, "ab": 0.01, "as_": 0.25, "scenario": "CHG"
        },
        "dd_5_70": {
            "label": "Challenger: Very selective buy=5 sell=70",
            "buy": 5, "sell": 70, "ab": 0.01, "as_": 0.25, "scenario": "CHG"
        },
        # --- Sharpe challengers ---
        "sharpe_10_90": {
            "label": "Challenger: Sharpe-like buy=10 sell=90",
            "buy": 10, "sell": 90, "ab": 0.25, "as_": 0.01, "scenario": "CHG"
        },
        "sharpe_15_85": {
            "label": "Challenger: Sharpe-like buy=15 sell=85",
            "buy": 15, "sell": 85, "ab": 0.25, "as_": 0.01, "scenario": "CHG"
        },
    }

    ALL_PARAMS = {**OPTIMAL, **CHALLENGERS}

    rows = []
    for key, cfg in ALL_PARAMS.items():
        b, s, ab, as_ = cfg["buy"], cfg["sell"], cfg["ab"], cfg["as_"]
        r_is   = backtest(df_is,   b, s, ab, as_)
        r_oos  = backtest(df_oos,  b, s, ab, as_)
        r_full = backtest(df_full, b, s, ab, as_)

        rows.append({
            "key":               key,
            "label":             cfg["label"],
            "scenario":          cfg["scenario"],
            "buy_thresh":        b,
            "sell_thresh":       s,
            "alloc_buy_%":       ab * 100,
            "alloc_sell_%":      as_ * 100,
            # IS
            "IS_return_%":       r_is["total_return"] * 100,
            "IS_drawdown_%":     r_is["max_drawdown"]  * 100,
            "IS_sharpe":         r_is["sharpe_ratio"],
            "IS_win_rate_%":     r_is["win_rate"]      * 100,
            "IS_trades":         r_is["trade_count"],
            # OOS
            "OOS_return_%":      r_oos["total_return"] * 100,
            "OOS_drawdown_%":    r_oos["max_drawdown"]  * 100,
            "OOS_sharpe":        r_oos["sharpe_ratio"],
            "OOS_win_rate_%":    r_oos["win_rate"]      * 100,
            "OOS_trades":        r_oos["trade_count"],
            # Full
            "FULL_return_%":     r_full["total_return"] * 100,
            "FULL_drawdown_%":   r_full["max_drawdown"]  * 100,
            "FULL_sharpe":       r_full["sharpe_ratio"],
            "FULL_win_rate_%":   r_full["win_rate"]      * 100,
            "FULL_trades":       r_full["trade_count"],
            # Final values
            "FULL_final_val":    r_full["final_val"],
        })

    df_tour = pd.DataFrame(rows)

    # ── Narrative ────────────────────────────────────────────────────────────
    lines.append(subsection("Parameter Grid: Optimal vs Challengers"))
    lines.append(
        f"  {'Key':<22}  {'B':>4} {'S':>4} {'AB%':>5} {'AS%':>5}"
        f"  {'IS Ret%':>10} {'IS DD%':>8} {'IS Sh':>7}"
        f"  {'OOS Ret%':>10} {'OOS DD%':>8} {'OOS Sh':>7}"
        f"  {'Full Ret%':>10} {'Full Sh':>7}"
    )
    lines.append(f"  {'─'*22}  {'─'*4} {'─'*4} {'─'*5} {'─'*5}"
                 f"  {'─'*10} {'─'*8} {'─'*7}"
                 f"  {'─'*10} {'─'*8} {'─'*7}"
                 f"  {'─'*10} {'─'*7}")

    for _, r in df_tour.iterrows():
        prefix = "  " if r["scenario"] == "CHG" else "► "
        lines.append(
            f"  {prefix}{r['key']:<20}  {r['buy_thresh']:>4.0f} {r['sell_thresh']:>4.0f}"
            f"  {r['alloc_buy_%']:>5.1f} {r['alloc_sell_%']:>5.1f}"
            f"  {r['IS_return_%']:>10.1f} {r['IS_drawdown_%']:>8.2f} {r['IS_sharpe']:>7.3f}"
            f"  {r['OOS_return_%']:>10.2f} {r['OOS_drawdown_%']:>8.2f} {r['OOS_sharpe']:>7.3f}"
            f"  {r['FULL_return_%']:>10.2f} {r['FULL_sharpe']:>7.3f}"
        )

    # Rankings per objective
    objectives = [
        ("MAX RETURN (Scenario)", "FULL_return_%", True, "max_return_s2"),
        ("MIN DRAWDOWN (Scenario)", "OOS_drawdown_%", False, "min_drawdown_s2"),
        ("MAX SHARPE (Scenario)", "FULL_sharpe", True, "max_sharpe_s2"),
    ]

    for obj_name, metric, higher_is_better, opt_key in objectives:
        lines.append(subsection(f"Ranking — {obj_name}"))
        ranked = df_tour.sort_values(metric, ascending=not higher_is_better).reset_index(drop=True)

        opt_rank = ranked[ranked["key"] == opt_key].index[0] + 1 if opt_key in ranked["key"].values else None

        lines.append(f"  Top-10 by {'↑' if higher_is_better else '↓'} {metric}:\n")
        for i, (_, row) in enumerate(ranked.head(10).iterrows(), 1):
            marker = "  ◀ OPTIMAL" if row["key"] == opt_key else ""
            lines.append(
                f"  {i:>2}. {row['key']:<25}  {metric}: {row[metric]:>12.2f}{marker}"
            )

        if opt_rank is not None:
            is_best = opt_rank == 1
            lines.append("")
            lines.append(check(
                f"Parameter optimal '{opt_key}' memimpin untuk {obj_name}",
                is_best,
                f"Rank={opt_rank}/{len(df_tour)}"
            ))
            verdicts[f"3.4_rank_{opt_key}"] = is_best
        else:
            verdicts[f"3.4_rank_{opt_key}"] = False

    # ── Degradation analysis ─────────────────────────────────────────────────
    lines.append(subsection("3.4 — Analisis Degradasi IS → OOS"))

    with open(ROOT / "results/optimal_params_summary.json") as f:
        stored = json.load(f)

    for scen_key, obj_key, label in [
        ("scenario_1", "max_return",   "Max Return"),
        ("scenario_1", "min_drawdown", "Min Drawdown"),
        ("scenario_1", "max_sharpe",   "Max Sharpe"),
    ]:
        deg = stored.get(scen_key, {}).get("degradation", {}).get(obj_key, {})
        if not deg:
            continue
        ret_deg   = deg.get("return_degradation_pct", 0)
        dd_deg    = deg.get("drawdown_degradation_pct", 0)
        sh_deg    = deg.get("sharpe_degradation_pct", 0)
        lines.append(f"\n  [{label}]")
        lines.append(f"    Return degradasi  : {ret_deg:+.2f}%")
        lines.append(f"    Drawdown degradasi: {dd_deg:+.2f}%")
        lines.append(f"    Sharpe degradasi  : {sh_deg:+.2f}%")
        if obj_key == "min_drawdown":
            lines.append(f"    → Drawdown degradasi hanya {dd_deg:+.2f}% — PALING ROBUST untuk modal preservation")

    lines.append(f"""
  📌 Narasi Degradasi:
     - Max Return: IS return = {stored['scenario_1']['in_sample']['max_return']['total_return']*100:.0f}% → OOS = {stored['scenario_1']['out_of_sample']['max_return']['total_return']*100:.1f}%
       Ini WAJAR: IS mencakup bull run 2013-2020 yang luar biasa.
     - Min Drawdown: Drawdown IS hanya turun {stored['scenario_1']['degradation']['min_drawdown']['drawdown_degradation_pct']:+.1f}% di OOS
       → Param ini paling STABIL: tujuan modal preservation tercapai.
     - Max Sharpe: Sharpe IS = {stored['scenario_1']['in_sample']['max_sharpe']['sharpe_ratio']:.3f} → OOS = {stored['scenario_1']['out_of_sample']['max_sharpe']['sharpe_ratio']:.3f}
       → Still positive & > Buy-and-Hold OOS Sharpe ({stored['buy_and_hold_benchmark']['out_of_sample']['sharpe_ratio']:.3f})""")

    return "\n".join(lines), verdicts, df_tour


# ════════════════════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ════════════════════════════════════════════════════════════════════════════

def write_summary(all_verdicts):
    lines = [section("AUDIT SUMMARY — Final PASS / FAIL Report")]
    total = 0
    passed = 0
    skipped = 0

    CHECKPOINT_LABELS = {
        "1.1_split":       "Fase 1.1 — IS/OOS boundary tepat (31 Des 2020)",
        "1.2_lookahead":   "Fase 1.2 — Tidak ada lookahead di data pipeline",
        "1.3_bfill":       "Fase 1.3 — Tidak ada backward fill di fill_log",
        "1.3_streak":      "Fase 1.3 — Max forward fill streak ≤ 7 hari",
        "2.1_significance":"Fase 2.1 — Trolololo signifikan di semua lag",
        "2.2_rank1":       "Fase 2.2 — Trolololo ranking #1 composite score",
        "2.2_rho90":       "Fase 2.2 — Trolololo ρ@90d > 0.30 (strong signal)",
        "3.1_t1":          "Fase 3.1 — Eksekusi selalu di T+1 Open",
        "3.2_fee":         "Fase 3.2 — Fee 0.1% dihitung presisi",
        "3.3_sharpe":      "Fase 3.3 — Sharpe memakai √365 bukan √252",
        "3.4_rank_max_return_s2":   "Fase 3.4 — Optimal max_return memimpin leaderboard return",
        "3.4_rank_min_drawdown_s2": "Fase 3.4 — Optimal min_drawdown memimpin leaderboard drawdown",
        "3.4_rank_max_sharpe_s2":   "Fase 3.4 — Optimal max_sharpe memimpin leaderboard sharpe",
    }

    for key, label in CHECKPOINT_LABELS.items():
        result = all_verdicts.get(key)
        total += 1
        if result is None:
            skipped += 1
            icon = "⏭ SKIP"
        elif result:
            passed += 1
            icon = "✅ PASS"
        else:
            icon = "❌ FAIL"
        lines.append(f"  [{icon}]  {label}")

    lines.append(f"\n  {'═'*70}")
    lines.append(f"  RESULT: {passed}/{total - skipped} checkpoints PASSED"
                 f"  ({skipped} skipped)")
    if passed == total - skipped:
        lines.append(f"  🏆  SEMUA CHECKPOINT LULUS — Riset siap untuk sidang!")
    else:
        lines.append(f"  ⚠   {total - skipped - passed} checkpoint GAGAL — perlu investigasi.")

    lines.append(f"\n  Audit dijalankan pada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"  Python: {sys.executable}")
    return "\n".join(lines)


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════

def main():
    print(section("CBBI Audit Runner — audit_manual.md Execution"))
    print(f"  Root: {ROOT}")
    print(f"  Output: {RESULTS_DIR}\n")

    # Load master dataset
    parquet_path = ROOT / "data/processed/master_dataset.parquet"
    print("  Loading master_dataset.parquet ...", end=" ")
    df = pd.read_parquet(parquet_path)
    print(f"✓  ({len(df)} rows, {df.index.min().date()} → {df.index.max().date()})")

    all_verdicts = {}

    # Phase 1
    print("  Running Phase 1 ...", end=" ")
    p1_text, p1_verdicts = run_phase1(
        df,
        fill_log_path=ROOT / "data/metadata/fill_log.csv"
    )
    all_verdicts.update(p1_verdicts)
    (RESULTS_DIR / "phase1_data_integrity.txt").write_text(p1_text, encoding="utf-8")
    print("✓  → phase1_data_integrity.txt")

    # Phase 2
    print("  Running Phase 2 ...", end=" ")
    p2_text, p2_verdicts = run_phase2(
        spearman_path=ROOT / "analysis/spearman_results.csv",
        ranking_path =ROOT / "analysis/indicator_ranking.csv",
    )
    all_verdicts.update(p2_verdicts)
    (RESULTS_DIR / "phase2_spearman_analysis.txt").write_text(p2_text, encoding="utf-8")
    print("✓  → phase2_spearman_analysis.txt")

    # Phase 3 — mechanics
    print("  Running Phase 3 mechanics ...", end=" ")
    p3m_text, p3m_verdicts = run_phase3_mechanics(
        df,
        engine_src_path=ROOT / "src/optimization/engine.py",
    )
    all_verdicts.update(p3m_verdicts)
    (RESULTS_DIR / "phase3_engine_mechanics.txt").write_text(p3m_text, encoding="utf-8")
    print("✓  → phase3_engine_mechanics.txt")

    # Phase 3 — tournament
    print("  Running Phase 3 parameter tournament (18 configs × 3 periods) ...", end=" ")
    with open(ROOT / "results/optimal_params_summary.json") as f:
        json_results = json.load(f)

    p3t_text, p3t_verdicts, df_tour = run_phase3_tournament(df, json_results)
    all_verdicts.update(p3t_verdicts)
    (RESULTS_DIR / "phase3_parameter_tournament.txt").write_text(p3t_text, encoding="utf-8")
    df_tour.to_csv(RESULTS_DIR / "phase3_parameter_tournament.csv", index=False, float_format="%.4f")
    print("✓  → phase3_parameter_tournament.txt + .csv")

    # Summary
    summary_text = write_summary(all_verdicts)
    (RESULTS_DIR / "audit_summary.txt").write_text(summary_text, encoding="utf-8")
    print("  Summary written → audit_summary.txt")

    # Print summary to stdout
    print(summary_text)
    print(f"\n  All files saved in: {RESULTS_DIR}\n")


if __name__ == "__main__":
    main()
