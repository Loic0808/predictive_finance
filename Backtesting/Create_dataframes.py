from datetime import datetime

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest

class CreateDataframe():
    """
    Class which allows to create historical dataframes
    """
    def Alpaca(
        self,
        api_key,
        secret_key,
        start_date: datetime,
        end_date: datetime,
        interval: datetime,
        asset_list: list[str],
    ):
        """
        start_date: Date on which we start testing the strategy
        end_date: Date on which we stop testing the strategy
        interval: Interval of the incomming data (e.g., 1 min, 15 min, 4 hours, ...)
        asset_list: List of assets on which we test the strategy
        """

        historical_data_client = StockHistoricalDataClient(api_key, secret_key)

        req = StockBarsRequest(
            symbol_or_symbols=asset_list,
            timeframe=interval,
            start=start_date,
            end=end_date,
        )

        df = historical_data_client.get_stock_bars(req).df
        df = df.reset_index()
        if df.empty:
            return df

        df = df.drop(["symbol", "trade_count", "vwap"], axis=1)

        return df