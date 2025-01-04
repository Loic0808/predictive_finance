import pandas as pd
import numpy as np

from Backtesting.Backtesting import BacktestColumnNames

class ColumnNames:
    HIGH = "high"
    LOW = "low"
    OPEN = "open"
    CLOSE = "close"
    EMA_50 = "EMA_50"
    TIMESTAMP = "timestamp"


class EasyBot:
    def __init__(self, bank_account, stock_qty, df) -> None:
        self.bank_account = bank_account
        self.qty = stock_qty
        self.columns = df.columns

        self.backtesting_columns = [
            BacktestColumnNames.TIMESTAMP_BUY,
            BacktestColumnNames.ENTRY_PRICE,
            BacktestColumnNames.STOP_LOSS,
            BacktestColumnNames.TAKE_PROFIT,
            BacktestColumnNames.STOCKS_TRADED,
            BacktestColumnNames.EXIT_PRICE,
            BacktestColumnNames.EXIT_PATTERN,
            BacktestColumnNames.MAX_PRICE,
            BacktestColumnNames.MIN_PRICE,
        ]
        self.backtesting = pd.DataFrame(columns=self.backtesting_columns)
        self.backtesting = self.backtesting.astype(
            {
                BacktestColumnNames.TIMESTAMP_BUY: 'datetime64[ns]',
                BacktestColumnNames.ENTRY_PRICE: float,
                BacktestColumnNames.STOP_LOSS: float,
                BacktestColumnNames.TAKE_PROFIT: float,
                BacktestColumnNames.STOCKS_TRADED: int,
                BacktestColumnNames.EXIT_PRICE: float,
                BacktestColumnNames.EXIT_PATTERN: str,
                BacktestColumnNames.MAX_PRICE: float,
                BacktestColumnNames.MIN_PRICE: float,
            }
        )
        self.log_info = []

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
        mean_abs_diff = df["AbsDiff"].iloc[-10:].mean()  # :50

        if self.len_high_point_candle >= 3 * mean_abs_diff:
            return True

        return False

    def __buy(self, df):
        """The body of the candle needs to close above the swing high point"""
        self.close_buy = df[ColumnNames.CLOSE].iloc[-1]
        self.stop_loss = df["Chandelier_Exit_Short"].iloc[-1]
        timestamp_buy = df[ColumnNames.TIMESTAMP].iloc[-1]

        range = np.abs(self.close_buy - self.stop_loss)
        self.take_profit = self.close_buy + 2 * range

        if self.close_buy >= self.high_point:
            self.buy_info = [
                timestamp_buy,
                self.close_buy,
                self.stop_loss,
                self.take_profit,
                self.qty,
            ]
            return True
        return False

    def __stop_loss_f(self, df):
        """When to sell stock to limit the loss"""
        if df[ColumnNames.CLOSE].iloc[-1] < self.stop_loss:
            self.buy_info.append(df[ColumnNames.CLOSE].iloc[-1])
            self.buy_info.append("stop-loss hit")
            return True
        return False

    def __take_profit_target(self, df):
        """Take profit function"""
        if df[ColumnNames.HIGH].iloc[-1] >= self.take_profit:
            self.buy_info.append(df[ColumnNames.CLOSE].iloc[-1])
            self.buy_info.append("take profit hit")
            return True
        return False

    def __backtesting(self):
        new_data = pd.DataFrame([self.buy_info], columns=self.backtesting_columns)
        self.backtesting = pd.concat([self.backtesting, new_data], ignore_index=True)

    def __steps(self, df):
        if self.step_1 and self.__price_below_EMA(df):
            self.log_info.append("price below EMA")
            self.step_1 = False

        if self.step_2 and not self.step_1 and self.__strategy_start(df):
            self.log_info.append("strategy start")
            self.step_2 = False

        if self.step_3 and not self.step_2 and self.__pullback(df):
            self.log_info.append("pullback")
            self.step_3 = False
            self.high_point, self.len_high_point_candle = (
                self.__get_swing_high_point_before_pullback(df)
            )

        if self.buy_bool and not self.step_3 and self.__invalid_trade_1(df):
            self.log_info.append("Invalid trade1")
            self.buy_bool = False
            # Start over
            return "invalid1"

        if self.buy_bool and not self.step_3 and self.__invalid_trade_2(df):
            self.log_info.append("Invalid trade2")
            self.buy_bool = False
            # Start over
            return "invalid2"

        if self.buy_bool and not self.step_3 and self.__buy(df):
            self.log_info.append("buy")
            self.bank_account -= self.qty * df[ColumnNames.OPEN].iloc[-1]
            self.buy_bool = False
            return "buy"

        return "hold"

    def __trading_strategy(self, df):
        if self.__stop_loss_f(df):
            self.log_info.append("sell and loose small amount")
            self.bank_account += self.qty * df[ColumnNames.OPEN].iloc[-1]
            return "sell1"

        if self.__take_profit_target(df):
            self.log_info.append("sell and make profit")
            self.bank_account += self.qty * df[ColumnNames.OPEN].iloc[-1]
            return "sell2"

        else:
            return 0
        
    def __MAE_and_MFE(self, df, res):
        self.max_price = max(self.max_price, df[ColumnNames.HIGH].iloc[-1])
        self.min_price = min(self.min_price, df[ColumnNames.LOW].iloc[-1])

        if res == "sell1" or res == "sell2":
            self.buy_info.append(self.max_price)
            self.buy_info.append(self.min_price)

    def __reinitialize_variables(self) -> None:
        self.step_1 = True
        self.step_2 = True
        self.step_3 = True

        self.max_price = -np.inf
        self.min_price = np.inf

        self.strat = False
        self.buy_bool = True

        self.high_point = np.inf
        self.len_high_point_candle = 0

        self.available_df = pd.DataFrame(self.columns)
        self.buy_info = []

    def run_strat(self, df):
        self.__reinitialize_variables()
        for index, row in df.iterrows():
            row_df = pd.DataFrame([row])
            self.available_df = pd.concat([self.available_df, row_df])
            self.log_info.append(self.bank_account)

            if len(self.available_df) >= 3:
                res = self.__steps(self.available_df)
                if not self.strat and (res == "invalid1" or res == "invalid2"):
                    self.__reinitialize_variables()
                elif not self.strat and res == "buy":
                    self.strat = True
                    continue  # Go directly to next candle

                if self.strat:
                    res = self.__trading_strategy(self.available_df)
                    self.__MAE_and_MFE(self.available_df, res)
                    if res == "sell1" or res == "sell2":
                        self.__backtesting()
                        self.__reinitialize_variables()
                        self.strat = False
                    else:
                        continue
