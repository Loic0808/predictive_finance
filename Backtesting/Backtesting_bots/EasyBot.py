import pandas as pd
import numpy as np

class ColumnNames:
    HIGH = "high"
    LOW = "low"
    OPEN = "open"
    CLOSE = "close"
    EMA_50 = "EMA_50"

class EasyBot():

    def __init__(self, bank_account, df) -> None:
        self.bank_account = bank_account
        self.columns = df.columns

        self.backtesting = pd.DataFrame()

    def __price_below_EMA(self, df) -> bool:
        """ Is True if price is below 50 day EMA  """

        open = df[ColumnNames.OPEN].iloc[-1]
        close = df[ColumnNames.CLOSE].iloc[-1]
        EMA_50 = df[ColumnNames.EMA_50].iloc[-1]

        if open >= EMA_50 and close <= EMA_50:
            return True
        
        return False

    def __strategy_start(self, df) -> bool:
        """ Strategy starts once the price is above EMA and a candle closes above it """

        open = df[ColumnNames.OPEN].iloc[-1]
        close = df[ColumnNames.CLOSE].iloc[-1]
        EMA_50 = df[ColumnNames.EMA_50].iloc[-1]

        if close >= EMA_50 and open >= EMA_50:
            return True
        
        return False

    def __pullback(self, df) -> bool:
        """ We consider a Pullback when we have at least 2 opposite candles coming down """
        bool1 = (df[ColumnNames.OPEN].iloc[-1] - df[ColumnNames.CLOSE].iloc[-1] > 0)
        bool2 = (df[ColumnNames.OPEN].iloc[-2] - df[ColumnNames.CLOSE].iloc[-2] > 0)

        # We add this condition which says that the candles must have a certain length
        bool3 = (df[ColumnNames.OPEN].iloc[-2] - df[ColumnNames.CLOSE].iloc[-1] >= 0.8*np.abs(df[ColumnNames.CLOSE].iloc[-3] - df[ColumnNames.OPEN].iloc[-3]))

        if bool1 and bool2 and bool3:
            return True
        
        return False

    def __get_swing_high_point_before_pullback(self, df):
        """Gets high point before pullback"""

        self.high_point = df[ColumnNames.HIGH].iloc[-3]

        self.len_high_point_candle = df[ColumnNames.CLOSE].iloc[-3] - df[ColumnNames.OPEN].iloc[-3]

        return self.high_point, self.len_high_point_candle

    def __invalid_trade_1(self, df) -> bool:
        """If the prices closes below the EMA after the pullback then the trade is invalid"""

        if df[ColumnNames.CLOSE].iloc[-1] < df[ColumnNames.EMA_50].iloc[-1]:
            # Trade is invalid
            return True
        # Trade is valid
        return False

    def __invalid_trade_2(self, df):
        """If the breakcoutcandle is 3 or 4 times bigger than the mean hight of candles before, then the trade is invalid"""

        df['AbsDiff'] = (df[ColumnNames.CLOSE] - df[ColumnNames.OPEN]).abs()
        mean_abs_diff = df['AbsDiff'].iloc[-10:].mean() # :50

        if self.len_high_point_candle >= 3*mean_abs_diff:
            return True
        
        return False

    def __buy(self, df):
        """The body of the candle needs to close above the swing high point"""
        self.close_buy = df[ColumnNames.CLOSE].iloc[-1]
        self.stop_loss = df['Chandelier_Exit_Short'].iloc[-1]

        if self.close_buy >= self.high_point:
            self.buy_info = [self.close_buy, self.stop_loss]
            return True
        return False

    def __stop_loss_f(self, df):
        """ When to sell stock to limit the loss """
        if df[ColumnNames.CLOSE].iloc[-1] < self.stop_loss:
            self.buy_info.append(df[ColumnNames.CLOSE].iloc[-1])
            return True
        return False

    def __take_profit_target(self, df):
        """Take profit function"""
        range = np.abs(self.close_buy - self.stop_loss)
        if df[ColumnNames.HIGH].iloc[-1] >= self.close_buy + 2*range:
            self.buy_info.append(df[ColumnNames.CLOSE].iloc[-1])
            return True
        return False
    
    def __backtesting(self):
        new_data = pd.DataFrame(self.buy_info, columns=['Close_price_buy', 'Stop_loss', 'Close_price_sell'])

        # Step 4: Append the new data to the empty DataFrame
        self.backtesting = pd.concat([self.backtesting, new_data], ignore_index=True)

    def __steps(self, df):

        if self.step_1 and self.__price_below_EMA(df):
            print("price below EMA")
            self.step_1 = False

        if self.step_2 and not self.step_1 and self.__strategy_start(df):
            print("strategy start")
            self.step_2 = False
            
        if self.step_3 and not self.step_2 and self.__pullback(df):
            print("pullback")
            self.step_3 = False
            self.high_point, self.len_high_point_candle = self.__get_swing_high_point_before_pullback(df)

        if not self.step_3 and self.__invalid_trade_1(df): 
            print("Invalid trade1")
            # Start over
            return "invalid1"
            
        if not self.step_3 and self.__invalid_trade_2(df):
            print("Invalid trade2")
            # Start over
            return "invalid2"

        if not self.step_3 and self.__buy(df):
            self.buy_bool = True
            return "buy"
            
        return "hold"
    
    def __trading_strategy(self, df, qty):

        if self.buy_bool:
            print("BUY")
            self.bank_account -= qty*df[ColumnNames.OPEN].iloc[-1]
            self.buy_bool = False
            return 0
        
        # Implement the stop loss functions here
        if self.__stop_loss_f(df):
            print("sell and loose small amount")
            self.bank_account += qty*df[ColumnNames.OPEN].iloc[-1]
            return "sell1"

        if self.__take_profit_target(df):
            print("sell and make profit")
            self.bank_account += qty*df[ColumnNames.OPEN].iloc[-1]
            return "sell2"
        
        else:
            return 0
    

    def __reinitialize_variables(self) -> None:
        self.step_1 = True
        self.step_2 = True
        self.step_3 = True

        self.strat = False
        self.buy_bool = False

        self.high_point = np.inf
        self.len_high_point_candle = 0

        self.is_buy = False
        self.available_df = pd.DataFrame(self.columns)
        self.buy_info = []

    def run_strat(self, df):
        self.__reinitialize_variables()
        for index, row in df.iterrows():
            row_df = pd.DataFrame([row])
            self.available_df = pd.concat([self.available_df, row_df])
            print(self.bank_account)

            if len(self.available_df) >= 3:
                res = self.__steps(self.available_df)
                if not self.strat and (res == "invalid1" or res ==  "invalid2"):
                    self.__reinitialize_variables()
                elif not self.strat and res == "buy":
                    self.strat = True
                    # We buy the asset and then go to the next candle and wait until we get a sell signal
                    res = self.__trading_strategy(self.available_df, 100)
                    continue # Go directly to next candle

                if self.strat:         
                    res = self.__trading_strategy(self.available_df, 100)
                    if res == "sell1" or res == "sell2":
                        self.__backtesting()
                        self.__reinitialize_variables()
                        self.strat = False
                    else:
                        continue