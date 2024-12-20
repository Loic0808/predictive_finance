import yfinance as yf

from DRL_v1 import StockTradingEnv
from stable_baselines3 import PPO
from datetime import datetime, timedelta

end_train = datetime.today() - timedelta(days=29)
start_train = datetime.today() - timedelta(days=59)

end_train_date = end_train.strftime('%Y-%m-%d')
start_train_date = start_train.strftime('%Y-%m-%d')

symbol = "MSFT"
interval = "15m"

# Training dataset
df_train = yf.download(symbol, start=start_train_date, end=end_train_date, interval=interval)
df_train.columns = df_train.columns.droplevel(1)
df_train.reset_index(inplace=True)
df_train = df_train.rename(columns={"Datetime": "date", "Adj Close": "adj_close"})

# Create trading environment for training
env_train = StockTradingEnv(df_train, initial_balance=100000, commission_fee=0.0001, slippage_cost=0.005)

# Train model
model = PPO("MlpPolicy", env_train, verbose=0)
model.learn(total_timesteps=100_000, progress_bar=True)

model.save("DRL_models/ppo_msft_v1_run1")



