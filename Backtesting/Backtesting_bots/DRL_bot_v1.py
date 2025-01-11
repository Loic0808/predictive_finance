# TradingEnv.py
import numpy as np
import gymnasium as gym
from gymnasium import spaces
import pandas as pd
import matplotlib.pyplot as plt 
from stable_baselines3 import PPO

from Trading_bots.Abstract_Bot import AbstractBot
from Backtesting.Backtesting import BacktestColumnNames
from Brokers.Alpaca.Column_names import ColumnNames


class DRLBotV1(AbstractBot):

    def __init__(
            self,
            model_name,
            bank_account, 
            commission_fee,
            slippage_cost
            ):
        self.bank_account = bank_account
        self.commission_fee = commission_fee
        self.slippage_cost = slippage_cost

        # Path to save the models
        self.path = f"/Users/doblerloic/Desktop/Finance_prediction_project/predictive_finance/Backtesting/DRL_backtest_models/models/{model_name}"

    def train_model(self):
        # call train model class
        pass

    def run_strat(self, df):
        # Initialize the testing environment and load the model
        env_test = StockTradingEnv(df, self.bank_account, self.commission_fee, self.slippage_cost)
        run_model = PPO.load(self.path, env=env_test)

        vec_env = run_model.get_env()
        obs = vec_env.reset()
        for i in range(len(df[ColumnNames.CLOSE])):
            action, _state = run_model.predict(obs)
            obs, reward, done, info = vec_env.step(action)
            
        self.backtesting_df = env_test.backtesting_df
        env_test.render_all()


