from datetime import datetime

from Backtesting.Backtesting_bots.DRL_bot_v1 import DRLBotV1
from Backtesting.DRL_backtest_models.Train_models import TrainDRLModels
from Backtesting.Backtesting import Backtesting

from Brokers.Alpaca.Alpaca_keyes import API_KEY, SECRET_KEY
from Utils.Indicators import EMA, ATR

from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

model_name = "Easy_DRL_v1.2"
bank_account = 10000
commission_fee = 0.01
slippage_cost = 0.1

###########################
##Training of the DRL bot##
###########################

Trainer = TrainDRLModels(model_name, bank_account, commission_fee, slippage_cost)

if not Trainer.zip_file_exists():
    print("Path does not exist, train the model")
    # Format is (YYYY, MM, DD)
    start_date_train = datetime(2024, 1, 1) 
    end_date_train = datetime(2024, 5, 1)

    df_train = Trainer.create_dataframe(
        api_key=API_KEY,
        secret_key=SECRET_KEY,
        start_date=start_date_train,
        end_date=end_date_train,
        interval=TimeFrame(amount = 1, unit = TimeFrameUnit.Minute),
        asset_list="TSLA"
    )

    Trainer.train_model(df_train)
else:
    print("Path does exist, load the model")

########################
##Load and run DRL bot##
########################

start_date_run = datetime(2024, 5, 1) 
end_date_run = datetime(2024, 7, 1)

backtesting = Backtesting()

data_df = backtesting.create_dataframe(
    api_key=API_KEY,
    secret_key=SECRET_KEY,
    start_date=start_date_run,
    end_date=end_date_run,
    interval=TimeFrame(amount = 1, unit = TimeFrameUnit.Minute),
    asset_list="TSLA"
    )

if data_df.empty:
    raise Exception("Empty dataframe")


data_df = EMA(data_df).EMA_50(50)
data_df = ATR(data_df).calculate_chandelier_exit()

DRL_bot = DRLBotV1(model_name, bank_account, commission_fee, slippage_cost)

backtesting_df = backtesting.run_bot(DRL_bot, data_df)

print(backtesting_df)

"""
backtesting_df, log_info_list = backtesting.run_bot(easy_bot, data_df)

backtesting_df = backtesting.calculate_profit_and_loss(backtesting_df, trade_type)
backtesting_df = backtesting.calculate_MAE_MFE(backtesting_df, trade_type)
backtesting_df = backtesting.calculate_risk_to_reward(backtesting_df, trade_type)
backtesting_df = backtesting.monetary_gains(backtesting_df, trade_type)

#print(backtesting_df)
#print(log_info_list)

print("Gains, losses and net profit", backtesting.net_profit(backtesting_df))
print("Winning rate", backtesting.win_rate(backtesting_df))
print("Profit factor", backtesting.profit_factor(backtesting_df))
print("Average win/loss", backtesting.average_win_over_loss(backtesting_df))
print("Risk reward ration", backtesting.risk_reward_ratio(backtesting_df))
print("Profitability", backtesting.profitability(backtesting_df))
print("Consistency", backtesting.consistency(backtesting_df))
print("Equity curve simulation", backtesting.equity_curve_simulation(backtesting_df, bank_account))
"""







"""from Backtesting.Backtesting_bots.DRL_bot_v1 import StockTradingEnv
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
    
env_test.render_all()"""