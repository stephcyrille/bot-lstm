import keras
import pandas as pd
import numpy as np
import logging
from utils.predictor import PredictorToolkit
from utils.dataset import TreadingDataset
from utils.strategy import TradeStrategy
from utils.field_processing import create_ts_from_df

bot_logger = logging.getLogger("bot_logger")

model = keras.models.load_model('./models/test/best_model_FRA40.keras')


SEQUENCE_LENGTH = 9
SHIFT_SIZE = 3

class TradeEngine:
    def __init__(self, symbol:str) -> None:
        self.capital = 0
        self.entry_price = 0
        self.rr_ratio = 0
        self.symbol = symbol
        self.volume = 0

        self.stop_loss = 0
        self.take_profit = 0
        self.position = ''

        self.dataset:TreadingDataset = None
        self.predicted_data:pd.DataFrame = None

        self.api_key = ''
        self.api_secret = ''
        self.base_url = ''
        self.account_id = ''

    def init(self):
        self.connect_to_broker()
        self._pull_account_data()
        self._calculate_position_size()
        bot_logger.info("[+] Engine Initialized")
        bot_logger.info("=== Bot Parameters ===")
        bot_logger.info("Account ID: {}".format(self.account_id))
        bot_logger.info("Symbol: {}".format(self.symbol))
        bot_logger.info("Capital: {}".format(self.capital))
        bot_logger.info("Risk-Reward Ratio: {}%".format(self.rr_ratio))
        bot_logger.info("Volume: {}".format(self.volume))
        bot_logger.info("======================")

    def connect_to_broker(self) -> None:
        pass

    def _calculate_position_size(self) -> None:
        risk_amount = self.capital * (self.rr_ratio / 100)
        if "EURUSDT" == self.symbol:
            stop_loss = 20 * 0.0001 # stop_loss pips * 0.0001
            self.volume = risk_amount / stop_loss
        elif "BTCUSD" == self.symbol:
            self.volume = 0.001
        else:
            raise ValueError("Invalid Symbol")

    def _pull_account_data(self) -> None:
        self.account_id = '123456'
        self.capital = 10000
        self.rr_ratio = 2.0

    def _get_the_entry_price(self) -> float:
        return self.entry_price
    
    def prepare_the_order(self) -> None:
        self._fetch_history_data()
        self._get_the_entry_price()
        self._predict_close()
        self._calculate_strategy()
        bot_logger.info("[+] Order Prepared")
        bot_logger.info("Entry Price: {}".format(self.entry_price))
        bot_logger.info("Stop Loss: {}".format(self.stop_loss))
        bot_logger.info("Take Profit: {}".format(self.take_profit))
        bot_logger.info("Position: {}".format(self.position))
    
    def _fetch_history_data(self) -> pd.DataFrame:
        base_df = pd.read_csv('./FRA40_H1_202403_2025.csv', sep='\t', usecols=['<DATE>', '<TIME>', '<OPEN>', '<HIGH>', '<LOW>', '<CLOSE>'])
        base_df.rename(columns={
            '<OPEN>': 'OPEN', 
            '<HIGH>': 'HIGH', 
            '<LOW>': 'LOW', 
            '<CLOSE>': 'CLOSE'
        }, inplace=True)

        base_df = create_ts_from_df(base_df, '<DATE>', '<TIME>', 'DATETIME')
        base_df.loc[:'2025-03-07 10:00:00']
        dataset = TreadingDataset(base_df[['CLOSE']])
        dataset.prepare_data()
        self.dataset = dataset
    
    def _calculate_strategy(self) -> pd.DataFrame:
        predicted_data = self.predicted_data
        if predicted_data.shape[0] == 0:
            bot_logger.error("[-] No data to predict")
            return
        else:
            strategy = TradeStrategy(predicted_data, self.symbol, self.rr_ratio)
            strategy.run(self.dataset.df)
            self.entry_price = strategy.df['ENTRY_PRICE'].values[0]
            self.stop_loss = strategy.df['STOP_LOSS'].values[0]
            self.take_profit = strategy.df['TAKE_PROFIT'].values[0]
            self.position = strategy.df['POSITION'].values[0]

    def _predict_close(self) -> None:
        last_prev_lines = self.dataset.feature_sequence[-1]
        pred_tk = PredictorToolkit(self.dataset.target_scaler, model, SEQUENCE_LENGTH)

        last_prev_lines = self.dataset.feature_sequence[-1]
        entry_price = self.dataset.df[['CLOSE']].iloc[-1:].values[0][0]
        new_df = pred_tk.predict_the_next_price(self.dataset.df[['CLOSE']], entry_price, last_prev_lines)
        self.predicted_data = pred_tk.predict_df
        self.dataset.update_df(new_df)

            

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    bot = TradeEngine("EURUSDT")
    bot.init()
    print("Done")
