import pandas as pd
import numpy as np
from typing import Optional

from .base_indicator import BaseIndicator

class CrossType(BaseIndicator):
    @classmethod
    def vector_endpoint(
        cls,
        s1:pd.Series, 
        s2:pd.Series, 
        prev_s1:pd.Series,
        prev_s2:pd.Series,
        upper_bound:Optional[pd.Series], 
        lower_bound:Optional[pd.Series], 
        upper_standard:Optional[pd.Series],
        lower_standard:Optional[pd.Series],
        name:str
    )->pd.DataFrame:
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

        # bool series of if cross
        golden_cross = (prev_s1 <= prev_s2) & (upper_bound >= upper_standard)
        death_cross = (prev_s1 > prev_s2) & (lower_bound <= lower_standard)

        # merge golden and death 
        # golden 1, death -1, both/no_cross 0
        res = golden_cross.astype("int8") - death_cross.astype("int8")

        # overwrite both as 2
        res.loc[golden_cross & death_cross] = 2

        # fill the first na caused by shift and return 
        return res.fillna(0).astype(int).to_frame(name)
    
    @classmethod
    def stream_endpoint(
        cls,
        cur_s1:float, cur_s2:float,
        prev_s1:float, prev_s2:float,
        cur_upper_bound:Optional[float],
        cur_upper_standard:Optional[float],
        cur_lower_bound:Optional[float],
        cur_lower_standard:Optional[float],
        name:str
    )->dict[str, int]:
        upper_standard = cur_upper_standard if cur_upper_standard is not None else cur_s2
        lower_standard = cur_lower_standard if cur_lower_standard is not None else cur_s1
        upper_bound = cur_upper_bound if cur_upper_bound is not None else cur_s1
        lower_bound = cur_lower_bound if cur_lower_bound is not None else cur_s2

        golden_cross = (prev_s1 <= prev_s2) and (upper_bound >= upper_standard)
        death_cross = (prev_s1 >= prev_s2) and (lower_bound <= lower_standard)

        res = 0
        res = 1 if golden_cross else res
        res = -1 if death_cross else res
        res = 2 if golden_cross and death_cross else res

        return {name:res}

    @classmethod
    def stream_handler(
        cls,
        s1:pd.Series, 
        s2:pd.Series, 
        prev_s1:pd.Series,
        prev_s2:pd.Series,
        upper_bound:Optional[pd.Series], 
        lower_bound:Optional[pd.Series], 
        upper_standard:Optional[pd.Series],
        lower_standard:Optional[pd.Series],
        name:str,
        prev_df:pd.DataFrame,
        cur_row:dict[str, int|float]
    )->dict[str, float]:
        kwargs = {
            "cur_s1":cur_row[s1.name],
            "cur_s2":cur_row[s2.name],
            "prev_s1":prev_s1.iloc[-1],
            "prev_s2":prev_s2.iloc[-1],
            "cur_upper_bound":None if upper_bound is None else cur_row[upper_bound.name],
            "cur_upper_standard":None if upper_standard is None else cur_row[upper_standard.name],
            "cur_lower_bound":None if lower_bound is None else cur_row[lower_bound.name],
            "cur_lower_standard":None if lower_standard is None else cur_row[lower_standard.name],
            "name":name
        }
        return __class__.stream_endpoint(**kwargs)

