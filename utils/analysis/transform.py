import numpy as np
import pandas as pd
from scipy.fftpack import fft
from typing import Tuple
from .stats_test import adf_test


# Find the well degree of differentiation
def find_diff_well_deg(data:pd.Series, iterations:int=10) -> Tuple[pd.Series, int]:
    """
    Find the well degree of differentiation
    :param data: pd.Series -> input time series
    :param iterations: int -> number of iterations
    :return: pd.Series, int -> differentiated time series, degree of differentiation
    """
    ts = data.copy()
    deg = 0
    for i in range(1, iterations):
        ts = ts.diff().dropna()
        if adf_test(ts, verbose=False) == True:
            deg = i
            break
    return (ts, deg)

def analyze_fft(series:pd.Series) -> Tuple[np.ndarray, np.ndarray]:
    """
    Analyze the Fourier transform
    :param series: pd.Series -> time series
    :return: np.ndarray, np.ndarray -> frequencies, amplitudes
    """
    n = len(series)
    freq = np.fft.fftfreq(n)  # Associated frequencies
    fft_values = fft(series - series.mean())  # Centered FFT
    amplitudes = np.abs(fft_values)

    # Retain only positive frequencies
    positive_freq = freq[:n // 2]
    positive_amplitudes = amplitudes[:n // 2]

    return positive_freq, positive_amplitudes
