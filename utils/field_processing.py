import pandas as pd

def create_ts_from_df(df:pd.DataFrame, date_col:str, time_col:str, ts_col_name:str) -> pd.DataFrame:
    """
    Create a time series from a dataframe
    :param df: input dataframe
    :param ts_name: name of the time series
    :param date_col: column name for date
    :param time_col: column name for time
    :param ts_col_name: column name for time series
    :return: time series
    """
    ts = df.copy()
    ts[ts_col_name] = pd.to_datetime(ts[date_col] + ' ' + ts[time_col])
    ts.set_index(ts_col_name, inplace=True)
    ts.drop(columns=[date_col, time_col], inplace=True)
    return ts