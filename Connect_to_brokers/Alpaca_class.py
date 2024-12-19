from Broker_class import TradingAPI, GetDataAPI
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, AssetClass

from alpaca.data import CryptoHistoricalDataClient, StockHistoricalDataClient, OptionHistoricalDataClient
from alpaca.data.live import CryptoDataStream, StockDataStream, OptionDataStream
from alpaca.data.requests import CryptoBarsRequest, StockBarsRequest, OptionBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime

class AlpacaTradingClass(TradingAPI):

    def __init__(self, API_key, asset_class: str):
        super().__init__(API_key, asset_class)

        # paper=True enables paper trading
        self.trading_client = TradingClient(self.API_key[0], self.API_key[1], paper=True)

    def get_order_status(self, order_id):
        return None

    def get_assets(self):
        # search for assets
        search_params = GetAssetsRequest(asset_class=self.asset_class)
        return self.trading_client.get_all_assets(search_params)
    
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
        
        return market_order
    
class AlpacaGetData(GetDataAPI):

    def __init__(self, API_key, asset_class: str):
        super().__init__(API_key, asset_class)

        if self.asset_class == AssetClass.US_EQUITY:
            self.client = StockHistoricalDataClient(self.API_key[0],  self.API_key[1])
            self.stream = StockDataStream(self.API_key[0], self.API_key[1])
        elif self.asset_class == AssetClass.US_OPTION:
            self.client = OptionHistoricalDataClient(self.API_key[0],  self.API_key[1])
            self.stream = OptionDataStream(self.API_key[0], self.API_key[1])
        else:
            self.client = CryptoHistoricalDataClient()
            self.stream = CryptoDataStream(self.API_key[0], self.API_key[1])

    def __parse_date(self, date_string):

        date_formats = [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S" 
        ]
        
        for date_format in date_formats:
            try:
                return datetime.strptime(date_string, date_format)
            except ValueError:
                continue  # Try the next format if current one fails
        
        raise ValueError(f"Date string '{date_string}' is not in a recognized format.")
    
    def __convert_interval_to_timeframe(self, interval: str):
        # Map your interval string to the appropriate TimeFrame object
        if interval.lower() == "week":
            return TimeFrame.Week
        elif interval.lower() == "month":
            return TimeFrame.Month
        elif interval.lower() == "hour":
            return TimeFrame.Hour
        elif interval.lower() == "day":
            return TimeFrame.Day
        elif interval.lower() == "minute":
            return TimeFrame.Minute
        else:
            raise ValueError(f"Unsupported interval: {interval}")

    def get_historical_market_data(self, symbol: list[str], interval: str, start_date: str, end_date: str):

        timeframe = self.__convert_interval_to_timeframe(interval)

        if self.asset_class == AssetClass.US_EQUITY:
            stock_request_params = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=timeframe,
                start=self.__parse_date(start_date),
                end=self.__parse_date(end_date)
            )

            bars = self.client.get_stock_bars(stock_request_params)

        elif self.asset_class == AssetClass.US_OPTION:

            option_request_params = OptionBarsRequest(
                symbol_or_symbols=symbol,  # Example option symbol
                timeframe=timeframe,
                start=self.__parse_date(start_date),
                end=self.__parse_date(end_date)
            )

            bars = self.client.get_option_bars(option_request_params)

        else:
            crypto_request_params = CryptoBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=timeframe,
                start=self.__parse_date(start_date),
                end=self.__parse_date(end_date)
            )

            bars = self.client.get_crypto_bars(crypto_request_params)

        # access bars as list - important to note that you must access by symbol key
        # even for a single symbol request - models are agnostic to number of symbols bars["BTC/USD"]

        return bars.df
    
    def get_latest_market_quotes(self, symbol: list[str]):

        # multi symbol request - single symbol is similar
        multisymbol_request_params = StockLatestQuoteRequest(symbol_or_symbols=symbol)

        latest_multisymbol_quotes = self.client.get_stock_latest_quote(multisymbol_request_params)

        return latest_multisymbol_quotes
    
    # async handler
    async def __quote_data_handler(self, data):
            # quote data will arrive here
            print(data)
    
    def get_live_market_data(self, symbol: list[str], timeframe: str):

        # Works only for 1 symbol
        self.stream.subscribe_quotes(self.__quote_data_handler, symbol)

        # Doesn't work when market is closed
        self.stream.run()
        

    


        

