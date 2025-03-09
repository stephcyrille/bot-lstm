import keras
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler


class PredictorToolkit:
    """
    This class is responsible for the prediction of the next value of a time series.
    """

    def __init__(self, target_scaler:MinMaxScaler, lstm_model:keras.Model, sequence_length:int=60):
        self.lstm_model = lstm_model
        self.sequence_length = sequence_length
        self.target_scaler = target_scaler
        self.next_index:pd.Timestamp = None
        self.predict_df = pd.DataFrame(columns=['ENTRY_PRICE', 'PREDICTED_CLOSE'])
        self.predict_df.index.name = 'DATETIME'


        
    def predict_the_next_price(self, df:pd.DataFrame, entry_price:float, 
                               previous_sequence:np.ndarray, close_label_field:str='CLOSE') -> pd.DataFrame:
        """
        Predict the next value (hour timeframe) of a time series using a LSTM model.
        feature_seq_array: The numpy darray containing the last sequence of data.
        sequence_length: The length of the sequence used for prediction.
        lstm_model: The trained LSTM model.
        close_label_field: The label of the field to predict.
        """
        self.next_index = df.index[-1] + pd.Timedelta(hours=1)
        prev_seq = previous_sequence.reshape(1, self.sequence_length, previous_sequence.shape[1])

        # Prediction 
        predicted_price_scaled = self.lstm_model.predict(prev_seq)
        predicted_price = self.target_scaler.inverse_transform(predicted_price_scaled)

        # Add the new row to the dataframe
        new_line_row = pd.DataFrame({close_label_field: predicted_price[0][0]}, index=[self.next_index])
        new_df = pd.concat([df, new_line_row])

        # Add the new row to the prediction dataframe
        new_row = pd.DataFrame({
            'ENTRY_PRICE': entry_price, 'PREDICTED_CLOSE': predicted_price[0][0]
            }, index=[self.next_index])
        self.predict_df = pd.concat([self.predict_df, new_row])

        return new_df



