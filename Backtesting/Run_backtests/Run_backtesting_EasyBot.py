from datetime import datetime

from Backtesting.Backtesting_bots.EasyBot import EasyBot
from Backtesting.Backtesting import Backtesting
from Brokers.Alpaca.Alpaca_keyes import API_KEY, SECRET_KEY

from alpaca.data.timeframe import TimeFrame, TimeFrameUnit


start_date = datetime(2024, 1, 1) # (YYYY, MM, DD)
end_date = datetime(2024, 4, 1)

backtesting = Backtesting()

backtesting_df = backtesting.create_dataframe(
    api_key=API_KEY,
    secret_key=SECRET_KEY,
    start_date=start_date,
    end_date=end_date,
    interval=TimeFrame(amount = 1, unit = TimeFrameUnit.Minute),
    asset_list="TSLA"
    )

print(backtesting_df)

#easy_bot = EasyBot(10000)