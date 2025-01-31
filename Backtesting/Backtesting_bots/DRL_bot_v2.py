import numpy as np
import gymnasium as gym
import pandas as pd

from gymnasium import spaces
from stable_baselines3 import PPO

from Trading_bots.Abstract_Bot import AbstractBot
from Brokers.Alpaca.Column_names import ColumnNames
from Backtesting.Backtesting import BacktestColumnNames
from Backtesting.DRL_backtest_models.Train_models import TrainDRLModels

class DRLBotV2(AbstractBot):
    def __init__(self, model_name, bank_account, commission_fee, slippage_cost):
        self.bank_account = bank_account
        self.commission_fee = commission_fee
        self.slippage_cost = slippage_cost
        self.model_name = model_name

        # Path to save the models
        self.path = f"/Users/doblerloic/Desktop/Finance_prediction_project/predictive_finance/Backtesting/DRL_backtest_models/models/{model_name}"

    def train_model(self, df_train):
        Trainer = TrainDRLModels(self.model_name, self.bank_account, self.commission_fee, self.slippage_cost)

        if not Trainer.zip_file_exists():
            print("Train model")
            Trainer.train_model(df_train)
        else:
            print("Load model")

    def run_strat(self, df):
        # Initialize the testing environment and load the model
        env_test = StockTradingEnv(
            df, self.bank_account, self.commission_fee, self.slippage_cost
        )
        run_model = PPO.load(self.path, env=env_test)

        vec_env = run_model.get_env()
        obs = vec_env.reset()
        for i in range(len(df[ColumnNames.CLOSE])):
            action, _state = run_model.predict(obs)
            obs, reward, done, info = vec_env.step(action)

        self.backtesting_df = env_test.backtest_df

    def get_backtest_df(self):
            return self.backtesting_df

class StockTradingEnv(gym.Env):
    def __init__(
        self, data, initial_balance=10000, commission_fee=0.01, slippage_cost=0.1
    ):
        super(StockTradingEnv, self).__init__()
        self.data = data
        self.current_step = 0
        self.initial_balance = initial_balance
        self.balance = self.initial_balance
        self.stock_owned = 0
        self.date = data[ColumnNames.TIMESTAMP]
        self.stock_price_history = data[ColumnNames.CLOSE]
        self.commission_fee = commission_fee
        self.slippage_cost = slippage_cost

        self.action_space = spaces.Box(
            low=np.array([-1, 0]), high=np.array([1, 1]), shape=(2,)
        )  # (Action, Amount) where Action: -1: Buy, 0: Hold, 1: Sell
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(1,))

        self.backtest_df = pd.DataFrame()
        self.done = False
        self.current_portfolio_value = initial_balance

    def reset(self, seed=None):
        self.current_step = 0
        self.balance = self.initial_balance
        self.stock_owned = 0
        self.done = False
        self.current_portfolio_value = self.initial_balance
        return self._get_observation(), {}

    def step(self, action):
        assert self.action_space.contains(action)
        prev_portfolio_value = (
            self.balance
            if self.current_step == 0
            else self.balance
            + self.stock_owned * self.stock_price_history[self.current_step - 1]
        )
        current_price = self.stock_price_history[self.current_step]
        amount = int(self.initial_balance * action[1] / current_price)

        if action[0] > 0:  # Buy
            amount = min(
                int(self.initial_balance * action[1] / current_price),
                int(
                    self.balance
                    / current_price
                    * (1 + self.commission_fee + self.slippage_cost)
                ),
            )
            if self.balance >= current_price * amount * (
                1 + self.commission_fee + self.slippage_cost
            ):
                self.stock_owned += amount
                self.balance -= (
                    current_price
                    * amount
                    * (1 + self.commission_fee + self.slippage_cost)
                )
        elif action[0] < 0:  # Sell
            amount = min(amount, self.stock_owned)
            if self.stock_owned > 0:
                self.stock_owned -= amount
                self.balance += (
                    current_price
                    * amount
                    * (1 - self.commission_fee - self.slippage_cost)
                )

        current_portfolio_value = self.balance + self.stock_owned * current_price
        excess_return = current_portfolio_value - prev_portfolio_value
        risk_free_rate = 0.02  # Example risk-free rate
        std_deviation = np.std(self.stock_price_history[: self.current_step + 1])
        sharpe_ratio = (
            (excess_return - risk_free_rate) / std_deviation
            if std_deviation != 0
            else 0
        )
        reward = sharpe_ratio

        self.__backtest_info(action, amount, current_portfolio_value)
        obs = self._get_observation()

        self.current_step += 1

        if self.current_step == len(self.data[ColumnNames.CLOSE]):
            done = True
        else:
            done = False

        self.done = done

        info = {}
        return obs, reward, done, False, info

    def __backtest_info(self, action, amount, current_portfolio_value):
        """
        Stores the action (buy, sell or hold), the timestamp, the number of traded
        stocks and the account information.
        """
        current_date = self.date[self.current_step]
        today_action = "buy" if action[0] > 0 else "sell"
        dict = {
            BacktestColumnNames.TIMESTAMP: [current_date],
            BacktestColumnNames.PORTFOLIO_VALUE: [current_portfolio_value],
            BacktestColumnNames.CASH: [self.balance],
            BacktestColumnNames.STOCKS_TRADED: [self.stock_owned],
            BacktestColumnNames.ACTION: [today_action],
            BacktestColumnNames.STOCKS_OWNED: [amount],
        }
        step_df = pd.DataFrame.from_dict(dict)
        self.backtest_df = pd.concat([self.backtest_df, step_df], ignore_index=True)

    def _get_observation(self):
        return np.array([self.stock_price_history[self.current_step]])
