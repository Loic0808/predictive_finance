import pandas as pd

df = pd.read_csv("Trading_Algorithms/Backtesting/Strat_dataframes/ppo_MSFT_15m_v1_run1.csv")  

# 4 cases: 
# If multiple sell and then buy: if buy > sell -> profit
#                                else -> loss
# If multiple buy and then sell: if sell > buy -> profit
#                                else -> loss