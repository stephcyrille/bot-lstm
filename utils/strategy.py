import pandas as pd
import numpy as np

class TradeStrategy:
    """
        Attributes:
            df (pd.DataFrame): DataFrame containing trading data.
            reward_risk_ratio (float): Ratio of reward to risk (e.g., 2 means TP = 2 * SL).

        Methods:
            __init__(df: pd.DataFrame, reward_risk_ratio: float = 2.0):
                Initializes the TradeStrategy with trading data and reward-risk ratio.

            _calculate_dynamic_multipliers(atr, rsi, bollinger_percent_b):
                Computes dynamic multipliers based on volatility (ATR), RSI, and Bollinger Bands.

            _calculate_stop_loss_take_profit(indicator_df: pd.DataFrame):
                Computes stop-loss and take-profit levels using dynamic multipliers.

            run(indicator_df: pd.DataFrame):
                Executes stop-loss and take-profit calculation.


            :param df: DataFrame containing trading data.
            :param reward_risk_ratio: Ratio of reward to risk (e.g., 2 means TP = 2 * SL).
            pass


            :param atr: Average True Range values.
            :param rsi: Relative Strength Index values.
            :param bollinger_percent_b: Bollinger Bands %B values.
            :return: Tuple containing stop-loss and take-profit multipliers.
            pass


            :param indicator_df: DataFrame containing indicator values (ATR, RSI, Bollinger Bands).
            pass

            Executes stop-loss and take-profit calculation.

            :param indicator_df: DataFrame containing indicator values (ATR, RSI, Bollinger Bands).
            pass
    """

    def __init__(self, df: pd.DataFrame, symbol:str = 'EUR/USD', reward_risk_ratio: float = 2.0):
        """
        Initialize the strategy.

        :param df: DataFrame contenant les données de trading
        :param reward_risk_ratio: Ratio gain/perte (ex: 2 signifie que TP = 2 * SL)
        """
        self.df = df.copy()
        self.reward_risk_ratio = reward_risk_ratio
        self.symbol = symbol
        self.df["POSITION"] = np.where(self.df["PREDICTED_CLOSE"] > self.df["ENTRY_PRICE"], "BUY", "SELL")

    def _calculate_dynamic_multipliers(self, atr, rsi, bollinger_percent_b, macd, signal_line):
        """
        Compute dynamic multipliers based on volatility (ATR), RSI, Bollinger Bands, MACD, and Signal Line.
        """
        
        stop_loss_multiplier = np.where(atr > 0.002, 1.5 * 1.2, 1.5)
        take_profit_multiplier = stop_loss_multiplier * (self.reward_risk_ratio)  # Ajustement avec le ratio

        # RSI adjustments
        stop_loss_multiplier *= np.where(rsi < 30, 1.2, 1)
        take_profit_multiplier *= np.where(rsi > 70, 0.8, 1)

        # Bollinger Bands adjustments
        stop_loss_multiplier *= np.where(bollinger_percent_b < 0.2, 1.2, 1)
        take_profit_multiplier *= np.where(bollinger_percent_b > 0.8, 0.8, 1)

        # MACD adjustments
        stop_loss_multiplier *= np.where(macd > signal_line, 1.2, 1)
        take_profit_multiplier *= np.where(macd < signal_line, 0.8, 1)

        return stop_loss_multiplier, take_profit_multiplier

    def _calculate_stop_loss_take_profit(self, indicator_df: pd.DataFrame):
        """
        Compute stop-loss and take-profit levels using dynamic multipliers.
        """
        data = self.df.merge(indicator_df, left_index=True, right_index=True)

        sl_mult, tp_mult = self._calculate_dynamic_multipliers(
            data["ATR"], data["RSI"], data["BOLLINGER_PERCENT_B"], data["MACD"], data["SIGNAL_LINE"]
        )

        data["STOP_LOSS"] = np.where(
            data["POSITION"] == "SELL",
            data["PREDICTED_CLOSE"] + sl_mult * data["ATR"],
            data["PREDICTED_CLOSE"] - sl_mult * data["ATR"]
        )

        data["TAKE_PROFIT"] = np.where(
            data["POSITION"] == "SELL",
            data["PREDICTED_CLOSE"] - tp_mult * data["ATR"],
            data["PREDICTED_CLOSE"] + tp_mult * data["ATR"]
        )

        self.df = data[["ENTRY_PRICE", "PREDICTED_CLOSE", "POSITION", "STOP_LOSS", "TAKE_PROFIT"]]
    
    def _cac40_stop_loss_take_profit(self, indicator_df: pd.DataFrame):
        """
        Compute stop-loss and take-profit levels for CAC40 using fixed multipliers.
        """
        data = self.df.merge(indicator_df, left_index=True, right_index=True)
        # Calculate stop-loss and take-profit based on MACD, ATR, and fixed pip values
        sl_pip = np.where(data["MACD"] > data["SIGNAL_LINE"], 15, 10)
        tp_pip = sl_pip * self.reward_risk_ratio

        data["STOP_LOSS"] = np.where(
            data["POSITION"] == "SELL",
            data["PREDICTED_CLOSE"] + sl_pip,
            data["PREDICTED_CLOSE"] - sl_pip
        )
        data["TAKE_PROFIT"] = np.where(
            data["POSITION"] == "SELL",
            data["PREDICTED_CLOSE"] - tp_pip,
            data["PREDICTED_CLOSE"] + tp_pip
        )
        self.df = data[["ENTRY_PRICE", "PREDICTED_CLOSE", "POSITION", "STOP_LOSS", "TAKE_PROFIT"]]

    def run(self, indicator_df: pd.DataFrame):
        """Executes stop-loss and take-profit calculation."""
        if self.symbol == 'EUR/USD':
            self._calculate_stop_loss_take_profit(indicator_df)
        elif self.symbol == 'CAC40':
            self._cac40_stop_loss_take_profit(indicator_df)
        else:
            raise ValueError("Invalid symbol. Only 'EUR/USD' or 'CAC40' is supported.")
