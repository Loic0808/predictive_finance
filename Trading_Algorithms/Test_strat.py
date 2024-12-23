import yfinance as yf

from DRL_v1 import StockTradingEnv
from stable_baselines3 import PPO
from datetime import datetime, timedelta

end_test = datetime.today()
start_test = end_test - timedelta(days=29)

end_test_date = end_test.strftime('%Y-%m-%d')
start_test_date = start_test.strftime('%Y-%m-%d')

symbol = "MSFT"
interval = "15m"

# Testing dataset
df_test = yf.download(symbol, start=start_test_date, end=end_test_date, interval=interval)
df_test.columns = df_test.columns.droplevel(1)
df_test.reset_index(inplace=True)
df_test = df_test.rename(columns={"Datetime": "date", "Adj Close": "adj_close"})

# Create trading environment for testing
env_test = StockTradingEnv(df_test, initial_balance=100000, commission_fee=0.0001, slippage_cost=0.005)

# Load model
model = PPO.load(f"Trading_Algorithms/DRL_models/ppo_{symbol}_{interval}_v1_run1", env=env_test)

# Run model
vec_env = model.get_env()
obs = vec_env.reset()
for i in range(len(df_test['adj_close'])):
    action, _state = model.predict(obs)
    obs, reward, done, info = vec_env.step(action)
    
#env_test.render_all()
test_df = env_test.info()

test_df.to_csv(f"Trading_Algorithms/Backtesting/Strat_dataframes/ppo_{symbol}_{interval}_v1_run1.csv", index=False)