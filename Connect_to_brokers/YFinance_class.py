import yfinance as yf
from Broker_class import GetDataAPI

class YFinanceGetData(GetDataAPI):

    def __init__(self, asset_class: str):
        self.asset_class = asset_class

    def get_historical_market_data(self, symbol: list[str], interval: str, start_date: str, end_date: str):

        df = yf.download(symbol, start=start_date, end=end_date, interval=interval)
        df.columns = df.columns.droplevel(1)
        df.reset_index(inplace=True)

        return df
 
        

