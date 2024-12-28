from alpaca.trading.requests import (
    MarketOrderRequest,
    StopLossRequest,
    TakeProfitRequest,
)
from alpaca.trading.enums import OrderClass, OrderSide, TimeInForce

import numpy as np


# In a later step create abstract classes for the column names
class ColumnNamesYF:
    HIGH = "High"
    LOW = "Low"
    OPEN = "Open"
    CLOSE = "Close"
    ADJ_CLOSE = "Adj Close"
    EMA_50 = "EMA_50"


class ColumnNames:
    HIGH = "high"
    LOW = "low"
    OPEN = "open"
    CLOSE = "close"
    EMA_50 = "EMA_50"


class EasyBot:
    """
    A later task will be to implement a general class for all different brokers where tradingclient is an
    abstract class.
    """

    def __init__(self, symbol, trading_client) -> None:
        self.symbol = symbol
        self.trading_client = trading_client

    def __price_below_EMA(self, df) -> bool:
        """Is True if price is below 50 day EMA"""

        open = df[ColumnNames.OPEN].iloc[-1]
        close = df[ColumnNames.CLOSE].iloc[-1]
        EMA_50 = df[ColumnNames.EMA_50].iloc[-1]

        if open >= EMA_50 and close <= EMA_50:
            return True

        return False

    def __strategy_start(self, df) -> bool:
        """Strategy starts once the price is above EMA and a candle closes above it"""

        open = df[ColumnNames.OPEN].iloc[-1]
        close = df[ColumnNames.CLOSE].iloc[-1]
        EMA_50 = df[ColumnNames.EMA_50].iloc[-1]

        if close >= EMA_50 and open >= EMA_50:
            return True

        return False

    def __pullback(self, df) -> bool:
        """We consider a Pullback when we have at least 2 opposite candles coming down"""
        bool1 = df[ColumnNames.OPEN].iloc[-1] - df[ColumnNames.CLOSE].iloc[-1] > 0
        bool2 = df[ColumnNames.OPEN].iloc[-2] - df[ColumnNames.CLOSE].iloc[-2] > 0

        # We add this condition which says that the candles must have a certain length
        bool3 = df[ColumnNames.OPEN].iloc[-2] - df[ColumnNames.CLOSE].iloc[
            -1
        ] >= 0.8 * np.abs(
            df[ColumnNames.CLOSE].iloc[-3] - df[ColumnNames.OPEN].iloc[-3]
        )

        if bool1 and bool2 and bool3:
            return True

        return False

    def __get_swing_high_point_before_pullback(self, df):
        """Gets high point before pullback"""

        self.high_point = df[ColumnNames.HIGH].iloc[-3]

        self.len_high_point_candle = (
            df[ColumnNames.CLOSE].iloc[-3] - df[ColumnNames.OPEN].iloc[-3]
        )

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

        df["AbsDiff"] = (df[ColumnNames.CLOSE] - df[ColumnNames.OPEN]).abs()
        mean_abs_diff = df["AbsDiff"].iloc[:50].mean()

        if self.len_high_point_candle >= 3 * mean_abs_diff:
            return True

        return False

    def __buy(self, df):
        """The body of the candle needs to close above the swing high point"""
        close_buy = df[ColumnNames.CLOSE].iloc[-1]
        stop_loss = df["Chandelier_Exit_Short"].iloc[-1]

        range = np.abs(close_buy - stop_loss)

        if self.close_buy >= self.high_point:
            req = MarketOrderRequest(
                symbol=self.symbol,
                qty=5,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY,
                order_class=OrderClass.BRACKET,
                take_profit=TakeProfitRequest(limit_price=close_buy + 2 * range),
                stop_loss=StopLossRequest(stop_price=stop_loss),
            )
            self.trading_client.submit_order(req)
            return True

        return False

    def __steps(self, df):
        if self.step_1 and self.__price_below_EMA(df):
            # Put a logging instead of a print
            print("Price below EMA")
            self.step_1 = False

        if self.step_2 and not self.step_1 and self.__strategy_start(df):
            print("strategy start")
            self.step_2 = False

        if self.step_3 and not self.step_2 and self.__pullback(df):
            print("pullback")
            self.step_3 = False
            self.high_point, self.len_high_point_candle = (
                self.__get_swing_high_point_before_pullback(df)
            )

        if not self.step_3 and self.__invalid_trade_1(df):
            print("Invalid trade1")
            # Start over
            return "invalid1"

        if not self.step_3 and self.__invalid_trade_2(df):
            print("Invalid trade2")
            # Start over
            return "invalid2"

        if self.__buy(df) and not self.step_3:
            return "buy"

        return "hold"

    def __reinitialize_variables(self) -> None:
        self.step_1 = True
        self.step_2 = True
        self.step_3 = True

        self.high_point = None
        self.len_high_point_candle = None
        self.close_buy = None
        self.stop_loss = None

        self.is_buy = False

    def run_strat(self, start, available_df):
        # I need to initialize the variables but only once!
        if start:
            self.__reinitialize_variables()

        if len(available_df) >= 3:
            res = self.__steps(available_df)
            if res == "invalid1" or res == "invalid2":
                self.__reinitialize_variables()
                # Here I also need to reinitialize the availale data -> do a separate class for this
            elif res == "buy":
                self.__reinitialize_variables()


"""
Things to add:
print bank account value
"""
