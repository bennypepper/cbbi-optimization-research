import sys
sys.path.insert(0, 'd:/Personal Projects/PKL_webapp')

import pandas as pd
import numpy as np

# Test data loader paths
from core.data_loader import DATASET_PATH, RESULTS_PATH, SCENARIO_1_LOG, SCENARIO_2_LOG
print('Dataset exists:', DATASET_PATH.exists())
print('Results JSON exists:', RESULTS_PATH.exists())
print('S1 log exists:', SCENARIO_1_LOG.exists())
print('S2 log exists:', SCENARIO_2_LOG.exists())

df = pd.read_parquet(DATASET_PATH)
print('Dataset shape:', df.shape)
print('Columns:', list(df.columns))
print('Date range:', df.index.min().date(), '->', df.index.max().date())
print('Trolololo sample values:', df['trolololo'].head(3).values)

# Test engine
from core.engine import run_backtest_full, warmup_numba
print('Warming up Numba...')
warmup_numba()
print('Warmup done.')

df_slice = df.loc['2015-01-01':'2020-12-31'].copy()
result = run_backtest_full(df_slice, 20, 75, 0.10, 0.10, 100000.0, 0.001)
m = result.metrics
print('-- Simulation Result --')
print('Total return:', round(m['total_return'] * 100, 1), '%')
print('Trades:', m['trade_count'])
print('Sharpe:', round(m['sharpe_ratio'], 2))
print('Trade log rows:', len(result.trade_log))
print('Portfolio history rows:', len(result.portfolio_history))

# Test charts import
from core.charts import build_equity_chart, build_cbbi_chart
fig1 = build_equity_chart(result)
print('Equity chart traces:', len(fig1.data))

fig2 = build_cbbi_chart(df_slice, 20, 75)
print('CBBI chart traces:', len(fig2.data))

print('ALL CHECKS PASSED')
