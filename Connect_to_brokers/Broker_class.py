from abc import ABC, abstractmethod

class OrderType:
    BUY = "buy"
    SELL = "sell"

class TradingAPI(ABC):

    def __init__(self, API_key: list[str]):
        self.API_key = API_key
    
    @abstractmethod
    def place_order(self, symbol: str, quantity: int, order_type: str):
        pass
    
    @abstractmethod
    def get_order_status(self, order_id: str):
        pass

class HistoricalDataAPI(ABC):
    def __init__(self, API_key: list[str], asset_class: str):
        self.API_key = API_key
        self.asset_class = asset_class
    
    @abstractmethod
    def get_market_data(self, symbol: list[str]):
        pass
