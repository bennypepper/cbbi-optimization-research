import numpy as np
from numba import njit
import pandas as pd

@njit
def run_backtest_numba(
    signals: np.ndarray,
    prices_open: np.ndarray,
    prices_close: np.ndarray,
    threshold_buy: int,
    threshold_sell: int,
    alloc_buy_pct: float,
    alloc_sell_pct: float,
    initial_cash: float = 100000.0,
    fee_rate: float = 0.001
):
    """
    Core backtest loop menggunakan Numba untuk kecepatan optimal (C-level performance).
    Mengembalikan array metrik dan array histori nilai portofolio.
    
    ATURAN EKSEKUSI (Anti-Lookahead Bias):
    - Sinyal hari T: `signals[T]` (didapat dari data penutupan market hari T).
    - Berdasarkan `signals[T]`, eksekusi Beli/Jual diputuskan dan dilakukan 
      pada hari berikutnya (T+1) menggunakan `prices_open[T+1]`.
    """
    n_days = len(signals)
    
    cash = initial_cash
    btc = 0.0
    trade_count = 0
    wins = 0
    sell_count = 0
    
    # Portfolio value tracker
    portfolio_value = np.zeros(n_days, dtype=np.float64)
    daily_returns = np.zeros(n_days, dtype=np.float64)
    
    avg_entry_price = 0.0
    
    portfolio_value[0] = initial_cash
    
    for i in range(n_days - 1):
        sig = signals[i]
        p_exec = prices_open[i+1] # Harga Open hari T+1 untuk eksekusi
        p_close_eval = prices_close[i] # Untuk valuasi akhir hari ke-i
        
        # Penilaian portfolio di hari i (sebelum eksekusi besok)
        curr_val = cash + (btc * p_close_eval)
        portfolio_value[i] = curr_val
        if i > 0:
            daily_returns[i] = (portfolio_value[i] - portfolio_value[i-1]) / portfolio_value[i-1]
            
        # Logika Trading Eksekusi T+1
        if sig < threshold_buy:
            # Sinyal Buy
            trade_amount = cash * alloc_buy_pct
            if trade_amount > 0:
                fee = trade_amount * fee_rate
                net_usd = trade_amount - fee
                btc_bought = net_usd / p_exec
                
                # Weighted average entry price
                total_cost = (btc * avg_entry_price) + trade_amount
                btc += btc_bought
                if btc > 0:
                    avg_entry_price = total_cost / btc
                
                cash -= trade_amount
                trade_count += 1
                
        elif sig > threshold_sell:
            # Sinyal Sell
            btc_sold = btc * alloc_sell_pct
            if btc_sold > 0:
                gross_usd = btc_sold * p_exec
                fee = gross_usd * fee_rate
                net_usd = gross_usd - fee
                
                cash += net_usd
                btc -= btc_sold
                trade_count += 1
                
                # Validasi hit win rate
                cost_of_sold = btc_sold * avg_entry_price
                if net_usd > cost_of_sold:
                    wins += 1
                sell_count += 1
    
    # Valuasi hari terakhir
    portfolio_value[n_days-1] = cash + (btc * prices_close[n_days-1])
    daily_returns[n_days-1] = (portfolio_value[n_days-1] - portfolio_value[n_days-2]) / portfolio_value[n_days-2]
    
    # ── Kalkulasi Metrik ──
    # 1. Total Return
    total_return = (portfolio_value[-1] - initial_cash) / initial_cash
    
    # 2. Maximum Drawdown
    max_drawdown = 0.0
    peak = portfolio_value[0]
    for i in range(n_days):
        if portfolio_value[i] > peak:
            peak = portfolio_value[i]
        dd = (peak - portfolio_value[i]) / peak
        if dd > max_drawdown:
            max_drawdown = dd
            
    # 3. Sharpe Ratio
    mean_ret = np.mean(daily_returns)
    std_ret = np.std(daily_returns)
    rf_daily = 0.04 / 365.0
    
    sharpe_ratio = 0.0
    if std_ret > 0:
        sharpe_ratio = ((mean_ret - rf_daily) / std_ret) * np.sqrt(365.0)
        
    # Output
    return total_return, max_drawdown, sharpe_ratio, wins, sell_count, trade_count
