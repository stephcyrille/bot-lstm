import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler


class TreadingDataset:
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
        self._calculate_indicators()
        self._add_shifted_features()
        self._encoding_features()
        self._create_sequence()
    
    def update_df(self, new_df:pd.DataFrame) -> None:
        """
        Update the dataframe.
        
        Parameters:
        ---
        - new_df (pd.DataFrame): The new dataframe.
        """
        self.df = new_df
        self.prepare_data()
    
    def calculate_atr(self, data:pd.DataFrame, period:int=14) -> None:
        """
        The Average True Range (ATR) is a technical analysis indicator that measures market volatility 
        by decomposing the entire range of an asset price for that period. It is typically derived from 
        the 14-day simple moving average of a series of true range indicators.
        Parameters:
        ---
        - period (int): The number of periods to use for calculating the ATR. Default is 14.
        """
        # Check if the columns are present
        if 'HIGH' not in data.columns or 'LOW' not in data.columns or 'CLOSE' not in data.columns:
            raise ValueError('The dataframe must have the columns HIGH, LOW and CLOSE.')

        # Check if the ATR column is already present
        if 'ATR' in self.df.columns:
            return

        data['High-Low'] = data['HIGH'] - data['LOW']
        data['High-Close'] = abs(data['HIGH'] - data['CLOSE'].shift(1))
        data['Low-Close'] = abs(data['LOW'] - data['CLOSE'].shift(1))
        
        tr = data[['High-Low', 'High-Close', 'Low-Close']].max(axis=1)
        atr = tr.rolling(window=period).mean()
        data['ATR'] = atr
        
        self.df = self.df.merge(data[['ATR']], how='inner', left_index=True, right_index=True)
        self.df.dropna(inplace=True)

    def _calculate_indicators(self) -> None:
        """
        Calculate the indicators.
        """
        self._calculate_ema()
        self._calculate_rsi()
        self._calculate_macd()
        self._calculate_bollinger_bands()
        
        # Remove the NA values
        self.df = self.df.iloc[40:]
        # Replace the index from the next day to the end of the dataset
        first_index = self.df.index[0]
        self.df = self.df.loc[first_index + pd.Timedelta(hours=(24 - first_index.hour)):]
    
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

    def _calculate_bollinger_bands(self, close_field:str=CLOSE_FIELD, window:int=20) -> None:
        """
        Calculate Bollinger Bands for a given dataframe.
        
        Parameters:
        ---
        - df (pd.DataFrame): DataFrame containing the closing prices.
        - window (int): The window size for the moving average and standard deviation.
        """
        self.df['MA'] = self.df[close_field].rolling(window=window).mean()
        self.df['STD'] = self.df[close_field].rolling(window=window).std()
        self.df['UPPER_BAND'] = self.df['MA'] + (self.df['STD'] * 2)
        self.df['LOWER_BAND'] = self.df['MA'] - (self.df['STD'] * 2)
        self.df['BOLLINGER_PERCENT_B'] = (self.df[close_field] - self.df['LOWER_BAND']) / (self.df['UPPER_BAND'] - self.df['LOWER_BAND'])
        self.df.drop(['MA', 'STD'], axis=1, inplace=True)

    def _calculate_ema(self, span:int=20, close_field:str=CLOSE_FIELD, indicator_field_name:str='EMA') -> None:
        """
        Calculate the Exponential Moving Average (EMA) for a given column in the dataframe.
        
        Parameters:
        ---
        - span (int): The span for the EMA calculation.
        - close_field (str): The column name for which to calculate the EMA. Default is 'CLOSE'.
        - indicator_field_name (str): The name of the new column to store the EMA values. Default is 'EMA'.
        """
        self.df[indicator_field_name] = self.df[close_field].ewm(span=span, adjust=False).mean()
    
    def _calculate_macd(self, column:str=CLOSE_FIELD, extra_field:bool=False,
                       long_span:int=26, short_span:int=12, signal_span:int=9) -> None:
        """
        Calculate the MACD (Moving Average Convergence Divergence) for a given column in the dataframe.
        
        Parameters:
        ---
        - column (str): The column name for which to calculate the MACD. Default is 'CLOSE'.
        - long_span (int): The long span for the EMA calculation. Default is 26.
        - extra_field (bool): Whether to keep the intermediate EMA columns. Default is False.
        - short_span (int): The short span for the EMA calculation. Default is 12.
        - signal_span (int): The span for the signal line EMA calculation. Default is 9.
        """
        self.df['EMA_SHORT'] = self.df[column].ewm(span=short_span, adjust=False).mean()
        self.df['EMA_LONG'] = self.df[column].ewm(span=long_span, adjust=False).mean()
        self.df['MACD'] = self.df['EMA_SHORT'] - self.df['EMA_LONG']
        self.df['SIGNAL_LINE'] = self.df['MACD'].ewm(span=signal_span, adjust=False).mean()

        if not extra_field:
            self.df.drop(['EMA_SHORT', 'EMA_LONG'], axis=1, inplace=True)
    
    def _calculate_rsi(self, period:int=14, column:str=CLOSE_FIELD, indicator_field_name:str='RSI') -> None:  
        """
        Calculate the Relative Strength Index (RSI) for a given column in the dataframe.
        
        Parameters:
        ---
        - period (int): The period for the RSI calculation. Default is 14.
        - column (str): The column name for which to calculate the RSI. Default is 'CLOSE'.
        - indicator_field_name (str): The name of the new column to store the RSI values. Default is 'RSI'.
        """
        delta = self.df[column].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        self.df[indicator_field_name] = 100 - (100 / (1 + rs))
