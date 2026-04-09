import json
import logging
import os
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

# Supress warnings
import warnings
warnings.filterwarnings('ignore')

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_input(prompt, default_val, cast_type=float):
    val = input(f"{prompt} (Default: {default_val}): ").strip()
    if not val:
        return default_val
    try:
        return cast_type(val)
    except ValueError:
        print(f"Input tidak valid. Menggunakan default: {default_val}")
        return default_val

def load_optimal_params(objective_key="max_return"):
    json_path = Path("results/optimal_params_summary.json")
    if not json_path.exists():
        return 45.0, 64.0, 0.25, 0.25  # Fallback
    
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    try:
        best = data["scenario_2"]["full_dataset"][objective_key]
        return best["threshold_buy"], best["threshold_sell"], best["allocation_buy_pct"], best["allocation_sell_pct"]
    except KeyError:
        return 45.0, 64.0, 0.25, 0.25

def run_cli_simulator():
    clear_screen()
    print("=" * 70)
    print(" CBBI BACKTEST SIMULATOR (CLI PROTOTYPE) ".center(70, "="))
    print("=" * 70)
    print("Membaca data historis...")
    
    parquet_path = Path("data/processed/master_dataset.parquet")
    if not parquet_path.exists():
        print(f"Error: {parquet_path} tidak ditemukan!")
        return
        
    df = pd.read_parquet(parquet_path)
    dates_available = df.index
    first_date = dates_available[0].strftime("%Y-%m-%d")
    last_date = dates_available[-1].strftime("%Y-%m-%d")
    
    print("\n[ TARGET OPTIMISASI LINGKUNGAN ]")
    print("Pilih profil risiko berdasarkan hasil klasifikasi Grid Search:")
    print("1. Maximum Return (Agresif)")
    print("2. Minimum Drawdown (Konservatif/Pertahanan Modal Tertinggi)")
    print("3. Maximum Sharpe Ratio (Balanced/Risk-Reward Optimal)")
    
    pilihan = input("Masukkan pilihan Anda (1/2/3) [Default: 1]: ").strip()
    
    obj_key = "max_return"
    obj_name = "Return Maksimum"
    if pilihan == "2":
        obj_key = "min_drawdown"
        obj_name = "Risiko Kerugian (Drawdown) Minimum"
    elif pilihan == "3":
        obj_key = "max_sharpe"
        obj_name = "Rasio Sharpe (Risk-Reward) Maksimum"

    opt_buy, opt_sell, opt_abuy, opt_asell = load_optimal_params(obj_key)
    
    print("\n[ INFORMASI RISET ]")
    print(f"Dari pencarian Grid Search (1,29 juta probabilitas historis),")
    print(f"Titik optimal '{obj_name}' berada pada konfigurasi:")
    print(f"- Buy Threshold : <= {opt_buy}%")
    print(f"- Sell Threshold: >= {opt_sell}%")
    print(f"- Alokasi Beli  : {opt_abuy * 100} % dari sisa Cash")
    print(f"- Alokasi Jual  : {opt_asell * 100} % dari total kepemilikan BTC")
    print("Gunakan parameter optimal di atas, atau kustomisasi mandiri di bawah ini.")
    print("-" * 70)

    print("\n[ KONFIGURASI SIMULASI ]")
    initial_cash = get_input("💰 Modal Awal Kas (USD)", 100000.0, float)
    start_date = get_input(f"📅 Periode Mulai (format YYYY-MM-DD, cth {first_date})", first_date, str)
    end_date = get_input(f"📅 Periode Akhir (format YYYY-MM-DD, cth {last_date})", last_date, str)
    
    buy_thresh = get_input(f"🟢 Buy Threshold (Trolololo <= %)", opt_buy, float)
    sell_thresh = get_input(f"🔴 Sell Threshold (Trolololo >= %)", opt_sell, float)
    alloc_buy = get_input(f"💵 Alokasi Beli (% dari Kas, cth 25)", opt_abuy * 100, float) / 100.0
    alloc_sell = get_input(f"🪙 Alokasi Jual (% dari Koin, cth 25)", opt_asell * 100, float) / 100.0
    
    fee_rate = 0.001 # 0.1% transaction fee flat

    print("\nMempersiapkan Mesin Waktu...")
    
    # Filtering Dataset
    try:
        mask = (df.index >= start_date) & (df.index <= end_date)
        df_sub = df.loc[mask].copy()
    except Exception as e:
        print("Format tanggal tidak valid!", e)
        return
        
    if df_sub.empty:
        print("Periode tanggal kosong atau tidak ditemukan dalam data historis!")
        return

    # Siapkan array
    dates = df_sub.index
    signals = df_sub["trolololo"].values.astype(np.float64)
    p_open = df_sub["btc_open"].values.astype(np.float64)
    p_close = df_sub["btc_close"].values.astype(np.float64)

    n_days = len(signals)
    cash = initial_cash
    btc = 0.0
    
    trade_logs = []
    buy_count = 0
    sell_count = 0
    
    # Tracking metrics (termasuk Peak and Max Drawdown with exact dates)
    portfolio_history = []
    peak_val = initial_cash
    max_dd = 0.0
    max_dd_date = dates[0]

    for i in range(n_days - 1):
        d_today = dates[i].date()
        d_tomor = dates[i+1].date()
        
        sig = signals[i]
        price_t_close = p_close[i]
        price_exec = p_open[i+1] # Anti-lookahead, selalu di-eksekusi Open besoknya
        
        # Penilaian portfolio per hari close time
        curr_val = cash + (btc * price_t_close)
        
        # Max Drawdown logger
        if curr_val > peak_val:
            peak_val = curr_val
        
        dd = (peak_val - curr_val) / peak_val
        if dd > max_dd:
            max_dd = dd
            max_dd_date = d_today
            
        action = None
        
        # Logic trigger trade
        if sig <= buy_thresh:
            trade_amount = cash * alloc_buy
            if trade_amount > 1.0: # Minimum nominal untuk beli
                fee = trade_amount * fee_rate
                net = trade_amount - fee
                btc_bought = net / price_exec
                
                cash -= trade_amount
                btc += btc_bought
                
                action = "BUY"
                buy_count += 1
                trade_logs.append(f"[{d_tomor}] 🟢 BUY  | {btc_bought:8.6f} BTC | Harga: ${price_exec:7.2f} | Modal Tumben: ${trade_amount:7.2f} (Fee: ${fee:5.2f})")
                
        elif sig >= sell_thresh:
            btc_sold = btc * alloc_sell
            if btc_sold > 0.000001: # Minimum nominal untuk jual
                gross = btc_sold * price_exec
                fee = gross * fee_rate
                net = gross - fee
                
                cash += net
                btc -= btc_sold
                
                action = "SELL"
                sell_count += 1
                trade_logs.append(f"[{d_tomor}] 🔴 SELL | {btc_sold:8.6f} BTC | Harga: ${price_exec:7.2f} | Dapat USDT: ${net:7.2f} (Fee: ${fee:5.2f})")
        
        # Update val history untuk graph (kalau untuk streamlit next phase)
        portfolio_history.append({
            "date": d_today,
            "portfolio": curr_val,
            "cash": cash,
            "btc": btc,
            "action": action
        })
        
    # Tambahkan hari terakhir untuk portfolio value
    final_price = p_close[-1]
    final_portfolio_val = cash + (btc * final_price)
    
    # UPDATE PENGECHEKAN DRAWDOWN TERAKHIR
    if final_portfolio_val > peak_val:
        peak_val = final_portfolio_val
    dd = (peak_val - final_portfolio_val) / peak_val
    if dd > max_dd:
        max_dd = dd
        max_dd_date = dates[-1].date()
        
    portfolio_history.append({
        "date": dates[-1].date(),
        "portfolio": final_portfolio_val,
        "cash": cash,
        "btc": btc,
        "action": None
    })

    # METRICS CALCULATION ==============================================================
    strategy_return_pct = ((final_portfolio_val - initial_cash) / initial_cash) * 100
    
    # HODL Benchmark Calculation
    hodl_initial_cash = initial_cash
    hodl_btc_bought = (hodl_initial_cash * (1 - fee_rate)) / p_open[0]
    hodl_final_val = hodl_btc_bought * final_price
    hodl_return_pct = ((hodl_final_val - initial_cash) / initial_cash) * 100
    
    diff_val = final_portfolio_val - hodl_final_val
    diff_str = f"+${diff_val:,.2f} (Strategi Menang!)" if diff_val > 0 else f"-${abs(diff_val):,.2f} (HODL Lebih Baik)"

    # OUTPUT SUMMARY ====================================================================
    clear_screen()
    print("=" * 80)
    print(" HASIL SIMULASI BACKTEST (UI PROTOTYPE) ".center(80, "="))
    print("=" * 80)
    print(f"| PORTFOLIO AKHIR       : ${final_portfolio_val:,.2f}  ({'+' if strategy_return_pct>0 else ''}{strategy_return_pct:,.1f}%)")
    print(f"| HODL COMPARISON       : ${hodl_final_val:,.2f}  ({'+' if hodl_return_pct>0 else ''}{hodl_return_pct:,.1f}%)")
    print(f"| MAX DRAWDOWN          : -{max_dd * 100:,.1f}%  (Terjadi pada: {max_dd_date})")
    print(f"| TOTAL TRADES          : {buy_count + sell_count}  (🟢 {buy_count} Buys, 🔴 {sell_count} Sells)")
    print("-" * 80)
    print(f"| SISA CASH (USD)       : ${cash:,.2f}")
    print(f"| SISA KOIN (BTC)       : {btc:,.6f} BTC")
    print(f"| STRATEGY VS HODL      : {diff_str}")
    print("=" * 80)
    
    # Tampilkan History
    ans = get_input("\nTampilkan histori transaksi lengkap? (y/n)", "n", str)
    if ans.lower() == 'y':
        print("\n--- HISTORI TRANSAKSI ---")
        if not trade_logs:
            print("Tidak ada transaksi sama sekali yang memenuhi threshold.")
        for log in trade_logs:
            print(log)
        print("-------------------------")
        
    print("\nPrototyping CLI selesai! Mode ini akan direplikasi ke dalam Framework Web Streamlit di Fase 4.")

if __name__ == "__main__":
    run_cli_simulator()
