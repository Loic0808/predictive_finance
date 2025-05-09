from datetime import datetime

from Backtesting.Backtesting_bots.EasyBot import EasyBot
from Backtesting.Backtesting import Backtesting
from Brokers.Alpaca.Alpaca_keyes import API_KEY, SECRET_KEY
from Utils.Indicators import EMA, ATR

from alpaca.data.timeframe import TimeFrame, TimeFrameUnit


# Format is (YYYY, MM, DD)
start_date = datetime(2024, 1, 1) 
end_date = datetime(2024, 1, 5)

trade_type = "long"

backtesting = Backtesting()

data_df = backtesting.create_dataframe(
    api_key=API_KEY,
    secret_key=SECRET_KEY,
    start_date=start_date,
    end_date=end_date,
    interval=TimeFrame(amount = 1, unit = TimeFrameUnit.Minute),
    asset_list="TSLA"
    )

if data_df.empty:
    raise Exception("Empty dataframe")


data_df = EMA(data_df).EMA_50(50)
data_df = ATR(data_df).calculate_chandelier_exit()

bank_account = 10000
stock_quantity = 10

easy_bot = EasyBot(bank_account, stock_quantity, data_df)

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
