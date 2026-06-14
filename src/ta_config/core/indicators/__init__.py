import pandas as pd

from .sma import (
    SMACalc as _SMACalc, 
)
from .ema import EMACalc
from .macd import MACDCalc

class SMACalc(_SMACalc):
    @staticmethod
    def vector_endpoint(base_series:pd.Series[float], window:int):
        '''Processes an entire historical dataframe at once.'''
        return super().vector_endpoint(base_series, window)
    
    @staticmethod
    def anchor_endpoint(base_series:pd.Series[float], window:int):
        '''
        Calculates a single SMA point directly from raw prices.
        Used to establish the initial tracking state when no previous SMA exists.
        '''
        return super().anchor_endpoint(base_series, window)

    @staticmethod
    def stream_endpoint(last_sma:float, oldest_price:float, new_price:float, window:int):
        '''
        High-speed O(1) step update.
        Dependent on having the previous SMA value.
        '''
        return super().stream_endpoint(last_sma, oldest_price, new_price, window)


__all__ = [
    "SMACalc",
]