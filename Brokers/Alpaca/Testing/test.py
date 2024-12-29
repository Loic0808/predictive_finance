from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest

import nest_asyncio
nest_asyncio.apply()

import asyncio
from alpaca.data.live.stock import StockDataStream
import pandas as pd


import threading
import time


API_KEY = "PKAG0XBVFXJPXPXBWPGW"
SECRET_KEY = "pjp69zCQBSUziTzXEjZ9DagW04sni7Jg99QKH6TH"

api_key = API_KEY
secret_key = SECRET_KEY

symbol = "TSLA"

stock_historical_data_client = StockHistoricalDataClient(api_key, secret_key)

symbols = [symbol]

def consumer_thread():
    try:
        # make sure we have an event loop, if not create a new one
        loop = asyncio.get_event_loop()
        loop.set_debug(True)
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    global data_stream
    data_stream = StockDataStream(api_key, secret_key)
    
    async def stock_data_stream_handler(data):
        print(data)
        print(type(data))
            
    data_stream.subscribe_bars(stock_data_stream_handler, *symbols)

    data_stream.run()

def additional_function():
    print("Running additional function")
    # Perform tasks here
    time.sleep(5)  # Simulate a task taking some time
    print("Additional function completed")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    while 1:
        threading.Thread(target=consumer_thread).start()
        time.sleep(5)
        loop.run_until_complete(data_stream.stop_ws())

        # Run the additional function in a separate thread
        additional_thread = threading.Thread(target=additional_function)
        additional_thread.start()
        
        # Wait for the additional function to complete
        additional_thread.join()

        time.sleep(20)