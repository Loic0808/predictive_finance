from alpaca.data.live import StockDataStream
from alpaca.data import CryptoHistoricalDataClient, StockHistoricalDataClient, OptionHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta

api_key = "PKAG0XBVFXJPXPXBWPGW"
secret_key = "pjp69zCQBSUziTzXEjZ9DagW04sni7Jg99QKH6TH"


# no keys required for crypto data
client = StockHistoricalDataClient(api_key, secret_key)

end_time = datetime.now() - timedelta(hours=1, minutes=20)

request_params = StockBarsRequest(
                        symbol_or_symbols=["MSFT"],
                        timeframe=TimeFrame.Minute,
                        start=datetime(2024, 12, 19, 17, 00),
                        end=end_time
                 )

bars = client.get_stock_bars(request_params)

# convert to dataframe
print(bars.df)

wss_client = StockDataStream(api_key, secret_key)

# async handler
last_print_time = None

# Async handler
async def quote_data_handler(data):
    global last_print_time

    current_time = datetime.now()
    
    if last_print_time is None or current_time - last_print_time >= timedelta(minutes=1):
        print(data)
        last_print_time = current_time

wss_client.subscribe_quotes(quote_data_handler, "MSFT")

wss_client.run()

# Data  looks like 
# symbol='MSFT' timestamp=datetime.datetime(2024, 12, 19, 17, 55, 10, 400383, tzinfo=datetime.timezone.utc) bid_price=408.0 bid_size=1.0 bid_exchange='V' ask_price=445.0 ask_size=1.0 ask_exchange='V' conditions=['R'] tape='C'


wss_client.stop()
    
wss_client.close()
