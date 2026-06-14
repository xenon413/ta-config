import pandas as pd
import numpy as np
from typing import Optional

from .base_indicator import BaseIndicator

# Overveiw
# SMA2SMACrossStandard: complete
# CrossType: compete
# CrossVal: missing anchor, stream endpoint
# CrossValApprox: not implemented
# TrendType: missing anchor, stream endpoint
# WindowMin: missing stream endpoint
# WindowMax: missing stream endpoint

class SMA2SMACrossStandard(BaseIndicator):
    '''cross standard unit as the base series value'''
    @staticmethod
    def vector_endpoint(
            base_series:pd.Series[float], 
            sma1:pd.Series[float], window1:int, 
            sma2:pd.Series[float], window2:int
        )->pd.Series[float]:
        
        # case same window cross every kline
        if window1 == window2:
            return base_series.copy()
        
        # formula (check equation.pdf for derivation)
        dx = window1*window2*(sma2-sma1)/(window2-window1)
        return base_series+dx

    @staticmethod
    def anchor_endpoint(
            cur_base: float, 
            cur_sma1: float, window1: int, 
            cur_sma2: float, window2: int
        ) -> float:
        
        if window1 == window2:
            return cur_base
            
        dx = (window1 * window2 * (cur_sma2 - cur_sma1)) / (window2 - window1)
        return cur_base + dx

    @staticmethod
    def stream_endpoint(
            cur_base: float, 
            cur_sma1: float, window1: int, 
            cur_sma2: float, window2: int
        ) -> float:
        
        return SMA2SMACrossStandard.anchor_endpoint(
            cur_base, 
            cur_sma1, window1, 
            cur_sma2, window2
        )

class CrossType(BaseIndicator):
    @staticmethod
    def vector_endpoint(
            s1:pd.Series[float], 
            s2:pd.Series[float], 
            prev_s1:Optional[pd.Series[float]],
            prev_s2:Optional[pd.Series[float]],
            upper_bound:Optional[pd.Series[float]], 
            upper_standard:Optional[pd.Series[float]],
            lower_bound:Optional[pd.Series[float]], 
            lower_standard:Optional[pd.Series[float]]
        )->pd.Series[int]:

        # NOTE:
        # the standard and bound must be in the same units, 
        # and it's not required to be in the same unit as s1, s2
        
        # e.g.
        # sma25 and sma320 the can have a calculated cross standard in price
        # and the bound would be the high/low price

        # get the standard that's needed to cross
        upper_standard = upper_standard if upper_standard is not None else s2
        lower_standard = lower_standard if lower_standard is not None else s1
        
        # the drift within one kline if needed 
        upper_bound = upper_bound if upper_bound is not None else s1
        lower_bound = lower_bound if lower_bound is not None else s2

        # optional providing previous value
        # to eliminate duplication on shift calculation
        if prev_s1 is None:
            prev_s1 = s1.shift(1)
        if prev_s2 is None:
            prev_s2 = s2.shift(1)

        # bool series of if cross
        golden_cross = (prev_s1 <= prev_s2) & (upper_bound >= upper_standard)
        death_cross = (prev_s1 > prev_s2) & (lower_bound <= lower_standard)

        # merge golden and death 
        # golden 1, death -1, both/no_cross 0
        res = golden_cross.astype("int8") - death_cross.astype("int8")

        # overwrite both as 2
        res.loc[golden_cross & death_cross] = 2

        # fill the first na caused by shift and return 
        return res.fillna(0).astype(int)
    
    @staticmethod
    def anchor_endpoint(
            cur_s1:float, cur_s2:float,
            prev_s1:float, prev_s2:float,
            cur_upper_bound:Optional[float],
            cur_upper_standard:Optional[float],
            cur_lower_bound:Optional[float],
            cur_lower_standard:Optional[float],
        )->int:

        upper_standard = cur_upper_standard if cur_upper_standard is not None else cur_s2
        lower_standard = cur_lower_standard if cur_lower_standard is not None else cur_s1
        upper_bound = cur_upper_bound if cur_upper_bound is not None else cur_s1
        lower_bound = cur_lower_bound if cur_lower_bound is not None else cur_s2

        golden_cross = (prev_s1 <= prev_s2) and (upper_bound >= upper_standard)
        death_cross = (prev_s1 > prev_s2) and (lower_bound <= lower_standard)

        if golden_cross and death_cross:
            return 2
        if golden_cross:
            return 1
        if death_cross:
            return -1
        return 0

    @staticmethod
    def stream_endpoint(
            cur_s1:float, cur_s2:float,
            prev_s1:float, prev_s2:float,
            cur_upper_bound:Optional[float],
            cur_upper_standard:Optional[float],
            cur_lower_bound:Optional[float],
            cur_lower_standard:Optional[float],
        )->int:
        return CrossType.anchor_endpoint(
            cur_s1, cur_s2,
            prev_s1, prev_s2,
            cur_upper_bound,
            cur_upper_standard,
            cur_lower_bound,
            cur_lower_standard,
        )

