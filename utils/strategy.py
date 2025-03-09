import pandas as pd
import numpy as np

class TradeStrategy:
    """
    This class implements a trading strategy with dynamic stop-loss and take-profit levels.
    """

    def __init__(self, df: pd.DataFrame, reward_risk_ratio: float = 2.0):
        """
        Initialize the strategy.

        :param df: DataFrame contenant les données de trading
        :param reward_risk_ratio: Ratio gain/perte (ex: 2 signifie que TP = 2 * SL)
        """
        self.df = df.copy()
        self.reward_risk_ratio = reward_risk_ratio
        self.df["POSITION"] = np.where(self.df["PREDICTED_CLOSE"] > self.df["ENTRY_PRICE"], "BUY", "SELL")

    def _calculate_dynamic_multipliers(self, atr, rsi, bollinger_percent_b):
        """
        Compute dynamic multipliers based on volatility (ATR), RSI, and Bollinger Bands.
        """
        stop_loss_multiplier = np.where(atr > 0.002, 1.5 * 1.2, 1.5)
        take_profit_multiplier = stop_loss_multiplier * self.reward_risk_ratio  # Ajustement avec le ratio

        # RSI adjustments
        stop_loss_multiplier *= np.where(rsi < 30, 1.2, 1)
        take_profit_multiplier *= np.where(rsi > 70, 0.8, 1)

        # Bollinger Bands adjustments
        stop_loss_multiplier *= np.where(bollinger_percent_b < 0.2, 1.2, 1)
        take_profit_multiplier *= np.where(bollinger_percent_b > 0.8, 0.8, 1)

        return stop_loss_multiplier, take_profit_multiplier

    def _calculate_stop_loss_take_profit(self, indicator_df: pd.DataFrame):
        """
        Compute stop-loss and take-profit levels using dynamic multipliers.
        """
        data = self.df.merge(indicator_df, left_index=True, right_index=True)

        sl_mult, tp_mult = self._calculate_dynamic_multipliers(data["ATR"], data["RSI"], data["BOLLINGER_PERCENT_B"])

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

    def run(self, indicator_df: pd.DataFrame):
        """Executes stop-loss and take-profit calculation."""
        self._calculate_stop_loss_take_profit(indicator_df)

    # def backtesting(self, real_df: pd.DataFrame, capital: float, risk_per_trade: float = 0.01) -> pd.DataFrame:
    #     """
    #     Perform backtesting using historical price data.
    #     """
    #     backtest_df = real_df.merge(self.df, left_index=True, right_index=True)
    #     trade_risk = risk_per_trade * capital

    #     wins = ((backtest_df["POSITION"] == "BUY") & (backtest_df["HIGH"] >= backtest_df["TAKE_PROFIT"])) | \
    #            ((backtest_df["POSITION"] == "SELL") & (backtest_df["LOW"] <= backtest_df["TAKE_PROFIT"]))

    #     losses = ((backtest_df["POSITION"] == "BUY") & (backtest_df["LOW"] <= backtest_df["STOP_LOSS"])) | \
    #              ((backtest_df["POSITION"] == "SELL") & (backtest_df["HIGH"] >= backtest_df["STOP_LOSS"]))

    #     win_trades = wins.sum()
    #     loss_trades = losses.sum()
        
    #     capital += win_trades * (trade_risk * self.reward_risk_ratio) - loss_trades * trade_risk

    #     print(f"Final Capital : {capital:.2f}")
    #     print(f"Win trades : {win_trades}, Loss trades : {loss_trades}")
    #     print(f"Success rate : {win_trades / max(1, (win_trades + loss_trades)) * 100:.2f}%")

    #     return backtest_df