class CrossVal(BaseIndicator):
    @classmethod
    def vector_endpoint(
        cls,
        s1:pd.Series,
        s2:pd.Series,
        base_series:pd.Series,
        cross_type:pd.Series,
        upper_bound:Optional[pd.Series], 
        lower_bound:Optional[pd.Series], 
        upper_standard:Optional[pd.Series],
        lower_standard:Optional[pd.Series],
        name:str
    )->pd.DataFrame:
        # upper standard usually the same as the lower standard
        upper_standard = upper_standard if upper_standard is not None else s2
        lower_standard = lower_standard if lower_standard is not None else s1
        upper_bound = upper_bound if upper_bound is not None else s1
        lower_bound = lower_bound if lower_bound is not None else s2

        # NOTE: for sma the base series usually is open price
        # when crossed violently it could happen that the whole kline price range is above the standard,
        # use the base series when it happen and use the standard when normal
        golden_price = np.where(lower_bound > upper_standard, base_series, upper_standard)
        death_price = np.where(upper_bound < lower_standard, base_series, lower_standard)

        # NOTE: when cross_type == 2 there's at least two cross in one kline
        # we simply ignore that valuees for now
        conditions = [
            (cross_type == 1),
            (cross_type == -1)
        ]
        choices = [golden_price, death_price]
        res = pd.Series(np.select(conditions, choices, default=0))
        return res.to_frame(name)

    @classmethod
    def stream_endpoint(
        cls,
        cur_s1:float,
        cur_s2:float,
        cur_base:float,
        cur_cross_type:int,
        cur_upper_bound:Optional[float],
        cur_lower_bound:Optional[float],
        cur_upper_standard:Optional[float],
        cur_lower_standard:Optional[float],
        name:str
    )->dict[str, float]:
        
        cur_upper_standard = cur_upper_standard if cur_upper_standard is not None else cur_s2
        cur_lower_standard = cur_lower_standard if cur_lower_standard is not None else cur_s1
        cur_upper_bound = cur_upper_bound if cur_upper_bound is not None else cur_s1
        cur_lower_bound = cur_lower_bound if cur_lower_bound is not None else cur_s2

        # standard_val = (cur_upper_standard + cur_lower_standard)/2
        golden_price = cur_base if cur_lower_bound > cur_upper_standard else cur_upper_standard
        death_price = cur_base if cur_upper_bound < cur_lower_standard else cur_lower_standard

        res = 0.0
        res = golden_price if cur_cross_type == 1 else res
        res = death_price if cur_cross_type == -1 else res

        return {name:res}

    @classmethod
    def stream_handler(
        cls,
        s1:pd.Series,
        s2:pd.Series,
        base_series:pd.Series,
        cross_type:pd.Series,
        upper_bound:Optional[pd.Series], 
        lower_bound:Optional[pd.Series], 
        upper_standard:Optional[pd.Series],
        lower_standard:Optional[pd.Series],
        name:str,
        prev_df:pd.DataFrame,
        cur_row:dict[str, int|float]
    )->dict[str, float]:
        kwargs = {
            "cur_s1":cur_row[s1.name],
            "cur_s2":cur_row[s2.name],
            "cur_base":cur_row[base_series.name],
            "cur_cross_type":cur_row[cross_type.name],
            "cur_upper_bound":None if upper_bound is None else cur_row[upper_bound.name],
            "cur_upper_standard":None if upper_standard is None else cur_row[upper_standard.name],
            "cur_lower_bound":None if lower_bound is None else cur_row[lower_bound.name],
            "cur_lower_standard":None if lower_standard is None else cur_row[lower_standard.name],
            "name":name
        }
        return __class__.stream_endpoint(**kwargs)
    
class TrendType(BaseIndicator):
    @classmethod
    def vector_endpoint(
        cls,
        prev_base_series:pd.Series,
        upper_bound:pd.Series,
        lower_bound:pd.Series,
        thresh:float,
        trend_len:int,
        name:str
    )->pd.DataFrame:
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

        return res.to_frame(name)

    @classmethod
    def tail(
        cls,
        prev_base_series:pd.Series,
        upper_bound:pd.Series,
        lower_bound:pd.Series,
        thresh:float,
        trend_len:int,
        name:str
    )->dict[str, int]:
        # trim everything to trend len
        upper_bound = upper_bound.tail(trend_len)
        lower_bound = lower_bound.tail(trend_len)
        prev_base_series = prev_base_series.tail(trend_len)

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
            return trend.iloc(-1),  

        tail_sum = trend.tail(trend_len-1).sum()

        res = 0
        res = 1 if tail_sum == trend_len-1 else res
        res = -1 if tail_sum == -(trend_len-1) else res

        return {name:res}

    @classmethod
    def stream_endpoint(
        cls,
        prev_base_series:pd.Series,
        upper_bound:pd.Series,
        lower_bound:pd.Series,
        thresh:float,
        trend_len:int,
        name:str
    )->dict[str, int]:
        # NOTE: use tail endpoint for now 
        # TODO: write O(1) implementation
        return cls.tail(prev_base_series, upper_bound, lower_bound, thresh, trend_len, name)
    
    @classmethod
    def stream_handler(
        cls,
        prev_base_series:pd.Series,
        upper_bound:pd.Series,
        lower_bound:pd.Series,
        thresh:float,
        trend_len:int,
        name:str,
        prev_df:pd.DataFrame,
        cur_row:dict[str, int|float]
    )->dict[str, int]:
        kwargs = {
            "prev_base_series":prev_base_series,
            "upper_bound":upper_bound,
            "lower_bound":lower_bound,
            "thresh":thresh,
            "trend_len":trend_len,
            "name":name
        }
        return __class__.stream_endpoint(**kwargs)
    
