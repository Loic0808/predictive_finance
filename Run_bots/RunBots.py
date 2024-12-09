import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from datetime import datetime

from TradingBots.EasyBot import EasyBot


dataF = yf.download("MSFT", start="2024-10-09", end="2024-12-06", interval='15m')
dataF.columns = dataF.columns.droplevel(1)
dataF.reset_index(inplace=True)
