"""
verify_manual.py
================
CLI Backtest Simulator — prototype tool for manual verification of Phase 3.

Run from project root:
    python -m src.optimization.verify_manual

Alias shortcut (add to PowerShell profile):
    function cbbi { python -m src.optimization.verify_manual @args }
"""

import json
import os
from pathlib import Path
import pandas as pd
import numpy as np

import warnings
warnings.filterwarnings("ignore")


# ── Helpers ───────────────────────────────────────────────────────────────────

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def get_input(prompt, default_val, cast_type=float):
    val = input(f"  {prompt} (Default: {default_val}): ").strip()
    if not val:
        return default_val
    try:
        return cast_type(val)
    except ValueError:
        print(f"  ⚠  Input tidak valid. Menggunakan default: {default_val}")
        return default_val


def load_optimal_params(objective_key="max_return"):
    json_path = Path("results/optimal_params_summary.json")
    if not json_path.exists():
        return 45.0, 64.0, 0.25, 0.25  # Fallback hardcode

    with open(json_path, "r") as f:
        data = json.load(f)

    try:
        best = data["scenario_2"]["full_dataset"][objective_key]
        return (
            best["threshold_buy"],
            best["threshold_sell"],
            best["allocation_buy_pct"],
            best["allocation_sell_pct"],
        )
    except KeyError:
        return 45.0, 64.0, 0.25, 0.25


def _fmt_usd(v):
    return f"${v:>14,.2f}"


def _fmt_btc(v):
    return f"{v:>12.6f}"


def _col(text, width, align="<"):
    return f"{text:{align}{width}}"


# ── Rich table printer ────────────────────────────────────────────────────────

COL_WIDTHS = {
    "#":           4,
    "Tanggal":     12,
    "Tipe":         5,
    "Harga BTC":   12,
    "Jumlah USD":  14,
    "Jumlah BTC":  12,
    "Index":        7,
    "Cash Setelah":14,
    "BTC Setelah": 12,
    "Equity":      14,
}

HEADERS = list(COL_WIDTHS.keys())
SEPARATORS = {k: "-" * v for k, v in COL_WIDTHS.items()}


def _row(*cells):
    parts = []
    for cell, (col, width) in zip(cells, COL_WIDTHS.items()):
        parts.append(f"{str(cell):<{width}}")
    return "  ".join(parts)


def print_trade_table(trade_logs):
    """Print rich transaction history table to terminal."""
    if not trade_logs:
        print("\n  Tidak ada transaksi yang memenuhi threshold.\n")
        return

    n_total = len(trade_logs)
    print(f"\n  {'=' * 120}")
    print(f"   📋 Riwayat Transaksi — {n_total} transaksi ditemukan")
    print(f"  {'=' * 120}")

    # Header
    header = _row(*HEADERS)
    print(f"  {header}")
    sep = _row(*SEPARATORS.values())
    print(f"  {sep}")

    for row in trade_logs:
        tipo = row["action"]
        prefix = "🟢" if tipo == "BUY" else "🔴"

        line = _row(
            row["no"],
            row["tanggal"],
            f"{prefix} {tipo}",
            f"${row['harga_btc']:,.2f}",
            f"${row['jumlah_usd']:,.2f}",
            f"{row['jumlah_btc']:.6f}",
            f"{row['index']:.1f}%",
            f"${row['cash_setelah']:,.2f}",
            f"{row['btc_setelah']:.6f}",
            f"${row['equity']:,.2f}",
        )
        print(f"  {line}")

    print(f"  {sep}\n")


# ── Main CLI ──────────────────────────────────────────────────────────────────

