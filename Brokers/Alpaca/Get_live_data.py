import os
import pandas as pd

from alpaca.data.live.stock import StockDataStream
from Brokers.Alpaca.Alpaca_keyes import API_KEY, SECRET_KEY

def delete_csv_if_exists(file_path):
    # Check if the file exists
    if os.path.exists(file_path):
            os.remove(file_path)
            

#file_name = 'Data/live_data.csv'
#delete_csv_if_exists(file_name)
i = 1

api_key = API_KEY
secret_key = SECRET_KEY

symbol = "TSLA"

stock_data_stream_client = StockDataStream(api_key, secret_key)
data_stream_list = []

async def stock_data_stream_handler(bar):
    global data_stream_list
    # Testing 
    global i
    data = {
        'timestamp': [bar.timestamp],
        'open': [bar.open],
        'high': [bar.high],
        'low': [bar.low],
        'close': [bar.close],
        'volume': [bar.volume]
    }
    data_stream_list.append(data)
    df = pd.DataFrame(data_stream_list)

    file_name = f"Data/live_data_{i}.csv"
    df.to_csv(file_name, index=False)  


symbols = [symbol]

stock_data_stream_client.subscribe_bars(stock_data_stream_handler, *symbols)

stock_data_stream_client.run()
