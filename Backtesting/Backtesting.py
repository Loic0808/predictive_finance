import os
import pickle
import numpy as np
import pandas as pd

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
        self.start_date = start_date
        self.end_date = end_date
        self.asset_list = asset_list

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
        file_path = f"Backtesting/Backtesting_data/EasyBot/start_{self.start_date}_end_{self.end_date}_asset{self.asset_list}.csv"
        list_path = f"Backtesting/Backtesting_data/EasyBot/start_{self.start_date}_end_{self.end_date}_asset{self.asset_list}.pkl"
        if os.path.exists(file_path):
            self.backtest_df = pd.read_csv(file_path)
            with open(list_path, 'rb') as file:
                self.log_info_list = pickle.load(file)
        else:
            self.trading_bot = trading_bot
            self.trading_bot.run_strat(df)
            self.backtest_df = self.trading_bot.backtesting
            self.log_info_list = self.trading_bot.log_info

            self.backtest_df.to_csv(file_path, index=False)
            with open(list_path, 'wb') as file:
                pickle.dump(self.log_info_list, file)

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
    
    def net_profit(self, df):
        gains = df[df[BacktestColumnNames.MONETARY_GAIN] >= 0][BacktestColumnNames.MONETARY_GAIN].sum()
        losses = df[df[BacktestColumnNames.MONETARY_GAIN] < 0][BacktestColumnNames.MONETARY_GAIN].sum()

        return gains, losses, gains - losses

    def win_rate(self, df):
        """
        What it Describes:
        Win Rate measures the proportion of profitable trades compared to the total number of trades.

        High Win Rate: Most trades are profitable, but it doesn't guarantee profitability if losses are large.
        Low Win Rate: A strategy can still be profitable with a low win rate if winners are much larger than losers (like trend-following strategies).
        Intuition:
        Think of it like a batting average in baseball. Winning often doesn’t mean winning big.
        """
        df_win = df[df[BacktestColumnNames.PROFIT_LOSS] > 0]
        wins = len(df_win)
        all_trades = len(df)

        return wins / all_trades
    
    def profit_factor(self, df):
        """
        Profit factor is the ratio of the total profits to total losses over a specific period or set of trades. A profit factor greater than 1 indicates that the strategy is profitable overall.
        This ratio provides insight into the overall efficiency of a trading strategy by comparing how much profit is made for every dollar lost. It’s a simple way to measure profitability.
        A profit factor of 2 means the strategy makes $2 in profit for every $1 lost.
        """
        gains = df[df[BacktestColumnNames.MONETARY_GAIN] >= 0][BacktestColumnNames.MONETARY_GAIN].sum()
        losses = df[df[BacktestColumnNames.MONETARY_GAIN] < 0][BacktestColumnNames.MONETARY_GAIN].sum()

        return gains/losses

    def average_win_over_loss(self, df):
        """
        The average win/loss is the average size of winning trades compared to the average size of losing trades.
        This metric helps traders understand the potential magnitude of wins compared to losses. A strategy with a high average win/loss ratio can remain profitable even if the win rate is relatively low.
        For instance, an average win/loss ratio of 3 means that, on average, winning trades are three times larger than losing trades.
        """
        average_gains = df[df[BacktestColumnNames.MONETARY_GAIN] >= 0][BacktestColumnNames.MONETARY_GAIN].mean()
        average_losses = abs(df[df[BacktestColumnNames.MONETARY_GAIN] < 0][BacktestColumnNames.MONETARY_GAIN].mean())

        return average_gains/average_losses

    def shrap_ration(self, df):
        """
        The Sharpe ratio is a risk-adjusted measure of return, showing how much excess return is received for the additional volatility (risk) taken by the trader. It is one of the most commonly used metrics in finance to compare different strategies.
        The Sharpe ratio allows traders to evaluate whether a strategy’s returns are due to smart trading or simply taking on too much risk. A higher Sharpe ratio indicates better risk-adjusted returns.
        A ratio above 1 is generally considered good, while above 2 is excellent.

        The Sharpe ratio is a key metric that measures the risk-adjusted return of a trading strategy. 
        It tells how much excess return one is receiving for the additional risk they're taking on compared to a risk-free asset (such as government bonds).
        """
        pass



    def risk_reward_ratio(self, df):
        """
        What it Describes:
        The Risk-Reward Ratio compares the average profit per trade to the average loss per trade.

        R:R > 1: On average, you gain more than you risk per trade.
        R:R < 1: The losses are larger than the profits, which can be dangerous unless the win rate is very high.
        Intuition:
        It describes how much reward you’re targeting for every unit of risk you take. Imagine risking $100 to make $300 — that’s a 3:1 risk-reward ratio.
        """
        winning_trades = df[df[BacktestColumnNames.PROFIT_LOSS] > 0][
            BacktestColumnNames.PROFIT_LOSS
        ]
        losing_trades = df[df[BacktestColumnNames.PROFIT_LOSS] < 0][
            BacktestColumnNames.PROFIT_LOSS
        ]

        if winning_trades.empty:
            return 0

        elif losing_trades.empty:
            return 0

        self.average_profit = winning_trades.mean()
        self.average_loss = abs(losing_trades.mean())

        return self.average_profit / self.average_loss

    def profitability(self, df):
        """
        What it Describes:
        Profitability assesses whether your strategy generates a positive return over the long term. It's often calculated as the net profit over a period.

        Key Factors:

        Considers both win rate and risk-reward ratio.
        Requires a large enough sample size to be meaningful.
        Intuition:
        Think of it like checking whether your entire trading career leaves you with more money than you started with.
        """
        # This is the expectation
        win_rate = self.win_rate(df)
        self.risk_reward_ratio(df)

        # We have a minus since we take the absolute value of the average loss
        return win_rate * self.average_profit - ((1 - win_rate) * self.average_loss)

    def maximal_drawdown(self, df):
        """
        What it Describes:
        Maximal Drawdown measures the largest peak-to-trough decline in your portfolio value during a backtest.

        Shows worst-case risk.
        Reflects how much capital you could lose before the strategy recovers.
        Intuition:
        Imagine climbing a mountain and then falling into a deep valley before reaching a new peak. Drawdown measures how deep that valley goes before recovery.
        """
        pass

    def consistency(self, df):
        # This is the standard deviation
        """
        What it Describes:
        Consistency evaluates whether the strategy performs well across different market conditions and time periods.

        A strategy with high consistency will perform similarly across different years or asset types.
        A strategy with low consistency may work well only in specific market conditions (e.g., trending markets but not sideways markets).
        Intuition:
        Think of a sports team — a consistent team performs well across multiple seasons, not just one.
        """
        mean_return = df[BacktestColumnNames.PROFIT_LOSS].mean()

        df["Squared_return"] = (df[BacktestColumnNames.PROFIT_LOSS] - mean_return) ** 2

        res = df["Squared_return"].sum()

        return np.sqrt(res / (len(df) - 1))

    def equity_curve_simulation(self, df, initial_capital):
        """
        What it Describes:
        An Equity Curve Simulator visualizes possible outcomes of a strategy based on metrics like win rate, risk-reward ratio, and starting capital.

        Useful for visualizing the potential path of capital growth.
        Often used for stress-testing and expectation setting.
        Intuition:
        Picture a line graph where your portfolio grows (or shrinks) over time, showing different possible paths your account could take under various scenarios.
        """
        rrr = self.risk_reward_ratio(df)
        wr = self.win_rate(df)

        return initial_capital * (1 + rrr * wr - (1 - wr))

    def test_in_sample(self):
        pass

    def out_of_sample(self):
        pass
