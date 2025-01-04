from datetime import datetime

from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest


# This Backtesting class is only build on the Alpaca Broker for now
class BacktestColumnNames:
    TIMESTAMP_BUY = "Timestamp_buy"
    ENTRY_PRICE = "Entry_price"
    STOP_LOSS = "Stop_loss"
    TAKE_PROFIT = "Take_profit"
    EXIT_PRICE = "Exit_price"
    STOCKS_TRADED = "Stocks_traded"
    EXIT_PATTERN = "Exit_pattern"
    MAX_PRICE = "Max_price_during_trade"
    MIN_PRICE = "Min_price_during_trade"
    PROFIT_LOSS = "profit/loss"
    MAE = "MAE"
    MFE = "MFE"
    REWARD_TO_RISK = "Reward_to_risk"
    MONETARY_GAIN = "Monetary_gain"


class Backtesting:
    """
    The backtesting class will test the trading bot on two types of data:

    -In-Sample Data: This is the portion of historical data used to develop, optimise, and fine-tune
     the trading strategy. During this phase, we adjust parameters and test different variations
     to improve the strategy’s performance. The risk with in-sample data is overfitting, where the
     strategy becomes too closely tailored to the historical data and may not perform well in new,
     unseen data.
    -Out-of-Sample Data: This is a separate set of historical data that was not used during the
     backtesting and/or optimisation process. It is reserved for testing the strategy after development
     to ensure that it performs well under different market conditions.
    """

    def __init__(
        self,
        # historical_data_client, not needed for now
    ):
        """
        historical_data_client: Data client to retrieve stocks, options or crypto
        """
        pass

    def create_dataframe(
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
        trading_bot: Trading strategy
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

    def run_bot(self, trading_bot, df):
        self.trading_bot = trading_bot
        self.trading_bot.run_strat(df)
        self.backtest_df = self.trading_bot.backtesting
        self.log_info_list = self.trading_bot.log_info
        return self.backtest_df, self.log_info_list

    def calculate_profit_and_loss(self, df, trade_type: str):
        if trade_type == "long":
            df[BacktestColumnNames.PROFIT_LOSS] = (
                df[BacktestColumnNames.EXIT_PRICE] - df[BacktestColumnNames.ENTRY_PRICE]
            )
        else:
            df[BacktestColumnNames.PROFIT_LOSS] = (
                df[BacktestColumnNames.ENTRY_PRICE] - df[BacktestColumnNames.EXIT_PRICE]
            )
        return df

    def calculate_MAE_MFE(self, df, trade_type: str):
        if trade_type == "long":
            df[BacktestColumnNames.MAE] = (
                df[BacktestColumnNames.ENTRY_PRICE] - df[BacktestColumnNames.MIN_PRICE]
            )
            df[BacktestColumnNames.MFE] = (
                df[BacktestColumnNames.MAX_PRICE] - df[BacktestColumnNames.ENTRY_PRICE]
            )
        else:
            df[BacktestColumnNames.MAE] = (
                df[BacktestColumnNames.MAX_PRICE] - df[BacktestColumnNames.ENTRY_PRICE]
            )
            df[BacktestColumnNames.MFE] = (
                df[BacktestColumnNames.ENTRY_PRICE] - df[BacktestColumnNames.MIN_PRICE]
            )
        return df

    def calculate_risk_to_reward(self, df, trade_type: str):
        if trade_type == "long":
            df[BacktestColumnNames.REWARD_TO_RISK] = (
                df[BacktestColumnNames.EXIT_PRICE] - df[BacktestColumnNames.ENTRY_PRICE]
            ) / (
                df[BacktestColumnNames.ENTRY_PRICE] - df[BacktestColumnNames.STOP_LOSS]
            )
        else:
            df[BacktestColumnNames.REWARD_TO_RISK] = (
                df[BacktestColumnNames.ENTRY_PRICE] - df[BacktestColumnNames.EXIT_PRICE]
            ) / (
                df[BacktestColumnNames.STOP_LOSS] - df[BacktestColumnNames.ENTRY_PRICE]
            )
        return df

    def monetary_gains(self, df, trade_type: str):
        if trade_type == "long":
            df[BacktestColumnNames.MONETARY_GAIN] = (
                df[BacktestColumnNames.EXIT_PRICE] - df[BacktestColumnNames.ENTRY_PRICE]
            ) * df[BacktestColumnNames.STOCKS_TRADED]
        else:
            df[BacktestColumnNames.MONETARY_GAIN] = (
                df[BacktestColumnNames.ENTRY_PRICE] - df[BacktestColumnNames.EXIT_PRICE]
            ) * df[BacktestColumnNames.STOCKS_TRADED]

        return df

    def test_in_sample(self):
        pass

    def out_of_sample(self):
        pass

    def win_rate(self):
        # if first - last column is pos it's a win, else it's a loss.
        pass

    """
Instrument (for backtests performed on more instruments)
Time and date of entry
Entry by market or limit order
Entry price
Exit price
Entry pattern and timeframe (if applicable)
Exit pattern and timeframe (if applicable)
Position size and % risk on your trading account
MAE – maximal adverse excursion (measured by pips/ticks, percentually or by Reward-to-Risk Ratio)
MFE – maximal favourable excursion (measured by pips/ticks, percentually or by Reward-to-Risk Ratio)
Result of the trade measured in Reward-to-Risk ratio or the amount of ticks/pips
Notes for the trade – level of conviction, emotional aspects
    """
