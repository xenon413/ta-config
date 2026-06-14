import pandas as pd
from typing import Optional

from .base_indicator import BaseIndicator
# Overveiw
# SMACalc: complete
# SMATrendMaintVal: missing anchor, stream endpoint
# SMAadjust: missing anchor, stream endpoint

class SMACalc(BaseIndicator):
    @staticmethod
    def vector_endpoint(base_series:pd.Series[float], window:int)->pd.Series[float]:
        return base_series.rolling(window).mean()
    
    @staticmethod
    def anchor_endpoint(base_series:pd.Series[float], window:int)->float:
        return base_series.tail(window).mean()
    
    @staticmethod
    def stream_endpoint(prev_sma:float, last_base:float, cur_base:float, window:int)->float:
        return prev_sma + (cur_base - last_base) / window

class SMATrendMaintVal(BaseIndicator):
    @staticmethod
    def vector_endpoint(
            sma:pd.Series[float],
            window:int,
            base_series:pd.Series[float], 
            prev_sma:Optional[pd.Series[float]]
        ):
        if prev_sma is None:
            prev_sma = sma.shift(1)

        return (base_series+window*(prev_sma-sma))

    @staticmethod
    def anchor_endpoint():...

    @staticmethod
    def stream_endpoint():...  

class SMAadjust(BaseIndicator):
    @staticmethod
    def vector_endpoint(base_series:pd.Series[float], adj_series:pd.Series[float], window:int):
        adjustment = (adj_series - base_series)/window
        return base_series+adjustment

    @staticmethod
    def anchor_endpoint():...

    @staticmethod
    def stream_endpoint():...  

