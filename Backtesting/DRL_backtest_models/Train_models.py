import os

from datetime import datetime
from stable_baselines3 import PPO

from Backtesting.Backtesting_bots.DRL_bot_v1 import StockTradingEnv
from Backtesting.Backtesting import Backtesting


class TrainDRLModels():

    def __init__(
            self,
            model_name,
            bank_account, 
            commission_fee,
            slippage_cost
            ):
        self.model_name = model_name
        self.bank_account = bank_account
        self.commission_fee = commission_fee
        self.slippage_cost = slippage_cost
        
        self.path_to_model = f"/Users/doblerloic/Desktop/Finance_prediction_project/predictive_finance/Backtesting/DRL_backtest_models/models/{model_name}"
        self.directory = "/Users/doblerloic/Desktop/Finance_prediction_project/predictive_finance/Backtesting/DRL_backtest_models/models/"

    def zip_file_exists(self):
        # Ensure the file has a .zip extension
        if not self.model_name.endswith('.zip'):
            self.model_name += '.zip'
        # Join the directory and filename safely
        zip_file_path = os.path.join(self.directory, self.model_name)
        # Check if the file exists
        return os.path.exists(zip_file_path)
        
    def train_model(self, df_train):
        # Initialize the environment for the bot
        env_train = StockTradingEnv(df_train, self.bank_account, self.commission_fee, self.slippage_cost)
        # Initialize, train and save the model
        trained_model = PPO("MlpPolicy", env_train, verbose=0)
        trained_model.learn(total_timesteps=100_000, progress_bar=True)
        trained_model.save(self.path_to_model)