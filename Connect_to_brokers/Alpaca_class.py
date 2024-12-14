from Broker_class import TradingAPI, HistoricalDataAPI
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, AssetClass

from alpaca.data import CryptoHistoricalDataClient, StockHistoricalDataClient, OptionHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime

class AlpacaTradingClass(TradingAPI):

    def __init__(self, API_key):
        super().__init__(API_key)

        # paper=True enables paper trading
        self.trading_client = TradingClient(self.API_key[0], self.API_key[1], paper=True)
    
    def place_order(self, symbol: str, quantity: int, order_type: str):

        if order_type == "buy":
            order = OrderSide.BUY
        else:
            order = OrderSide.SELL

        market_order_data = MarketOrderRequest(
                    symbol=symbol,
                    qty=quantity,
                    side=order,
                    time_in_force=TimeInForce.DAY
                    )
        
        # Market order
        market_order = self.trading_client.submit_order(
                order_data=market_order_data
               )
    
class AlpacaGetHistoricalData(HistoricalDataAPI):

    def __init__(self, API_key, asset_class):
        super().__init__(API_key, asset_class)

        if self.asset_class == AssetClass.US_EQUITY:
            self.client = StockHistoricalDataClient(self.API_key[0],  self.API_key[1])
        elif self.asset_class == AssetClass.US_OPTION:
            self.client = OptionHistoricalDataClient(self.API_key[0],  self.API_key[1])
        else:
            self.client = CryptoHistoricalDataClient()

    def get_market_data(self, symbol: list[str], timeframe: str, start_date: str, end_date: str):
        if timeframe == "Min":
            frame = TimeFrame.Minute
        elif timeframe == "Hour":
            frame = TimeFrame.Hour
        elif timeframe == "Day":
            frame = TimeFrame.Day
        elif timeframe == "Week":
            frame = TimeFrame.Week
        else:
            frame = TimeFrame.Month

        request_params = CryptoBarsRequest(
                        symbol_or_symbols=symbol,
                        timeframe=frame,
                        start=datetime(2022, 7, 1),
                        end=datetime(2022, 9, 1)
                 )

        bars = self.client.get_crypto_bars(request_params)

        # convert to dataframe
        bars.df

        # access bars as list - important to note that you must access by symbol key
        # even for a single symbol request - models are agnostic to number of symbols
        bars["BTC/USD"]

    


        

