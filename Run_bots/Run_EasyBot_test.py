import os
import time
import pytz
import pandas as pd

import time as timemodule
from datetime import datetime, time, timezone, timedelta
from zoneinfo import ZoneInfo

from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest

from alpaca.trading.client import TradingClient

from Brokers.Alpaca.Alpaca_keyes import API_KEY, SECRET_KEY
from Utils.Indicators import EMA, ATR
from Trading_bots.Connected_EasyBot import EasyBot

api_key = API_KEY
secret_key = SECRET_KEY

file_path = '/Users/doblerloic/Desktop/Finance_prediction_project/predictive_finance/Brokers/Alpaca/Data/live_data.csv'

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
    now = datetime.now()
    next_minute = (now.replace(second=0, microsecond=0) + timedelta(minutes=1))
    sleep_time = (next_minute - now).total_seconds()
    # We assume a small delay of 2 seconds
    delay = 2
    timemodule.sleep(sleep_time + delay)

"""
It can happen that we have data loss, i.e. one minute can be skipped and then we land directly at the next 
minute.
"""

def parse_datetime(dt_str):
    return datetime.strptime(dt_str, "[datetime.datetime(%Y, %m, %d, %H, %M, tzinfo=datetime.timezone.utc)]")

def convert_df(df):
    df['timestamp'] = df['timestamp'].apply(parse_datetime).dt.tz_localize(pytz.utc)
    df['open'] = df['open'].str.strip('[]').astype('float64')
    df['high'] = df['high'].str.strip('[]').astype('float64')
    df['low'] = df['low'].str.strip('[]').astype('float64')
    df['close'] = df['close'].str.strip('[]').astype('float64')
    df['volume'] = df['volume'].str.strip('[]').astype('float64')
    return df

i = 1
j = 1

def is_market_open():

    eastern = pytz.timezone('US/Eastern')
    now = datetime.now(eastern)

    market_open = time(9, 30)
    market_close = time(16, 0)

    is_weekday = now.weekday() < 5
    is_market_hours = market_open <= now.time() <= market_close
    
    return is_weekday and is_market_hours

while True:
    if is_market_open():
        if not os.path.exists(file_path):
            print("Data loss")
        else:
            df_stream = pd.read_csv(file_path) 
            print(df_stream)

        if len(df_stream) == i-1:
            wait_until_next_minute()
        
        elif len(df_stream) == i: 
            df_stream = convert_df(df_stream)
            dataF = pd.concat([df, df_stream], axis=0, ignore_index=True)

            dataF = EMA(dataF).EMA_50(50)
            dataF = ATR(dataF).calculate_chandelier_exit()

            data_of_interest = dataF[-j:]

            res = trading_bot.run_strat(data_of_interest)

            # If we buy or there is an invalid trade, we reinitialize the data
            if res:
                j = 1

            print(i, j, res, df_stream['timestamp'].iloc[-1])
            print(datetime.now(timezone.utc) - df_stream['timestamp'].iloc[-1])

            i+=1
            j+=1
            # Only do skip to next minute if it is not already passed
            if datetime.now(timezone.utc) - df_stream['timestamp'].iloc[-1] < timedelta(seconds=120):
                print("wait untile next min")
                wait_until_next_minute()
            else:
                continue
        
        """# Handle first minute and times where we have data loss
        else:
            continue
            #timemodule.sleep(30)
            #print("sleep")"""
    else:
        print("Market is closed.")
        break  


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




