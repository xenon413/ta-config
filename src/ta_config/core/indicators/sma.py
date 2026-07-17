import pandas as pd
from typing import Optional

from .base_indicator import BaseIndicator

class SMACalc(BaseIndicator):
    @classmethod
    def vector_endpoint(
        cls,
        base_series:pd.Series, 
        window:int, 
        name:str
    )->pd.DataFrame:
        return base_series.rolling(window).mean().to_frame(name)
    
    @classmethod
    def stream_endpoint(
        cls,
        prev_sma:float, 
        prev_base:float, 
        cur_base:float, 
        window:int,
        name:str
    )->dict[str, float]:
        return {name:(prev_sma + (cur_base - prev_base) / window)}

    @classmethod
    def tail(
        cls, 
        base_series:pd.Series, 
        window:int, 
        name:str
    )->dict[str, float]:
        return {name:base_series.tail(window).mean()}
    
    @classmethod
    def stream_handler(
        cls,
        base_series:pd.Series,
        window:int,
        name:str,
        prev_df:pd.DataFrame,
        cur_row:dict[str, int|float]
    )->dict[str, float]:
        kwargs = {
            "prev_sma":prev_df[name].iloc[-1],
            "prev_base":base_series.iloc[-1],
            "cur_base":cur_row[base_series.name],
            "window":window,
            "name":name
        }
        return __class__.stream_endpoint(**kwargs)
        
class SMA2SMACrossStandard(BaseIndicator):
    @classmethod
    def vector_endpoint(
        cls,
        base_series:pd.Series, 
        sma1:pd.Series,
        sma2:pd.Series,
        window1:int,
        window2:int,
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
            cur_sma1: float,
            cur_sma2: float,
            window1: int, 
            window2: int,
            name:str
        ) -> dict[str, float]:
        
        if window1 == window2:
            return cur_base
            
        dx = (window1 * window2 * (cur_sma2 - cur_sma1)) / (window2 - window1)
        return {name:(cur_base + dx)}

    @classmethod
    def stream_handler(
        cls,
        base_series:pd.Series, 
        sma1:pd.Series,
        sma2:pd.Series,
        window1:int, 
        window2:int,
        name:str,
        prev_df:pd.DataFrame, 
        cur_row:dict[str, int|float]
    )->dict[str, float]:
        kwargs = {
            "cur_base":cur_row[base_series.name],
            "cur_sma1":cur_row[sma1.name],
            "window1":window1,
            "cur_sma2":cur_row[sma2.name],
            "window2":window2,
            "name":name
        }
        return __class__.stream_endpoint(**kwargs)
    
class SMATrendMaintVal(BaseIndicator):
    @classmethod
    def vector_endpoint(
        cls,
        base_series:pd.Series,
        sma:pd.Series,
        prev_sma:pd.Series,
        window:int,
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

    @classmethod
    def stream_handler(
        cls,
        base_series:pd.Series,
        sma:pd.Series,
        prev_sma:pd.Series,
        window:int,
        name:str,
        prev_df:pd.DataFrame,
        cur_row:dict[str, int|float]
    )->dict[str, float]:
        params = {
            "cur_base":cur_row[base_series.name],
            "cur_sma":cur_row[sma.name],
            "prev_sma":sma.iloc[-1],
            "window":window,
            "name":name,
        }
        return __class__.stream_endpoint(**params)

class SMAadjust(BaseIndicator):
    @classmethod
    def vector_endpoint(
        cls,
        base_series:pd.Series, 
        adj_series:pd.Series, 
        window:int,
        name:str
    )->pd.DataFrame:
        adjustment = (adj_series - base_series)/window
        return (base_series+adjustment).to_frame(name)

    @classmethod
    def stream_endpoint(
        cls, 
        cur_base:float, 
        cur_adj:float, 
        window:int, 
        name:str
    )->dict[str, float]:
        return {name:(cur_base+(cur_adj-cur_base)/window)}

    @classmethod
    def stream_handler(
        cls,
        base_series:pd.Series, 
        adj_series:pd.Series, 
        window:int,
        name:str,
        prev_df:pd.DataFrame,
        cur_row:dict[str, int|float]
    )->dict[str, float]:
        kwargs = {
            "cur_base":cur_row[base_series.name],
            "cur_adj":cur_row[adj_series.name],
            "window":window,
            "name":name
        }
        return __class__.stream_endpoint(**kwargs)
