from abc import ABC, abstractmethod

class TradingAPI(ABC):

    def __init__(self, API_key: list[str], asset_class: str):
        self.API_key = API_key
        self.asset_class = asset_class
    
    @abstractmethod
    def place_order(self, symbol: str, quantity: int, order_type: str):
        pass
    
    @abstractmethod
    def get_order_status(self, order_id: str):
        pass

class GetDataAPI(ABC):
    def __init__(self, API_key: list[str], asset_class: str):
        self.API_key = API_key
        self.asset_class = asset_class
    
    @abstractmethod
    def get_historical_market_data(self, symbol: list[str], timeframe: str, start_date: str, end_date: str):
        pass

    @abstractmethod
    def get_live_market_data(self, symbol: list[str], timeframe: str):
        pass
