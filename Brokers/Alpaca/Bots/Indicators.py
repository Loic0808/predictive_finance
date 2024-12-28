from Brokers.Alpaca.Testing.EasyBot import ColumnNames

class ATR():
    def __init__(self, df):
        self.df = df

    def __calculate_atr(self, n):
        # Calculate the True Range (TR)
        self.df["TR"] = self.df[[ColumnNames.HIGH, ColumnNames.LOW, ColumnNames.CLOSE]].max(axis=1) - self.df[
            [ColumnNames.HIGH, ColumnNames.LOW, ColumnNames.CLOSE]
        ].min(axis=1)
        self.df["TR"] = self.df["TR"].combine(self.df[ColumnNames.HIGH] - self.df[ColumnNames.CLOSE].shift(), max)
        self.df["TR"] = self.df["TR"].combine(self.df[ColumnNames.LOW] - self.df[ColumnNames.CLOSE].shift(), max)

        # Calculate the ATR using a rolling window
        self.df["ATR"] = self.df["TR"].rolling(window=n).mean()
        return self.df

    def calculate_chandelier_exit(self, n=22, multiplier=3):
        # Calculate the ATR
        self.df = self.__calculate_atr(n)

        # Calculate the highest high and lowest low over the lookback period
        self.df["Highest_High"] = self.df[ColumnNames.HIGH].rolling(window=n).max()
        self.df["Lowest_Low"] = self.df[ColumnNames.LOW].rolling(window=n).min()

        # Calculate the Chandelier Exit
        self.df["Chandelier_Exit_Long"] = self.df["Highest_High"] - self.df["ATR"] * multiplier
        self.df["Chandelier_Exit_Short"] = self.df["Lowest_Low"] + self.df["ATR"] * multiplier

        self.df = self.df.drop(columns=["TR", "Highest_High", "Lowest_Low"])

        return self.df

class EMA():

    def __init__(self, df):

        self.df = df

    def EMA_50(self, n=50):
        self.df[ColumnNames.EMA_50] = self.df[ColumnNames.CLOSE].ewm(span=n, adjust=False).mean()
        return self.df

