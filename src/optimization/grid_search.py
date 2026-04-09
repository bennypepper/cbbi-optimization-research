import itertools
import logging
from typing import List, Tuple
from tqdm import tqdm

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from src.optimization.engine import run_backtest_numba

logger = logging.getLogger(__name__)

# Batasan parameter sesuai PRD (Bagian 1.4)
BUY_THRESHOLDS = list(range(1, 46))        # 1-45
SELL_THRESHOLDS = list(range(55, 101))     # 55-100
ALLOC_BUY = [i / 100.0 for i in range(1, 26)]   # 1% - 25%
ALLOC_SELL = [i / 100.0 for i in range(1, 26)]  # 1% - 25%

def _run_chunk(
    chunk: List[Tuple[int, int, float, float]],
    signals: np.ndarray,
    prices_open: np.ndarray,
    prices_close: np.ndarray
) -> List[Tuple]:
    """
    Eksekusi satu chunk iterasi kombinasi (untuk dieksekusi paralel oleh joblib).
    Akan memanggil numba engine secara massal.
    """
    results = []
    # Jalankan simulasi untuk satu kombinasi
    for (t_buy, t_sell, a_buy, a_sell) in chunk:
        (total_return, max_drawdown, 
         sharpe_ratio, wins, sell_count, trade_count) = run_backtest_numba(
            signals, prices_open, prices_close,
            t_buy, t_sell, a_buy, a_sell,
            100000.0, 0.001
        )
        
        # Win rate logic: jika sell_count 0 maka win_rate = 0
        win_rate = float(wins) / sell_count if sell_count > 0 else 0.0
        
        results.append((
            int(t_buy), int(t_sell), float(a_buy), float(a_sell),
            float(total_return), float(max_drawdown), float(sharpe_ratio), 
            float(win_rate), int(trade_count)
        ))
    return results

def run_grid_search(df: pd.DataFrame, signal_column: str = "trolololo", n_jobs: int = -1) -> pd.DataFrame:
    """
    Eksplorasi eksekusi Grid Search memutari semua ruang parameter.
    1.293.750 probabilitas komputasi kombinasi.
    
    Returns:
        DataFrame lengkap yang berisikan riwayat setiap konfigurasi percobaan.
    """
    # Ekstrak data numpy dari dataframe untuk diberikan ke Numba
    signals = df[signal_column].values.astype(np.float64)
    prices_open = df["btc_open"].values.astype(np.float64)
    prices_close = df["btc_close"].values.astype(np.float64)
    
    # 1. Bangun seluruh kombinasi parameter (Cartesian Product)
    combinations = list(itertools.product(
        BUY_THRESHOLDS, SELL_THRESHOLDS, ALLOC_BUY, ALLOC_SELL
    ))
    total_combs = len(combinations)
    logger.info("Total kombinasi Grid Search: %d kombinasi", total_combs)
    
    # 2. Pecah per batch / chunk (contoh: 50,000 per chunk) untuk paralelisasi yang efisien
    chunk_size = 50000
    chunks = [combinations[i:i + chunk_size] for i in range(0, total_combs, chunk_size)]
    
    logger.info("Mengeksekusi %d chunks ke multicore processor via JobLib...", len(chunks))
    
    # 3. Eksekusi terparalelisasi
    results_list2d = Parallel(n_jobs=n_jobs)(
        delayed(_run_chunk)(chunk, signals, prices_open, prices_close)
        for chunk in tqdm(chunks, desc="Grid Search Progress")
    )
    
    # 4. Pipihkan multi-level response (flatMap)
    all_results = [item for sublist in results_list2d for item in sublist]
    
    # 5. Konversi ke DataFrame
    columns = [
        "threshold_buy", "threshold_sell", "allocation_buy_pct", "allocation_sell_pct",
        "total_return", "max_drawdown", "sharpe_ratio", "win_rate", "trade_count"
    ]
    
    results_df = pd.DataFrame(all_results, columns=columns)
    return results_df