class TrendVal(BaseIndicator):
    @classmethod
    def vector_endpoint(
        cls,
        base_series:pd.Series,
        upper_bound:pd.Series,
        lower_bound:pd.Series,
        upper_standard:pd.Series,
        lower_standard:pd.Series,
        trend_type:pd.Series,
        name:str
    )->pd.DataFrame:
        upper_val = np.where(lower_bound>upper_standard, base_series, upper_standard)
        upper_val = np.where(upper_bound<upper_standard, 0, upper_val)

        lower_val = np.where(upper_bound<lower_standard, base_series, lower_standard)
        lower_val = np.where(lower_bound>lower_bound, base_series, lower_val)

        conditions = [
            (trend_type==1),
            (trend_type==-1)
        ]
        choices = [upper_val, lower_val]
        res = pd.Series(np.select(conditions, choices, default=0))
        return res.to_frame(name)
    
    @classmethod
    def stream_endpoint(
        cls,
        cur_upper_bound:float,
        cur_lower_bound:float,
        cur_upper_standard:float,
        cur_lower_standard:float,
        cur_trend_type:int,
        cur_base:float,
        name:str
    )->dict[str, float]:
        upper_val = cur_base if cur_lower_bound>cur_upper_standard else cur_upper_standard
        upper_val = 0 if cur_upper_bound<cur_upper_standard else upper_val

        lower_val = cur_base if cur_upper_bound<cur_lower_standard else cur_lower_standard
        lower_val = 0 if cur_lower_bound>cur_lower_standard else lower_val

        res = 0
        res = upper_val if cur_trend_type == 1 else res
        res = lower_val if cur_trend_type == -1 else res

        return {name:res} 
    
    @classmethod
    def stream_handler(
        cls,
        base_series:pd.Series,
        upper_bound:pd.Series,
        lower_bound:pd.Series,
        upper_standard:pd.Series,
        lower_standard:pd.Series,
        trend_type:pd.Series,
        name:str,
        prev_df:pd.DataFrame,
        cur_row:dict[str, int|float]
    )->dict[str, float]:
        kwargs = {
            "cur_upper_bound":cur_row[upper_bound.name],
            "cur_upper_standard":cur_row[upper_standard.name],
            "cur_lower_bound":cur_row[lower_bound.name],
            "cur_lower_standard":cur_row[lower_standard.name],
            "cur_trend_type":cur_row[trend_type.name],
            "cur_base":cur_row[base_series.name],
            "name":name
        }
        return __class__.stream_endpoint(**kwargs)
    
class WindowMax(BaseIndicator):
    @classmethod
    def vector_endpoint(
        cls, 
        base_series:pd.Series, 
        window:int, 
        name:str
    )->pd.DataFrame:
        return base_series.rolling(window).max().to_frame(name)
        
    @classmethod
    def tail(
        cls, 
        base_series:pd.Series, 
        window:int, 
        name:str
    )->dict[str, float]:
        return {name:base_series.tail(window).max()}

    @classmethod
    def stream_endpoint(
        cls, 
        base_series:pd.Series, 
        window:int, 
        name:str
    )->dict[str, float]:
        # NOTE: use tail endpoint for now 
        # TODO: write O(1) implementation
        return cls.tail(base_series, window, name)
        
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
            "base_series":base_series,
            "window":window,
            "name":name
        }
        return __class__.stream_endpoint(**kwargs)
    
class WindowMin(BaseIndicator):
    @classmethod
    def vector_endpoint(
        cls, 
        base_series:pd.Series, 
        window:int, 
        name:str
    )->pd.DataFrame:
        return base_series.rolling(window).min().to_frame(name)
    
    @classmethod
    def tail(
        cls, 
        base_series:pd.Series, 
        window:int, 
        name:str
    )->dict[str, float]:
        return {name:base_series.tail(window).min()}
    
    @classmethod
    def stream_endpoint(
        cls, 
        base_series:pd.Series, 
        window:int, 
        name:str
    )->dict[str, float]:
        # NOTE: use tail endpoint for now 
        # TODO: write O(1) implementation
        return cls.tail(base_series, window, name)

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
            "base_series":base_series,
            "window":window,
            "name":name
        }
        return __class__.stream_endpoint(**kwargs)
    
class Shift(BaseIndicator):
    @classmethod
    def vector_endpoint(
        cls, 
        base_series:pd.Series, 
        period:int, 
        name:str
    )->pd.DataFrame:
        return base_series.shift(period).to_frame(name)
    
    @classmethod
    def tail(
        cls, 
        base_series:pd.Series, 
        period:int, 
        name:str
    )->dict[str, float]:
        return {name:base_series.iloc[-(period+1)]}
    
    @classmethod
    def stream_endpoint(
        cls, 
        base_series:pd.Series, 
        period:int, 
        name:str
    )->dict[str, float]:
        return cls.tail(base_series, period, name)
    

    @classmethod
    def stream_handler(
        cls, 
        base_series:pd.Series, 
        period:int, 
        name:str,
        prev_df:pd.DataFrame,
        cur_row:dict[str, int|float]
    )->dict[str, float]:
        kwargs = {
            "base_series":base_series,
            "period":period,
            "name":name
        }
        return __class__.stream_endpoint(**kwargs)