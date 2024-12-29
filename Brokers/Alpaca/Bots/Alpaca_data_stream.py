from Alpaca_keyes import API_KEY, SECRET_KEY
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import asyncio
import pandas as pd
import threading
import time

from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest

from alpaca.trading.client import TradingClient
from alpaca.data.live.stock import StockDataStream

from Indicators import EMA, ATR
from Connected_EasyBot import EasyBot

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

data_stream_list = []
symbols = [symbol]


# Read data candles every minute
def consumer_thread():
    try:
        # make sure we have an event loop, if not create a new one
        loop = asyncio.get_event_loop()
        loop.set_debug(True)
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    global data_stream
    global data_stream_list

    data_stream = StockDataStream(api_key, secret_key)

    async def stock_data_stream_handler(bar):
        data = {
            'timestamp': [bar.timestamp],
            'open': [bar.open],
            'high': [bar.high],
            'low': [bar.low],
            'close': [bar.close],
            'volume': [bar.volume]
        }
        data_stream_list.append(data)

    data_stream.subscribe_bars(stock_data_stream_handler, *symbols)

    data_stream.run()

def run_bot():
    print("Test")
    time.sleep(5)

    global data_stream_list
    res = False

    df_stream = pd.DataFrame(data_stream_list)

    dataF = pd.concat([df, df_stream], axis=0, ignore_index=True)
    
    # union of historical and live df, calculate EMA and ATR, run bot on the runnging data only
    dataF = EMA(dataF).EMA_50(50)
    dataF = ATR(dataF).calculate_chandelier_exit()

    # If there is no datastream there is no reason to run the following
    if data_stream_list:
        data_of_interest = dataF[-len(data_stream_list):]

        res = trading_bot.run_strat(data_of_interest)

    if res:
        data_stream_list = []


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    # While time between 9.30 and 4 pm and day not sat or sun
    while 1:
        threading.Thread(target=consumer_thread).start()
        time.sleep(5)
        loop.run_until_complete(data_stream.stop_ws())

        # Run the additional function in a separate thread
        additional_thread = threading.Thread(target=run_bot)
        additional_thread.start()
        
        # Wait for the additional function to complete
        additional_thread.join()

        time.sleep(5)