class CrossVal(BaseIndicator):
    @staticmethod
    def vector_endpoint(
            s1:pd.Series[float], 
            s2:pd.Series[float], 
            base_series:pd.Series[float],
            cross_type:pd.Series[int],
            upper_bound:Optional[pd.Series[float]], 
            lower_bound:Optional[pd.Series[float]], 
            standard:Optional[pd.Series[float]],
        )->pd.Series[int]:
        
        # upper standard usually the same as the lower standard
        upper_standard = standard if standard is not None else s2
        lower_standard = standard if standard is not None else s1
        upper_bound = upper_bound if upper_bound is not None else s1
        lower_bound = lower_bound if lower_bound is not None else s2

        # NOTE: for sma the base series usually is open price
        golden_price = np.where(lower_bound > upper_standard, base_series, upper_standard)
        death_price = np.where(upper_bound < lower_standard, base_series, lower_standard)

        # TODO: resolve the missing cross_type == 2
        conditions = [
            (cross_type == 1),
            (cross_type == -1)
        ]
        choices = [golden_price, death_price]
        res = pd.Series(np.select(conditions, choices, default=0))
        return res
    
    @staticmethod
    def anchor_endpoint():...

    @staticmethod
    def stream_endpoint():...

class CrossValApprox(BaseIndicator):
    @staticmethod
    def vector_endpoint():...

    @staticmethod
    def anchor_endpoint():...

    @staticmethod
    def stream_endpoint():...

class TrendType(BaseIndicator):
    @staticmethod
    def vector_endpoint(
            upper_bound:pd.Series[float],
            lower_bound:pd.Series[float],
            thresh:float,
            trend_len:int,
            base_series:Optional[pd.Series[float]],
            prev_base_series:Optional[pd.Series[float]],
        ):

        if base_series is None and prev_base_series is None:
            raise ValueError("need to provide base_series or prev_base_series")
        
        if prev_base_series is None:
            prev_base_series = base_series.shift(1)

        long = upper_bound >= prev_base_series
        short = lower_bound < prev_base_series
        flat_upper = (upper_bound - prev_base_series).abs()/prev_base_series
        flat_lower = (lower_bound - prev_base_series).abs()/prev_base_series

        trend = pd.Series(0, index=prev_base_series.index, dtype="int8")
        trend[long] = 1
        trend[short] = -1
        trend[flat_upper < thresh] = 0
        trend[flat_lower < thresh] = 0

        if trend_len <= 2:
            return trend
        
        rolling_sum = trend.rolling(window=trend_len-1).sum()
        
        conditions = [
            (rolling_sum == trend_len-1),
            (rolling_sum == -(trend_len-1)),
        ]
        choices = [1, -1]

        candidate = pd.Series(np.select(conditions, choices, default=0), index=prev_base_series.index).shift(1)

        res = np.where(candidate == trend, trend, 0)
        res = pd.Series(res, index=prev_base_series.index)

        return res
    
    @staticmethod
    def anchor_endpoint():...

    @staticmethod
    def stream_endpoint():...        
    
class TrendVal(BaseIndicator):
    @staticmethod
    def vector_endpoint(
            lower_bound:pd.Series[float],
            upper_bound:pd.Series[float],
            upper
        ):
        pass
    
    @staticmethod
    def anchor_endpoint():...
    
    @staticmethod
    def stream_endpoint():...
    
class WindowMax(BaseIndicator):
    @staticmethod
    def vector_endpoint(base_series:pd.Series[float], window:int)->pd.Series[float]:
        return base_series.rolling(window).max()
        
    @staticmethod
    def anchor_endpoint(base_series:pd.Series[float], window:int)->float:
        return base_series.tail(window).max()

    @staticmethod
    def stream_endpoint():...
        
class WindowMin(BaseIndicator):
    @staticmethod
    def vector_endpoint(base_series:pd.Series[float], window:int):
        return base_series.rolling(window).min()
    
    @staticmethod
    def anchor_endpoint(base_series:pd.Series[float], window:int)->float:
        return base_series.tail(window).min()
    
    @staticmethod
    def stream_endpoint():...

