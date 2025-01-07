from Backtesting.Backtesting_bots.DRL_bot_v1 import StockTradingEnv
from Connect_to_brokers.YFinance_class import YFinanceGetData

from stable_baselines3 import PPO


YFinance_data_loader = YFinanceGetData("Stocks")
df_train = YFinance_data_loader.get_historical_market_data(["MSFT"], "15m", "2024-10-19", "2024-11-16")
df_train = df_train.rename(columns={"Datetime": "date", "Adj Close": "adj_close"})

env_train = StockTradingEnv(df_train, initial_balance=100000, commission_fee=0.0001, slippage_cost=0.005)

model = PPO("MlpPolicy", env_train, verbose=0)
model.learn(total_timesteps=100_000, progress_bar=True)

model.save("Run_bots/Runs/ppo_msft_v1_run1")
# Load and run the data somewhere else


df_test = YFinance_data_loader.get_historical_market_data(["MSFT"], "15m", "2024-11-17", "2024-12-16")
df_test = df_test.rename(columns={"Datetime": "date", "Adj Close": "adj_close"})

env_test = StockTradingEnv(df_test, initial_balance=100000, commission_fee=0.0001, slippage_cost=0.005)

model = PPO.load("Run_bots/Runs/ppo_msft_v1_run1", env=env_test)

vec_env = model.get_env()
obs = vec_env.reset()
for i in range(len(df_test['adj_close'])):
    action, _state = model.predict(obs)
    obs, reward, done, info = vec_env.step(action)
    
env_test.render_all()