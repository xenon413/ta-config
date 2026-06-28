import pandas as pd
from typing import Optional

from .base_indicator import BaseIndicator

class SMACalc(BaseIndicator):
    
    @classmethod
    def vector_endpoint(
            cls,
            base_series:pd.Series[float], 
            window:int, 
            name:str
        )->pd.DataFrame:
        return base_series.rolling(window).mean().to_frame(name)
    
    @classmethod
    def stream_endpoint(
            cls,
            prev_sma:float, 
            last_base:float, 
            cur_base:float, 
            window:int,
            name:str
        )->dict[str, float]:
        return {name:(prev_sma + (cur_base - last_base) / window)}

    @classmethod
    def tail(cls, base_series:pd.Series[float], window:int, name:str)->dict[str, float]:
        return {name:base_series.tail(window).mean()}
    
class SMA2SMACrossStandard(BaseIndicator):
    @classmethod
    def vector_endpoint(
            cls,
            base_series:pd.Series[float], 
            sma1:pd.Series[float], window1:int, 
            sma2:pd.Series[float], window2:int,
            name:str
        )->pd.DataFrame:
        
        # case same window cross every kline
        if window1 == window2:
            return base_series.copy()
        
        # formula (check equation.pdf for derivation)
        dx = window1*window2*(sma2-sma1)/(window2-window1)
        return (base_series+dx).to_frame(name)

    @classmethod
    def stream_endpoint(
            cls,
            cur_base: float, 
            cur_sma1: float, window1: int, 
            cur_sma2: float, window2: int,
            name:str
        ) -> dict[str, float]:
        
        if window1 == window2:
            return cur_base
            
        dx = (window1 * window2 * (cur_sma2 - cur_sma1)) / (window2 - window1)
        return {name:(cur_base + dx)}

class SMATrendMaintVal(BaseIndicator):
    @classmethod
    def vector_endpoint(
            cls,
            sma:pd.Series[float],
            window:int,
            base_series:pd.Series[float], 
            prev_sma:pd.Series[float],
            name:str
        )->pd.DataFrame:
        return (base_series+window*(prev_sma-sma)).to_frame(name)

    @classmethod
    def stream_endpoint(
            cls,
            cur_base:float,
            cur_sma:float, 
            prev_sma:float, 
            window:int,
            name:str
        )->dict[str, float]:
        return {name:(cur_base + window*(prev_sma-cur_sma))} 

class SMAadjust(BaseIndicator):
    @classmethod
    def vector_endpoint(
            cls,
            base_series:pd.Series[float], 
            adj_series:pd.Series[float], 
            window:int,
            name:str
        )->pd.DataFrame:
        adjustment = (adj_series - base_series)/window
        return (base_series+adjustment).to_frame(name)

    @classmethod
    def stream_endpoint(cls, cur_base:float, cur_adj:float, window:int, name:str)->dict[str, float]:
        return {name:(cur_base+(cur_adj-cur_base)/window)}
