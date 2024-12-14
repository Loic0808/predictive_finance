from TradingBots.DRL_trading_bot import StockTradingEnv
from Connect_to_brokers.YFinance_class import YFinanceGetData

from stable_baselines3 import PPO


YFinance_data_loader = YFinanceGetData("Stocks")
df_train = YFinance_data_loader.get_historical_market_data(["MSFT"], "15m", "2024-10-16", "2024-11-13")
df_train = df_train.rename(columns={"Datetime": "date", "Adj Close": "adj_close"})


env_train = StockTradingEnv(df_train, initial_balance=100000, commission_fee=0.0001, slippage_cost=0.005)

model = PPO("MlpPolicy", env_train, verbose=0)
model.learn(total_timesteps=100_000, progress_bar=True)

# Load and run the data somewhere else

