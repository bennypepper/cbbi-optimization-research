import json
import logging
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from src.optimization.grid_search import run_grid_search
from src.optimization.engine import run_backtest_numba

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parents[2]
PARQUET_PATH = ROOT_DIR / "data" / "processed" / "master_dataset.parquet"
RESULTS_DIR = ROOT_DIR / "results"
TRIAL_LOG_DIR = RESULTS_DIR / "trial_log"


def create_buy_and_hold_benchmark(prices_close: np.ndarray) -> dict:
    initial_price = prices_close[0]
    final_price = prices_close[-1]
    total_return = (final_price - initial_price) / initial_price
    
    # Drawdown
    max_drawdown = 0.0
    peak = prices_close[0]
    for p in prices_close:
        if p > peak:
            peak = p
        dd = (peak - p) / peak
        if dd > max_drawdown:
            max_drawdown = dd
            
    # Sharpe
    daily_returns = np.array([(prices_close[i] - prices_close[i-1])/prices_close[i-1] for i in range(1, len(prices_close))])
    mean_ret = np.mean(daily_returns)
    std_ret = np.std(daily_returns)
    rf_daily = 0.04 / 365.0
    sharpe_ratio = 0.0
    if std_ret > 0:
        sharpe_ratio = ((mean_ret - rf_daily) / std_ret) * np.sqrt(365.0)
        
    return {
        "total_return": float(total_return),
        "max_drawdown": float(max_drawdown),
        "sharpe_ratio": float(sharpe_ratio)
    }

def calculate_degradation(val_is, val_oos, minimize=False):
    if minimize: # e.g. drawdown (lower is better) -> if OOS is higher, it degraded
        # if val_is == 0 prevent div by zero
        if val_is == 0: return 0.0
        return (val_oos - val_is) / val_is
    else: # e.g return or sharpe (higher is better) -> if OOS is lower, it degraded
        if val_is == 0: return 0.0
        return (val_is - val_oos) / val_is 

def extract_best(df: pd.DataFrame, objective: str, min_trade_count: int = 10) -> dict:
    valid_df = df[df["trade_count"] >= min_trade_count]
    if valid_df.empty:
        # fallback
        valid_df = df
        
    if objective == "max_return":
        best_idx = valid_df["total_return"].idxmax()
    elif objective == "min_drawdown":
        best_idx = valid_df["max_drawdown"].idxmin()
    elif objective == "max_sharpe":
        best_idx = valid_df["sharpe_ratio"].idxmax()
        
    best_row = valid_df.loc[best_idx]
    return best_row.to_dict()

