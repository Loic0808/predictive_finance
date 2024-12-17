from abc import ABC, abstractmethod

"""
For each Broker define the corresponding column names
"""

class ColumnNamesBrokers(ABC):
    @abstractmethod
    def set_column_names(self):
        pass

class ColumnNamesAlpaca(ColumnNamesBrokers):

    def set_column_names(self):
        self.HIGH = "high"
        self.LOW = "low"
        self.OPEN = "open"
        self.CLOSE = "close"

class ColumnNamesYfinance(ColumnNamesBrokers):
    def set_column_names(self):
        self.HIGH = "High"
        self.LOW = "Low"
        self.OPEN = "Open"
        self.CLOSE = "Close"
        self.ADJ_CLOSE = "Adj Close"