from datetime import datetime

from Backtesting.Backtesting_bots.EasyBot import EasyBot
from Backtesting.Backtesting import Backtesting
from Brokers.Alpaca.Alpaca_keyes import API_KEY, SECRET_KEY
from Utils.Indicators import EMA, ATR

from alpaca.data.timeframe import TimeFrame, TimeFrameUnit


# Format is (YYYY, MM, DD)
start_date = datetime(2024, 1, 1) 
end_date = datetime(2024, 1, 5)

backtesting = Backtesting()

data_df = backtesting.create_dataframe(
    api_key=API_KEY,
    secret_key=SECRET_KEY,
    start_date=start_date,
    end_date=end_date,
    interval=TimeFrame(amount = 1, unit = TimeFrameUnit.Minute),
    asset_list="TSLA"
    )

data_df = EMA(data_df).EMA_50(50)
data_df = ATR(data_df).calculate_chandelier_exit()

bank_account = 10000

easy_bot = EasyBot(bank_account, data_df)

backtesting_df = backtesting.run_bot(easy_bot)

# The error is that the bot runs the second part of the strategy only at the end.
# I enter in the buy signal multiple times, I need to reinitialize (a part) of the data
# or I need to add a bool variable so that I don't enter the buy signal.

print(backtesting_df)