def run_cli_simulator():
    clear_screen()
    print("=" * 80)
    print(" CBBI BACKTEST SIMULATOR — Verifikasi Manual Fase 3 ".center(80, "="))
    print("=" * 80)
    print()

    parquet_path = Path("data/processed/master_dataset.parquet")
    if not parquet_path.exists():
        print(f"  ❌ Error: {parquet_path} tidak ditemukan!")
        print("     Jalankan pipeline preprocessor terlebih dahulu.")
        return

    print("  Membaca data historis...", end=" ")
    df = pd.read_parquet(parquet_path)
    first_date = df.index[0].strftime("%Y-%m-%d")
    last_date  = df.index[-1].strftime("%Y-%m-%d")
    print(f"✓  ({len(df)} hari, {first_date} → {last_date})")
    print()

    # ── Pilih skenario ──────────────────────────────────────────────────────
    print("  ┌─ TARGET OPTIMISASI ─────────────────────────────────────────────────┐")
    print("  │  1. Maximum Return  (Agresif)                                       │")
    print("  │  2. Minimum Drawdown (Konservatif / Pertahanan Modal)               │")
    print("  │  3. Maximum Sharpe  (Balanced / Risk-Reward Optimal)                │")
    print("  └─────────────────────────────────────────────────────────────────────┘")
    print()
    pilihan = input("  Masukkan pilihan (1/2/3) [Default: 1]: ").strip()

    obj_key  = "max_return"
    obj_name = "Return Maksimum"
    if pilihan == "2":
        obj_key, obj_name = "min_drawdown", "Risiko Kerugian (Drawdown) Minimum"
    elif pilihan == "3":
        obj_key, obj_name = "max_sharpe", "Rasio Sharpe (Risk-Reward) Maksimum"

    opt_buy, opt_sell, opt_abuy, opt_asell = load_optimal_params(obj_key)

    print()
    print("  ┌─ KONFIGURASI OPTIMAL GRID SEARCH ──────────────────────────────────┐")
    print(f"  │  Skenario  : {obj_name:<55} │")
    print(f"  │  Buy  Thr  : <= {opt_buy}%{'':<53} │")
    print(f"  │  Sell Thr  : >= {opt_sell}%{'':<53} │")
    print(f"  │  Alokasi Beli : {opt_abuy * 100:.0f}% dari sisa Cash{'':<41} │")
    print(f"  │  Alokasi Jual : {opt_asell * 100:.0f}% dari total BTC{'':<42} │")
    print("  └─────────────────────────────────────────────────────────────────────┘")
    print()

    # ── Input konfigurasi ───────────────────────────────────────────────────
    print("  ─── KONFIGURASI SIMULASI ───────────────────────────────────────────────")
    initial_cash = get_input("💰 Modal Awal Kas (USD)", 100_000.0, float)
    start_date   = get_input(f"📅 Periode Mulai (YYYY-MM-DD, cth {first_date})", first_date, str)
    end_date     = get_input(f"📅 Periode Akhir (YYYY-MM-DD, cth {last_date})",  last_date,  str)
    buy_thresh   = get_input("🟢 Buy Threshold  (Trolololo <=  %)", opt_buy,         float)
    sell_thresh  = get_input("🔴 Sell Threshold (Trolololo >=  %)", opt_sell,        float)
    alloc_buy    = get_input(f"💵 Alokasi Beli  (% dari Kas, cth {opt_abuy*100:.0f})", opt_abuy * 100,  float) / 100.0
    alloc_sell   = get_input(f"🪙 Alokasi Jual  (% dari Koin, cth {opt_asell*100:.0f})", opt_asell * 100, float) / 100.0

    fee_rate = 0.001  # 0.1% flat

    if buy_thresh >= sell_thresh:
        print(f"\n  ⛔ Buy Threshold ({buy_thresh}) harus lebih kecil dari Sell Threshold ({sell_thresh})!")
        return

    # ── Filter data ─────────────────────────────────────────────────────────
    print(f"\n  Mempersiapkan mesin waktu... ({start_date} → {end_date})")
    try:
        mask   = (df.index >= start_date) & (df.index <= end_date)
        df_sub = df.loc[mask].copy()
    except Exception as e:
        print(f"  ❌ Format tanggal tidak valid: {e}")
        return

    if df_sub.empty:
        print("  ❌ Periode tanggal tidak ditemukan dalam data historis!")
        return

    dates    = df_sub.index
    signals  = df_sub["trolololo"].values.astype(np.float64)
    p_open   = df_sub["btc_open"].values.astype(np.float64)
    p_close  = df_sub["btc_close"].values.astype(np.float64)
    n_days   = len(signals)

    # ── Backtest loop ────────────────────────────────────────────────────────
    cash = initial_cash
    btc  = 0.0
    avg_entry_price = 0.0

    trade_logs   = []   # rich dict rows for table display
    buy_count    = 0
    sell_count   = 0
    peak_val     = initial_cash
    max_dd       = 0.0
    max_dd_date  = dates[0].date()

    for i in range(n_days - 1):
        d_today = dates[i].date()
        d_tomor = dates[i + 1].date()

        sig          = signals[i]
        price_close  = p_close[i]
        price_exec   = p_open[i + 1]   # Anti-lookahead: execute at T+1 open

        curr_val = cash + (btc * price_close)

        # Max drawdown tracking
        if curr_val > peak_val:
            peak_val = curr_val
        dd = (peak_val - curr_val) / peak_val if peak_val > 0 else 0.0
        if dd > max_dd:
            max_dd      = dd
            max_dd_date = d_today

        # Trade decision
        if sig <= buy_thresh:
            trade_amount = cash * alloc_buy
            if trade_amount > 1.0:
                fee        = trade_amount * fee_rate
                net_usd    = trade_amount - fee
                btc_bought = net_usd / price_exec

                total_cost      = (btc * avg_entry_price) + trade_amount
                btc            += btc_bought
                avg_entry_price = total_cost / btc if btc > 0 else 0.0
                cash           -= trade_amount
                buy_count      += 1

                equity_after = cash + btc * price_exec
                trade_logs.append({
                    "no":          len(trade_logs) + 1,
                    "tanggal":     str(d_tomor),
                    "action":      "BUY",
                    "harga_btc":   price_exec,
                    "jumlah_usd":  trade_amount,
                    "jumlah_btc":  btc_bought,
                    "index":       sig,
                    "cash_setelah":cash,
                    "btc_setelah": btc,
                    "equity":      equity_after,
                    # Inline compact string kept for log-only view
                    "_brief": (
                        f"[{d_tomor}] 🟢 BUY  | {btc_bought:8.6f} BTC | "
                        f"Harga: ${price_exec:8,.2f} | Modal: ${trade_amount:10,.2f} "
                        f"(Fee: ${fee:6.2f}) | CBBI: {sig:.1f}%"
                    ),
                })

        elif sig >= sell_thresh:
            btc_sold = btc * alloc_sell
            if btc_sold > 0.000001:
                gross  = btc_sold * price_exec
                fee    = gross * fee_rate
                net    = gross - fee
                cash  += net
                btc   -= btc_sold
                sell_count += 1

                equity_after = cash + btc * price_exec
                trade_logs.append({
                    "no":          len(trade_logs) + 1,
                    "tanggal":     str(d_tomor),
                    "action":      "SELL",
                    "harga_btc":   price_exec,
                    "jumlah_usd":  gross,
                    "jumlah_btc":  btc_sold,
                    "index":       sig,
                    "cash_setelah":cash,
                    "btc_setelah": btc,
                    "equity":      equity_after,
                    "_brief": (
                        f"[{d_tomor}] 🔴 SELL | {btc_sold:8.6f} BTC | "
                        f"Harga: ${price_exec:8,.2f} | Dapat: ${net:10,.2f} "
                        f"(Fee: ${fee:6.2f}) | CBBI: {sig:.1f}%"
                    ),
                })

    # Final day valuation
    final_price = p_close[-1]
    final_val   = cash + (btc * final_price)
    if final_val > peak_val:
        peak_val = final_val
    dd = (peak_val - final_val) / peak_val if peak_val > 0 else 0.0
    if dd > max_dd:
        max_dd      = dd
        max_dd_date = dates[-1].date()

    # ── HODL benchmark ───────────────────────────────────────────────────────
    hodl_btc = (initial_cash * (1 - fee_rate)) / p_open[0]
    hodl_val = hodl_btc * final_price
    strategy_return = ((final_val   - initial_cash) / initial_cash) * 100
    hodl_return     = ((hodl_val    - initial_cash) / initial_cash) * 100
    diff_val        = final_val - hodl_val

    # ── Output summary ───────────────────────────────────────────────────────
    clear_screen()
    print("=" * 80)
    print(" HASIL SIMULASI BACKTEST — VERIFIKASI MANUAL FASE 3 ".center(80, "="))
    print("=" * 80)
    print()
    print(f"  {'METRIK':<35} {'STRATEGI':>20}   {'HODL':>20}")
    print(f"  {'-'*75}")
    print(f"  {'Nilai Portfolio Akhir':<35} {'${:,.2f}'.format(final_val):>20}   {'${:,.2f}'.format(hodl_val):>20}")
    print(f"  {'Total Return':<35} {'{:+.2f}%'.format(strategy_return):>20}   {'{:+.2f}%'.format(hodl_return):>20}")
    print(f"  {'Max Drawdown':<35} {'-{:.2f}%'.format(max_dd*100):>20}   {'':>20}")
    print(f"  {'Tgl Max Drawdown':<35} {str(max_dd_date):>20}   {'':>20}")
    print(f"  {'Total Trades':<35} {'{} (🟢 {} Buy, 🔴 {} Sell)'.format(buy_count+sell_count, buy_count, sell_count):>20}   {'':>20}")
    print(f"  {'-'*75}")
    print(f"  {'Sisa Cash (USD)':<35} {'${:,.2f}'.format(cash):>20}")
    print(f"  {'Sisa BTC':<35} {'{:.6f} BTC'.format(btc):>20}")
    print()
    verdict = f"+${diff_val:,.2f}  → Strategi Menang! 🚀" if diff_val > 0 else f"-${abs(diff_val):,.2f}  → HODL Lebih Baik"
    print(f"  Strategy vs HODL : {verdict}")
    print("=" * 80)

    # ── Riwayat transaksi ────────────────────────────────────────────────────
    print()
    ans = input("  Tampilkan riwayat transaksi lengkap? (y/n) [Default: n]: ").strip().lower()
    if ans == "y":
        print_trade_table(trade_logs)

    print()
    print("  ✅ Prototyping CLI selesai! Mode ini direplikasi ke Streamlit di Fase 4.")
    print()


if __name__ == "__main__":
    run_cli_simulator()
