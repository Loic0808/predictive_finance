from Brokers.Alpaca.Alpaca_keyes import API_KEY, SECRET_KEY
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import time

from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest

from alpaca.trading.client import TradingClient
from alpaca.data.live.stock import StockDataStream

from Utils.Indicators import EMA, ATR
from Trading_bots.Connected_EasyBot import EasyBot

api_key = API_KEY
secret_key = SECRET_KEY

symbol = "TSLA"

##################
#Data preparation#
##################

stock_historical_data_client = StockHistoricalDataClient(api_key, secret_key)

now = datetime.now(ZoneInfo("America/New_York"))

# EasyBot will run every minute
req = StockBarsRequest(
    symbol_or_symbols = [symbol],
    timeframe=TimeFrame(amount = 1, unit = TimeFrameUnit.Minute),
    start = now - timedelta(days = 40),                          
    # end_date=None,                                  
    #limit = 2,                    
)

df = stock_historical_data_client.get_stock_bars(req).df

df = df.reset_index()
df = df.drop(['symbol', 'trade_count', 'vwap'], axis=1)

################################
#Prepare trading client and bot#
################################

trade_client = TradingClient(api_key=api_key, secret_key=secret_key, paper=True)
trading_bot = EasyBot(symbol, trade_client)

############################
#Read live data and run bot#
############################

def wait_until_next_minute():
    # Get the current time
    now = datetime.now()
    # Calculate the time for the next minute
    next_minute = (now.replace(second=0, microsecond=0) + timedelta(minutes=1))
    # Calculate the time to sleep until the next minute
    sleep_time = (next_minute - now).total_seconds()
    time.sleep(sleep_time)

while True:
    df_stream = pd.read_csv('Data/live_data.csv') 
    dataF = pd.concat([df, df_stream], axis=0, ignore_index=True)
    print(dataF)
    wait_until_next_minute()


"""dataF = EMA(dataF).EMA_50(50)
dataF = ATR(dataF).calculate_chandelier_exit()

# Read data candles every minute
data_stream = StockDataStream(api_key, secret_key)
data_of_interest = dataF[-len(df_stream):]

res = trading_bot.run_strat(data_of_interest)

if res:
        data_stream_list = []

while True:
        read_and_process_csv(file_path)
        time.sleep(interval)"""

# 2 things to do: I need to reinitialize the stream data if buy or invalid AND I need to make the bot run 
# async or at least continuously
# Need to run the files simultaneously