class StockTradingEnv(gym.Env):
    def __init__(self, data, initial_balance=10000, commission_fee=0.01, slippage_cost=0.1):
        super(StockTradingEnv, self).__init__()
        self.data = data
        self.current_step = 0
        self.initial_balance = initial_balance
        self.balance = self.initial_balance
        self.stock_owned = 0
        self.date = data[ColumnNames.TIMESTAMP]
        self.stock_price_history = data[ColumnNames.CLOSE]
        self.stock_high_price_history = data[ColumnNames.HIGH]
        self.stock_low_price_history = data[ColumnNames.LOW]
        self.commission_fee = commission_fee
        self.slippage_cost = slippage_cost
        
        self.action_space = spaces.Box(low=np.array([-1, 0]), high=np.array([1, 1]), shape=(2,))  # (Action, Amount) where Action: -1: Buy, 0: Hold, 1: Sell
        #  _____________
        # |Action|Amount|
        # |    +1|    +1|
        # |    -1|     0|
        #
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(1,))
        
        self.render_df = pd.DataFrame()
        self.done = False
        self.current_portfolio_value = initial_balance

        # Own added variables 
        self.in_trade = False
        self.max_price = -np.inf
        self.min_price = np.inf
        self.last_action = 0
        self.buy_info = []

        """
        All the backtesting/monitoring information will be stored here. We enter a trade when we buy or sell a stock
        we don't exit this trade as long as we don't to the opposite action, i.e., even if we buy multiple times, as long as
        we don't sell a stock we are still in the trade
        """
        self.backtesting_columns = [
            BacktestColumnNames.TIMESTAMP,
            BacktestColumnNames.ENTRY_PRICE,
            BacktestColumnNames.STOP_LOSS,
            BacktestColumnNames.TAKE_PROFIT,
            BacktestColumnNames.STOCKS_TRADED, 
            BacktestColumnNames.MAX_PRICE,
            BacktestColumnNames.MIN_PRICE,
            BacktestColumnNames.TRADE_TYPE,
            BacktestColumnNames.IN_TRADE,
            BacktestColumnNames.EXIT_PRICE,
        ]
        self.backtesting_df = pd.DataFrame(columns=self.backtesting_columns)
        self.backtesting_df = self.backtesting_df.astype(
            {
                BacktestColumnNames.TIMESTAMP: 'datetime64[ns]',
                BacktestColumnNames.ENTRY_PRICE: float,
                BacktestColumnNames.STOP_LOSS: float,
                BacktestColumnNames.TAKE_PROFIT: float,
                BacktestColumnNames.STOCKS_TRADED: int,
                BacktestColumnNames.MAX_PRICE: float,
                BacktestColumnNames.MIN_PRICE: float,
                BacktestColumnNames.TRADE_TYPE: str,
                BacktestColumnNames.IN_TRADE: bool,
                BacktestColumnNames.EXIT_PRICE: float,
            }
        )

    def group_backtesting(self):
        # We need to group by actions
        pass
        
    def reset(self, seed = None):
        self.current_step = 0
        self.balance = self.initial_balance
        self.stock_owned = 0
        self.done = False
        self.current_portfolio_value = self.initial_balance
        self.in_trade = False
        self.max_price = -np.inf
        self.min_price = np.inf
        self.last_action = 0
        self.buy_info = []
        return self._get_observation(), {}
    
    def step(self, action):
        assert self.action_space.contains(action)
        prev_portfolio_value = self.balance if self.current_step == 0 else self.balance + self.stock_owned * self.stock_price_history[self.current_step - 1]
        current_price = self.stock_price_history[self.current_step]    
        amount = int(self.initial_balance * action[1] / current_price)

        # If we are in trading, at each step we calculate the max and min price of the asset
        if self.in_trade:
            self.max_price = max(self.max_price, self.stock_high_price_history[self.current_step])
            self.min_price = min(self.min_price, self.stock_low_price_history[self.current_step])
    
        if action[0] > 0:  # Buy
            amount =  min(int(self.initial_balance * action[1] / current_price), int(self.balance / current_price * (1 + self.commission_fee + self.slippage_cost)))
            if self.balance >= current_price * amount * (1 + self.commission_fee + self.slippage_cost):
                self.stock_owned += amount
                self.balance -= current_price * amount * (1 + self.commission_fee + self.slippage_cost)

                if self.in_trade:
                    # We are in a trade
                    if self.last_action == -1:
                        # We exit the trade
                        self.buy_info.extend([
                            self.date[self.current_step], # date of action
                            None, # There can be multiple entry prices before
                            None, # Stop loss
                            None, # Take profit
                            amount, # Number of stocks traded
                            self.max_price, # max price
                            self.min_price, # min price
                            self.trade_type, # long or short
                            self.in_trade, # Tells if we trade or not
                            self.stock_price_history[self.current_step] # exit price
                        ])

                        self.max_price = -np.inf
                        self.min_price = np.inf
                        self.in_trade = False 
                        self.last_action = 1

                    else:
                        # We continue in the same trade 
                        self.buy_info.extend([
                            self.date[self.current_step], 
                            self.stock_price_history[self.current_step],
                            None, 
                            None, 
                            amount, 
                            None, 
                            None, 
                            self.trade_type, 
                            self.in_trade, 
                            None
                        ])

                else:
                    # We enter a trade
                    self.trade_type = "long"
                    self.in_trade = True
                    self.last_action = 1

                    self.buy_info.extend([
                            self.date[self.current_step], 
                            self.stock_price_history[self.current_step],
                            None, 
                            None, 
                            amount, 
                            None, 
                            None, 
                            self.trade_type, 
                            self.in_trade, 
                            None 
                        ])

        elif action[0] < 0:  # Sell
            amount = min(amount, self.stock_owned)
            if self.stock_owned > 0:
                self.stock_owned -= amount
                self.balance += current_price * amount * (1 - self.commission_fee - self.slippage_cost)

                if self.in_trade:
                    # We are in a trade
                    if self.last_action == 1:
                        # We exit the trade
                        self.buy_info.extend([
                            self.date[self.current_step], # date of action
                            None, # There can be multiple entry prices before
                            None, # Stop loss
                            None, # Take profit
                            amount, # Number of stocks traded
                            self.max_price, # max price
                            self.min_price, # min price
                            self.trade_type, # long or short
                            self.in_trade, # Tells if we trade or not
                            self.stock_price_history[self.current_step] # exit price
                        ])

                        self.max_price = -np.inf
                        self.min_price = np.inf
                        self.in_trade = False 
                        self.last_action = -1

                    else:
                        # We continue in the same trade 
                        self.buy_info.extend([
                            self.date[self.current_step], 
                            self.stock_price_history[self.current_step],
                            None, 
                            None, 
                            amount, 
                            None, 
                            None, 
                            self.trade_type, 
                            self.in_trade, 
                            None
                        ])

                else:
                    # We enter a trade
                    self.trade_type = "short"
                    self.in_trade = True
                    self.last_action = -1

                    self.buy_info.extend([
                            self.date[self.current_step], 
                            self.stock_price_history[self.current_step],
                            None, 
                            None, 
                            amount, 
                            None, 
                            None, 
                            self.trade_type, 
                            self.in_trade, 
                            None 
                        ])
        
        current_portfolio_value = self.balance + self.stock_owned * current_price
        excess_return = current_portfolio_value - prev_portfolio_value 
        risk_free_rate = 0.02  # Example risk-free rate
        std_deviation = np.std(self.stock_price_history[:self.current_step + 1])
        sharpe_ratio = (excess_return - risk_free_rate) / std_deviation if std_deviation != 0 else 0
        reward = sharpe_ratio

        if len(self.buy_info) > 0:
            new_data = pd.DataFrame([self.buy_info], columns=self.backtesting_columns)
            self.backtesting_df = pd.concat([self.backtesting_df, new_data], ignore_index=True)
            self.buy_info = []
         
        self.render(action, amount, current_portfolio_value)
        obs = self._get_observation()
        
        self.current_step += 1
        
        if self.current_step == len(self.data[ColumnNames.CLOSE]):
            done = True
        else:
            done = False
        
        self.done = done

        info = {}  
        return obs, reward, done, False,info
    
    
    def _get_observation(self):
        return np.array([
            self.stock_price_history[self.current_step]
        ])
    
    def render(self, action, amount, current_portfolio_value, mode = None):
        current_date = self.date[self.current_step]
        today_action =  'buy' if action[0] > 0 else 'sell'
        current_price = self.stock_price_history[self.current_step]
        
        if mode == 'human':
            print(f"Step:{self.current_step}, Date: {current_date}, Market Value: {current_portfolio_value:.2f}, Balance: {self.balance:.2f}, Stock Owned: {self.stock_owned}, Stock Price: {current_price:.2f}, Today Action: {today_action}:{amount}")
        else:
            pass
        dict = {
            'Date': [current_date], 'market_value': [current_portfolio_value], 'balance': [self.balance], 'stock_owned': [self.stock_owned], 'price': [current_price], 'action': [today_action], 'amount':[amount]
        }
        step_df = pd.DataFrame.from_dict(dict)
        self.render_df = pd.concat([self.render_df, step_df], ignore_index=True)
    
    def render_all(self):
        df = self.render_df.set_index('Date')   
        print(df)    
        """
        fig, ax = plt.subplots(figsize=(18, 6)) 
        df.plot( y="market_value" , use_index=True,  ax = ax, style='--' , color='lightgrey') 
        df.plot( y="price" , use_index=True,  ax = ax , secondary_y = True , color='black')
         
        for idx in df.index.tolist():
            if (df.loc[idx]['action'] == 'buy') & (df.loc[idx]['amount'] > 0):
                plt.plot(
                    idx,
                    df.loc[idx]["price"] - 1,
                    'g^'
                )
                plt.text(idx, df.loc[idx]["price"]- 3, df.loc[idx]['amount'] , c= 'green',fontsize=8, horizontalalignment='center', verticalalignment='center')
            elif (df.loc[idx]['action'] == 'sell') & (df.loc[idx]['amount'] > 0):
                plt.plot(
                    idx,
                    df.loc[idx]["price"] + 1,
                    'rv'
                    )
                plt.text(idx, df.loc[idx]["price"] + 3, df.loc[idx]['amount'], c= 'red',fontsize=8, horizontalalignment='center', verticalalignment='center')
        """