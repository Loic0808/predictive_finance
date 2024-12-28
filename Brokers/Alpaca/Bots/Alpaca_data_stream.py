from Alpaca_keyes import API_KEY, SECRET_KEY
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest

from Indicators import EMA, ATR

api_key = API_KEY
secret_key = SECRET_KEY

symbol = "TSLA"

stock_historical_data_client = StockHistoricalDataClient(api_key, secret_key)

# Finish using test_prepare_data_bot