def run_phase3():
    logger.info("=" * 60)
    logger.info("FASE 3: Mesin Optimisasi & Backtest Numba — MULAI")
    logger.info("=" * 60)
    
    if not PARQUET_PATH.exists():
        raise FileNotFoundError(f"Dataset master tidak ditemukan: {PARQUET_PATH}")
        
    df = pd.read_parquet(PARQUET_PATH)
    
    # Pembagian dataset
    df_is = df[df["phase"] == "in_sample"].copy()
    df_oos = df[df["phase"] == "out_of_sample"].copy()
    df_full = df.copy()
    
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    TRIAL_LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Data dict output akhir
    final_output = {
        "metadata": {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_trials_per_run": 1293750,
        },
        "scenario_1": {
            "algorithm_used": "grid_search"
        },
        "scenario_2": {
            "algorithm_used": "grid_search",
            "disclosure": "Hasil ini menggunakan seluruh data historis dalam proses optimisasi. Konfigurasi ini tidak dapat digunakan sebagai sinyal prediktif. Tujuannya adalah memetakan batas potensi maksimal indikator CBBI secara historis."
        },
        "buy_and_hold_benchmark": {
            "in_sample": create_buy_and_hold_benchmark(df_is["btc_close"].values),
            "out_of_sample": create_buy_and_hold_benchmark(df_oos["btc_close"].values),
            "full_dataset": create_buy_and_hold_benchmark(df_full["btc_close"].values)
        }
    }
    
    # ── SKENARIO 1 ──
    logger.info("Memulai SKENARIO 1 (In-Sample: 2012-2020)")
    start_time = time.time()
    results_is = run_grid_search(df_is)
    results_is.to_parquet(TRIAL_LOG_DIR / "scenario_1_grid_search_in_sample.parquet")
    logger.info("Skernario 1 Grid Search In-Sample Selesai! (Waktu: %.2f detik)", time.time() - start_time)
    
    # Extract best untuk IS
    best_is_ret = extract_best(results_is, "max_return")
    best_is_dd = extract_best(results_is, "min_drawdown")
    best_is_shp = extract_best(results_is, "max_sharpe")
    
    final_output["scenario_1"]["in_sample"] = {
        "max_return": best_is_ret,
        "min_drawdown": best_is_dd,
        "max_sharpe": best_is_shp
    }
    
    # OOS Evaluation secara selektif pada OOS dataset untuk parameter best_is _*
    logger.info("Evaluasi Out-of-Sample Skenario 1...")
    signals_oos = df_oos["trolololo"].values.astype(np.float64)
    prices_open_oos = df_oos["btc_open"].values.astype(np.float64)
    prices_close_oos = df_oos["btc_close"].values.astype(np.float64)
    
    oos_evaluations = {}
    degradations = {}
    
    for obj_key, best_params in [("max_return", best_is_ret), ("min_drawdown", best_is_dd), ("max_sharpe", best_is_shp)]:
        (ret_oos, dd_oos, shp_oos, wins_oos, sell_count_oos, tc_oos) = run_backtest_numba(
            signals_oos, prices_open_oos, prices_close_oos,
            best_params["threshold_buy"], best_params["threshold_sell"],
            best_params["allocation_buy_pct"], best_params["allocation_sell_pct"],
            100000.0, 0.001
        )
        wr_oos = float(wins_oos) / sell_count_oos if sell_count_oos > 0 else 0.0
        
        oos_evaluations[obj_key] = {
            "threshold_buy": best_params["threshold_buy"],
            "threshold_sell": best_params["threshold_sell"],
            "allocation_buy_pct": best_params["allocation_buy_pct"],
            "allocation_sell_pct": best_params["allocation_sell_pct"],
            "total_return": ret_oos,
            "max_drawdown": dd_oos,
            "sharpe_ratio": shp_oos,
            "win_rate": wr_oos,
            "trade_count": tc_oos
        }
        
        degradations[obj_key] = {
            "return_degradation_pct": calculate_degradation(best_params["total_return"], ret_oos, minimize=False) * 100,
            "drawdown_degradation_pct": calculate_degradation(best_params["max_drawdown"], dd_oos, minimize=True) * 100,
            "sharpe_degradation_pct": calculate_degradation(best_params["sharpe_ratio"], shp_oos, minimize=False) * 100,
            "trade_count_oos": tc_oos,
            "low_sample_warning": tc_oos < 10
        }
        
    final_output["scenario_1"]["out_of_sample"] = oos_evaluations
    final_output["scenario_1"]["degradation"] = degradations
    

    # ── SKENARIO 2 ──
    logger.info("Memulai SKENARIO 2 (Full Dataset: 2012-2026)")
    start_time = time.time()
    results_full = run_grid_search(df_full)
    results_full.to_parquet(TRIAL_LOG_DIR / "scenario_2_grid_search_full.parquet")
    logger.info("Skernario 2 Grid Search Selesai! (Waktu: %.2f detik)", time.time() - start_time)
    
    # Extract best untuk FULL
    final_output["scenario_2"]["full_dataset"] = {
        "max_return": extract_best(results_full, "max_return"),
        "min_drawdown": extract_best(results_full, "min_drawdown"),
        "max_sharpe": extract_best(results_full, "max_sharpe")
    }

    # Terakhir, Simpan Summary Result
    out_json = RESULTS_DIR / "optimal_params_summary.json"
    with open(out_json, "w") as f:
        json.dump(final_output, f, indent=2)
        
    logger.info("Output Final JSON Optimal Params berhasil disimpan di: %s", out_json)
    logger.info("Tahap 3 Selesai dengan Sukses!")

if __name__ == "__main__":
    run_phase3()
