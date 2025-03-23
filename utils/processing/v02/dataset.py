import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler


class TradingDataset:
    """
    This class is responsible for calculating the indicators.
    the dataframe must be first processed with time index
    """
    CLOSE_FIELD = 'CLOSE'
    SHIFT_SIZE = 3
    SEQUENCE_LENGTH = 9

    def __init__(self, df:pd.DataFrame, close_field:str = CLOSE_FIELD, 
                 shift_size:int=SHIFT_SIZE, sequence_length:int=SEQUENCE_LENGTH, 
                 target_features_list:list[str] = ['HIGH', 'LOW', 'CLOSE']):
        self.df = df
        self.close_field = close_field
        self.shift_size = shift_size
        self.sequence_length = sequence_length
        self.target_features_list = target_features_list
        self.shifted_df = None
        self.scaled_df = None
        self.target_scaler = None
        self.feature_sequence = None
        self.target_sequence = None
        self._check_time_index()
    
    def _check_time_index(self) -> None:
        """
        Check if the dataframe has a time index.
        """
        if not isinstance(self.df.index, pd.DatetimeIndex):
            raise ValueError('The dataframe must have a time index.')

    def prepare_data(self) -> None:
        """
        Prepare the data for the model.
        """
        if self.df is None:
            raise ValueError('The dataframe is empty.')
        elif self.df.shape[0] < 100:
            raise ValueError('The dataframe must have at least 40 rows.')
        self._add_shifted_features()
        self._encoding_features()
        self._create_sequence()
    
    def _add_shifted_features(self) -> None:
        """
        Create extra features for the model with a shift of shift_size. 
        So if we have x features and shift_size = 3, we will have 3 * x new features.
        """
        data = self.df.copy()
        features_list = data.columns.tolist()
        shifted_features = pd.concat(
            [data[feature].shift(i).rename(f'{feature}(t-{i})') 
            for feature in features_list for i in range(self.shift_size, 0, -1)],
            axis=1
        )

        # Reput the base trading features into the shifted features
        features_base_list = [x for x in ['OPEN', 'HIGH', 'LOW', 'CLOSE'] if x in self.df.columns.tolist()]
        self.shifted_df = pd.concat([self.df[features_base_list], shifted_features], axis=1).dropna()
    
    def _create_sequence(self) -> None:
        """
        Create the sequences for the LSTM model.
        """
        # Ensure the target features are scaled correctly
        scaled_targets = self.target_scaler.transform(self.shifted_df[self.target_features_list])
        # Drop the target features from the input features
        input_features = self.scaled_df.drop(columns=self.target_features_list)
        
        X = []
        y = []
        for i in range(self.sequence_length, len(self.scaled_df)):
            # Append the sequence of input features
            X.append(input_features.iloc[i-self.sequence_length:i].values)
            # Append the corresponding target values
            y.append(scaled_targets[i, :])
        
        # Convert lists to numpy arrays
        self.feature_sequence = np.array(X)
        self.target_sequence = np.array(y)
    
    def _encoding_features(self) -> None:
        """
        Encode the features.
        """
        # Initialize the MinMaxScaler for the target only
        self.target_scaler = MinMaxScaler(feature_range=(0, 1))
        self.target_scaler.fit(self.shifted_df[self.target_features_list])

        # Initialize the MinMaxScaler for features only
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(self.shifted_df)
        self.scaled_df = pd.DataFrame(scaled_data, index=self.shifted_df.index, columns=self.shifted_df.columns)

    def update_df(self, df:pd.DataFrame) -> None:
        """
        Update the dataframe.
        """
        self.df = df
        self.prepare_data()

