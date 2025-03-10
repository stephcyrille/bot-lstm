import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler


class AgentTreadingDataset:
    """
    This class is responsible for calculating the indicators.
    the dataframe must be first processed with time index
    """
    CLOSE_FIELD = 'CLOSE'
    SHIFT_SIZE = 3
    SEQUENCE_LENGTH = 9

    def __init__(self, df:pd.DataFrame):
        self.df = df
        self._check_time_index()
        self.shifted_df = None
        self.scaled_df = None
        self.target_scaler = None
        self.feature_sequence = None
        self.target_sequence = None

    def prepare_data(self) -> None:
        """
        Prepare the data for the model.
        """
        if self.df is None:
            raise ValueError('The dataframe is empty.')
        elif self.df.shape[0] < 100:
            raise ValueError('The dataframe must have at least 40 rows.')
        extra_field = ['OPEN', 'HIGH', 'LOW', 'VOLUME', 'ATR']
        self.df = self.df.drop(columns=[field for field in extra_field if field in self.df.columns])
        self._add_shifted_features()
        self._encoding_features()
        self._create_sequence()
    
    def _add_shifted_features(self, shift_size:int=SHIFT_SIZE) -> None:
        """
        Create extra features for the model with a shift of shift_size. 
        So if we have x features and shift_size = 3, we will have 3 * x new features.
        
        Features
        ---
        - shift_size: int
        """
        features_list = self.df.columns.tolist()
        shifted_features = pd.concat(
            [self.df[feature].shift(i).rename(f'{feature}(t-{i})') 
            for feature in features_list for i in range(shift_size, 0, -1)],
            axis=1
        )
        self.shifted_df = pd.concat([self.df[self.CLOSE_FIELD], shifted_features], axis=1).dropna()
    
    def _check_time_index(self) -> None:
        """
        Check if the dataframe has a time index.
        """
        if not isinstance(self.df.index, pd.DatetimeIndex):
            raise ValueError('The dataframe must have a time index.')
        
    def _create_sequence(self, sequence_length:int=SEQUENCE_LENGTH) -> None:
        """
        Create the sequences for the LSTM model.
        
        Parameters:
        ---
        - sequence_length (int): The length of the sequence.
        """
        X = []
        y = []
        for i in range(sequence_length, len(self.scaled_df)):
            X.append(self.scaled_df.drop(columns=[self.CLOSE_FIELD]).iloc[i-sequence_length:i].values)
            y.append(self.scaled_df[self.CLOSE_FIELD].iloc[i])
        self.feature_sequence = np.array(X)
        self.target_sequence = np.array(y)
    
    def _encoding_features(self) -> None:
        """
        Encode the features.
        """
        # Initialize the MinMaxScaler for the target only
        self.target_scaler = MinMaxScaler(feature_range=(0, 1))
        self.target_scaler.fit(self.shifted_df[[self.CLOSE_FIELD]])

        # Initialize the MinMaxScaler for features only
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(self.shifted_df)
        self.scaled_df = pd.DataFrame(scaled_data, index=self.shifted_df.index, columns=self.shifted_df.columns)
