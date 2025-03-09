import pandas as pd
import numpy as np

class Backtester:
    def __init__(self, df:pd.DataFrame) -> None:
        """
        Initialize the backtester with historical data.
        """
        self.df = df
        self.results = []

    def simulate_trades(self):
        """
        Simulate trades using adjusted stop-loss and take-profit.
        """
        for i, row in self.df.iterrows():
            entry_price = row['ENTRY_PRICE']
            position = row['POSITION']
            stop_loss = row['STOP_LOSS']
            take_profit = row['TAKE_PROFIT']
            actual_close = row['CLOSE']

            if position == 'BUY':
                # Check if take-profit or stop-loss is reached
                if actual_close >= take_profit:
                    profit = take_profit - entry_price
                    self.results.append(profit)
                elif actual_close <= stop_loss:
                    profit = stop_loss - entry_price
                    self.results.append(profit)
                else:
                    profit = actual_close - entry_price
                    self.results.append(profit)
            elif position == 'SELL':
                # Check if take-profit or stop-loss is reached
                if actual_close <= take_profit:
                    profit = entry_price - take_profit
                    self.results.append(profit)
                elif actual_close >= stop_loss:
                    profit = entry_price - stop_loss
                    self.results.append(profit)
                else:
                    profit = entry_price - actual_close
                    self.results.append(profit)

    def calculate_performance_metrics(self):
        """
        Calculate performance metrics.
        """
        results = pd.Series(self.results)
        total_trades = len(results)
        winning_trades = results[results > 0].count()
        losing_trades = results[results <= 0].count()
        win_rate = winning_trades / total_trades
        net_profit = results.sum()
        average_profit = results.mean()
        sharpe_ratio = self.calculate_sharpe_ratio(results)

        performance_metrics = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'net_profit': net_profit,
            'average_profit': average_profit,
            'sharpe_ratio': sharpe_ratio
        }
        return performance_metrics

    def calculate_sharpe_ratio(self, returns:pd.Series, risk_free_rate:float=0.0):
        """
        Calculate the Sharpe ratio.
        """
        excess_returns = returns - risk_free_rate
        sharpe_ratio = excess_returns.mean() / excess_returns.std()
        return sharpe_ratio