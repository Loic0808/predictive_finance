import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from datetime import datetime

from TradingBots.EasyBot import EasyBot
from TradingBots.Indicator_functions import ATR

dataF = yf.download("MSFT", start="2024-10-15", end="2024-12-09", interval='15m')
dataF.columns = dataF.columns.droplevel(1)
dataF.reset_index(inplace=True)

dataF = ATR(dataF).calculate_chandelier_exit()

print(dataF)