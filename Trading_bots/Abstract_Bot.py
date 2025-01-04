from abc import ABC, abstractmethod

# Try to implement these methods. For this first implement the DRL bot and see what are the methods I can already 
# implement here (remove @abstractmethod for implementing a method in the abstract class) and the ones I need to 
# implement in the code of the corresponding bot.

# See https://academy.ftmo.com/lesson/how-to-backtest-trading-strategies/#:~:text=Backtesting%20is%20the%20process%20of,10%20or%2020%20years%20back.
# for all the methods which I could implement

class AbstractBot(ABC):

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def run_strat(self):
        pass
    
    @abstractmethod
    def __get_entry_price(self):
        pass

    @abstractmethod
    def __get_stop_loss(self):
        pass

    @abstractmethod
    def __get_take_profit(self):
        pass

    @abstractmethod
    def __get_exit_price(self):
        pass

    @abstractmethod
    def __get_exit_pattern(self):
        pass

    @abstractmethod
    def __MAE_and_MFE(self):
        # See code in EasyBot
        pass

    @abstractmethod
    def backtesting(self):
        pass