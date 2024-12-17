import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from Connect_to_brokers.ColumnNames import ColumnNamesBrokers
from Connect_to_brokers.Broker_class import TradingAPI, GetDataAPI
from Helper_functions.Column_names import ColumnNamesFuntions

class EasyBot():

    """
    1) Initialize the date/time when the class object is created
    2) Fetch data corresponding to that time (we fetch 50 days since we use the 50 day moving average. Probalby we don't need to fetch the data in 15 min intervals)
    3) Every unit of time (15 min, 1 hour, etc) we consider the new input data and we append it to our current
       dataframe

    Eventually:
    4) Once I have this, I can do the following: Look at all signs which indicate to buy before hte current date. If the last buy signal has not happened yet then we can use the past
    data, we basically land in the middle of the strategy. Maybe this is not even needed if the bot starts with the market.
    5) In the future maybe create a python file where all the data is stored, historical data and so, so that I don't need to load the data inside each class
    """

    def __init__(self, trading_api: TradingAPI, load_data: GetDataAPI, column_names: ColumnNamesBrokers, API_key: list[str]) -> None:

        self.trading_api = trading_api
        self.load_data = load_data
        self.API_key = API_key
        self.column_names = column_names

    # Will be private method in the future, connected to client info directly
    def get_client_data(self, trading_asset: str, symbol: str, bank_account, time_frame: str = "15Min"):
        self.trading_asset = trading_asset # Stocks, options or crypto
        self.symbol = symbol
        self.time_frame = time_frame
        self.bank_account = bank_account

    def __get_nearest_15_min_datetime(t):
        rounded_minutes = (t.minute // 15) * 15
        new_t = t.replace(minute=rounded_minutes, second=0, microsecond=0)
    
        return new_t

    def __initialize_dataframe(self) -> None:
        self.current_time = datetime.now()
        start_date = self.current_time - timedelta(days=60)
        self.df = self.load_data.get_historical_market_data(
            self.symbol,
            self.time_frame, 
            start_date,
            self.__get_nearest_15_min_datetime(self.current_time)
        )

        self.columns = self.df.columns

    def __price_below_EMA(self) -> bool:
        """ Is True if price is below 50 day EMA  """

        open = self.df[self.column_names.OPEN].iloc[-1]
        close = self.df[self.column_names.CLOSE].iloc[-1]
        EMA_50 = self.df[ColumnNamesFuntions.EMA_50].iloc[-1]

        if open >= EMA_50 and close <= EMA_50:
            return True
        
        return False

    def __strategy_start(self) -> bool:
        """ Strategy starts once the price is above EMA and a candle closes above it """

        open = self.df[self.column_names.OPEN].iloc[-1]
        close = self.df[self.column_names.CLOSE].iloc[-1]
        EMA_50 = self.df[ColumnNamesFuntions.EMA_50].iloc[-1]

        if close >= EMA_50 and open >= EMA_50:
            return True
        
        return False

    def __pullback(self) -> bool:
        """ We consider a Pullback when we have at least 2 opposite candles coming down """
        bool1 = (self.df[self.column_names.OPEN].iloc[-1] - self.df[self.column_names.CLOSE].iloc[-1] > 0)
        bool2 = (self.df[self.column_names.OPEN].iloc[-2] - self.df[self.column_names.CLOSE].iloc[-2] > 0)

        # We add this condition which says that the candles must have a certain length
        bool3 = (self.df[self.column_names.OPEN].iloc[-2] - self.df[self.column_names.CLOSE].iloc[-1] >= 0.8*np.abs(self.df[self.column_names.CLOSE].iloc[-3] - self.df[self.column_names.OPEN].iloc[-3]))

        if bool1 and bool2 and bool3:
            return True
        
        return False

    def __get_swing_high_point_before_pullback(self):
        """Gets high point before pullback"""

        self.high_point = self.df.High.iloc[-3]

        self.len_high_point_candle = self.df[self.column_names.CLOSE].iloc[-3] - self.df[self.column_names.OPEN].iloc[-3]

        return self.high_point, self.len_high_point_candle

    def __invalid_trade_1(self) -> bool:
        """If the prices closes below the EMA after the pullback then the trade is invalid"""

        if self.df[self.column_names.CLOSE].iloc[-1] < self.df[ColumnNamesFuntions.EMA_50].iloc[-1]:
            # Trade is invalid
            return True
        # Trade is valid
        return False

    def __invalid_trade_2(self):
        """If the breakcoutcandle is 3 or 4 times bigger than the mean hight of candles before, then the trade is invalid"""

        self.df['AbsDiff'] = (self.df[self.column_names.CLOSE] - self.df[self.column_names.OPEN]).abs()
        mean_abs_diff = self.df['AbsDiff'].iloc[:50].mean()

        if self.len_high_point_candle >= 3*mean_abs_diff:
            return True
        
        return False

    def __buy(self):
        """The body of the candle needs to close above the swing high point"""
        self.close_buy = self.df[self.column_names.CLOSE].iloc[-1]
        self.stop_loss = self.df['Chandelier_Exit_Short'].iloc[-1]

        if self.close_buy >= self.high_point:
            return True, self.close_buy, self.stop_loss
        
        return False, 0, 0

    def __stop_loss_f(self):
        """ When to sell stock to limit the loss """
        if self.df[self.column_names.CLOSE].iloc[-1] < self.stop_loss:
            return True
        return False

    def __take_profit_target(self):
        """Take profit function"""
        range = np.abs(self.close_buy - self.stop_loss)
        if self.df.High.iloc[-1] >= self.close_buy + 2*range:
            return True
        return False

    def __steps(self):

        if self.step_1 and self.__price_below_EMA(self.df):
            print("price below EMA")
            self.step_1 = False

        if self.step_2 and not self.step_1 and self.__strategy_start(self.df):
            print("strategy start")
            self.step_2 = False
            
        if self.step_3 and not self.step_2 and self.__pullback(self.df):
            print("pullback")
            self.step_3 = False
            self.high_point, self.len_high_point_candle = self.__get_swing_high_point_before_pullback(self.df)

        if not self.is_buy and not self.step_3 and self.__invalid_trade_1(self.df): 
            print("Invalid trade1")
            # Start over
            return "invalid1"
            
        if not self.is_buy and not self.step_3 and self.__invalid_trade_2(self.df):
            print("Invalid trade2")
            # Start over
            return "invalid2"

        if not self.is_buy and not self.step_3:
            self.is_buy, self.close_buy, self.stop_loss = self.__buy(self.df)
            if self.is_buy:
                return "buy"
            
        return "hold"
    
    def __trading_strategy(self):

        if self.buy_bool:
            print("BUY")
            self.bank_account -= 100*self.df[self.column_names.OPEN].iloc[-1]
            self.buy_bool = False
            return 0
        
        # Implement the stop loss functions here
        if self.__stop_loss_f():
            print("sell and loose small amount")
            self.bank_account += 100*self.df[self.column_names.OPEN].iloc[-1]
            return "sell1"

        if self.__take_profit_target():
            print("sell and make profit")
            self.bank_account += 100*self.df[self.column_names.OPEN].iloc[-1]
            return "sell2"
        
        else:
            return 0
    

    def __reinitialize_variables(self) -> None:
        self.step_1 = True
        self.step_2 = True
        self.step_3 = True

        self.strat = False
        self.buy_bool = True

        self.high_point = None
        self.len_high_point_candle = None
        self.close_buy = None
        self.stop_loss = None 

        self.is_buy = False

    def run_strat(self):
        self.__reinitialize_variables()

        self.__initialize_dataframe()

        self.available_df = pd.DataFrame(self.columns)

        # Every 15 min read the new dataframe, probably faster if I append only the newest row
        for index, row in self.df.iterrows():
            row_df = pd.DataFrame([row])
            self.available_df = pd.concat([self.available_df, row_df])
            print(self.bank_account)

            if len(self.available_df) >= 3:
                res = self.__steps(self.available_df)
                if not self.strat and (res == "invalid1" or res ==  "invalid2"):
                    self.__reinitialize_variables()
                elif not self.strat and res == "buy":
                    self.strat = True
                    continue # Go directly to next candle

                if self.strat:         
                    res = self.__trading_strategy(self.available_df)
                    if res == "sell1" or res == "sell2":

                        self.__reinitialize_variables()
                        self.strat = False
                    else:
                        continue