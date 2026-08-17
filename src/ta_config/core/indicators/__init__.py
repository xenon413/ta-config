import pandas as pd
from typing import Optional

from .sma import (
    SMACalc as _SMACalc, 
    SMA2SMACrossStandard as _SMA2SMACrossStandard,
    SMATrendMaintVal as _SMATrendMaintVal,
    SMAadjust as _SMAadjust
)
from .ema import (
    EMACalc as _EMACalc,
)
from .macd import (
    MACDCalc as _MACDCalc,
)
from .relation import (
    CrossType as _CrossType,
    CrossVal as _CrossVal,
    TrendType as _TrendType,
    TrendVal as _TrendVal,
    WindowMax as _WindowMax,
    WindowMin as _WindowMin,
    Shift as _Shift,
    RelativePosition as _RelativePosition
)

# ---- from .sma ----
class SMACalc(_SMACalc):
    """
    Calculates the Simple Moving Average (SMA).
    """

    name = "sma_calc"
    @classmethod
    def vector_endpoint(
        cls,
        base_series:pd.Series,
        window:int, 
        name:Optional[str]=None
    )->pd.DataFrame:
        """
        Execute historical vectorized matrix calculations for SMA.
        
        Args:
            base_series (pd.Series[float]): The input series to calculate SMA for.
            window (int): The rolling window size.
            name (str): The column name for the output DataFrame. Defaults to "sma".
            
        Returns:
            pd.DataFrame: A DataFrame containing the calculated SMA.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().vector_endpoint(
            base_series=base_series, 
            window=window, 
            name=names[0]
        )
    
    @classmethod
    def stream_endpoint(
        cls,
        prev_sma:float, 
        prev_base:float, 
        cur_base:float, 
        window:int, 
        name:Optional[str]=None
    )->dict[str, float]:
        """
        Compute the next step SMA using a low-latency O(1) recursive equation.
        
        Args:
            last_sma (float): The previous SMA value.
            oldest_price (float): The oldest price dropping out of the window (last_base).
            new_price (float): The current price entering the window (cur_base).
            window (int): The rolling window size.
            name (str): The key name for the output dictionary. Defaults to "sma".
            
        Returns:
            dict[str, float]: A dictionary with the computed SMA.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().stream_endpoint(
            prev_sma=prev_sma, 
            prev_base=prev_base, 
            cur_base=cur_base, 
            window=window, 
            name=names[0]
        )

    @classmethod
    def stream_handler(
        cls,
        base_series:pd.Series,
        window:int,
        prev_df:pd.DataFrame,
        cur_row:dict[str, int|float],
        name:Optional[str]=None,
    )->dict[str, float]:
        """
        Process the next stream step SMA using the previous DataFrame state.
        
        Args:
            base_series (pd.Series[float]): The input series history.
            window (int): The rolling window size.
            name (str): The key name for the output dictionary. Defaults to "sma_calc".
            prev_df (pd.DataFrame): The previous DataFrame state.
            cur_row (dict[str, int | float]): The current row values.
            
        Returns:
            dict[str, float]: A dictionary with the computed SMA.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().stream_handler(
            base_series=base_series,
            window=window,
            name=names[0],
            prev_df=prev_df,
            cur_row=cur_row
        )

    @classmethod
    def tail(
        cls, 
        base_series:pd.Series, 
        window:int, 
        name:Optional[str]=None
    )->dict[str, float]:
        """
        Calculate the SMA for the tail of a series.
        
        Args:
            base_series (pd.Series[float]): The input series.
            window (int): The rolling window size.
            name (str): The key name for the output dictionary. Defaults to "sma".
            
        Returns:
            dict[str, float]: A dictionary with the computed tail SMA.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().tail(
            base_series=base_series, 
            window=window, 
            name=names[0]
        )
    
class SMA2SMACrossStandard(_SMA2SMACrossStandard):
    """
    Calculates the cross standard unit as the base series value for two SMAs.
    Determines the price level required for two moving averages to cross in the next step.
    """

    name = "sma2sma_cross_standard"
    @classmethod
    def vector_endpoint(
        cls, 
        base_series:pd.Series,
        sma1:pd.Series, 
        window1:int, 
        sma2:pd.Series, 
        window2:int, 
        name:Optional[str]=None
    )->pd.DataFrame:
        """
        Execute historical vectorized calculations for SMA cross standards.
        
        Args:
            base_series (pd.Series[float]): The base price series.
            sma1 (pd.Series[float]): The first SMA series.
            window1 (int): The window size of the first SMA.
            sma2 (pd.Series[float]): The second SMA series.
            window2 (int): The window size of the second SMA.
            name (str): The column name for the output DataFrame. Defaults to "sma2sma_cross_standard".
            
        Returns:
            pd.DataFrame: A DataFrame containing the cross standard values.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().vector_endpoint(
            base_series=base_series,
            sma1=sma1,
            window1=window1,
            sma2=sma2,
            window2=window2,
            name=names[0]
        )
    
    @classmethod
    def stream_endpoint(
        cls, 
        cur_base:float,
        cur_sma1:float,
        window1:int,
        cur_sma2:float,
        window2:int,
        name:Optional[str]=None
    )->dict[str, float]:
        """
        Compute the next step SMA cross standard using O(1) math.
        
        Args:
            cur_base (float): The current base price.
            cur_sma1 (float): The current value of the first SMA.
            window1 (int): The window size of the first SMA.
            cur_sma2 (float): The current value of the second SMA.
            window2 (int): The window size of the second SMA.
            name (str): The key name for the output dictionary. Defaults to "sma2sma_cross_standard".
            
        Returns:
            dict[str, float]: A dictionary with the computed cross standard value.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().stream_endpoint(
            cur_base=cur_base,
            cur_sma1=cur_sma1,
            window1=window1,
            cur_sma2=cur_sma2,
            window2=window2,
            name=names[0]
        )

    @classmethod
    def stream_handler(
        cls,
        base_series:pd.Series,
        sma1:pd.Series,
        sma2:pd.Series,
        window1:int,
        window2:int,
        prev_df:pd.DataFrame,
        cur_row:dict[str, int|float],
        name:Optional[str]=None,
    )->dict[str, float]:
        """
        Process the next stream step SMA cross standard using the previous DataFrame state.
        
        Args:
            base_series (pd.Series[float]): The base price series.
            sma1 (pd.Series[float]): The first SMA series.
            sma2 (pd.Series[float]): The second SMA series.
            window1 (int): The window size of the first SMA.
            window2 (int): The window size of the second SMA.
            name (str): The key name for the output dictionary. Defaults to "sma2sma_cross_standard".
            prev_df (pd.DataFrame): The previous DataFrame state.
            cur_row (dict[str, int | float]): The current row values.
            
        Returns:
            dict[str, float]: A dictionary with the computed cross standard value.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().stream_handler(
            base_series=base_series,
            sma1=sma1,
            sma2=sma2,
            window1=window1,
            window2=window2,
            name=names[0],
            prev_df=prev_df,
            cur_row=cur_row
        )
    
class SMATrendMaintVal(_SMATrendMaintVal):
    """
    Calculates the base value required to maintain the current SMA trend.
    """

    name = "sma_trend_maint_val"
    @classmethod
    def vector_endpoint(
        cls, 
        sma:pd.Series,
        prev_sma:pd.Series,
        window:int,
        base_series:pd.Series,
        name:Optional[str]=None
    )->pd.DataFrame:
        """
        Execute historical vectorized calculations for SMA trend maintenance value.
        
        Args:
            sma (pd.Series[float]): The current SMA series.
            window (int): The rolling window size.
            base_series (pd.Series[float]): The base price series.
            prev_sma (pd.Series[float]): The previous step's SMA series.
            name (str): The column name for the output DataFrame. Defaults to "sma_trend_maint_val".
            
        Returns:
            pd.DataFrame: A DataFrame containing the trend maintenance values.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().vector_endpoint(
            sma=sma,
            window=window,
            base_series=base_series,
            prev_sma=prev_sma,
            name=names[0]
        )

    @classmethod
    def stream_endpoint(
        cls, 
        cur_base:float, 
        cur_sma:float, 
        prev_sma:float,
        window:int,
        name:Optional[str]=None
    )->dict[str, float]:
        """
        Compute the next step SMA trend maintenance value using O(1) math.
        
        Args:
            cur_base (float): The current base price.
            cur_sma (float): The current SMA value.
            prev_sma (float): The previous SMA value.
            window (int): The rolling window size.
            name (str): The key name for the output dictionary. Defaults to "sma_trend_maint_val".
            
        Returns:
            dict[str, float]: A dictionary with the computed trend maintenance value.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().stream_endpoint(
            cur_base=cur_base,
            cur_sma=cur_sma,
            prev_sma=prev_sma,
            window=window,
            name=names[0]
        )

    @classmethod
    def stream_handler(
        cls,
        base_series:pd.Series,
        sma:pd.Series,
        prev_sma:pd.Series,
        window:int,
        prev_df:pd.DataFrame,
        cur_row:dict[str, int|float],
        name:Optional[str]=None,
    )->dict[str, float]:
        """
        Process the next stream step SMA trend maintenance value using the previous DataFrame state.
        
        Args:
            base_series (pd.Series[float]): The base price series.
            sma (pd.Series[float]): The current SMA series.
            prev_sma (pd.Series[float]): The previous step's SMA series.
            window (int): The rolling window size.
            name (str): The key name for the output dictionary. Defaults to "sma_trend_maint_val".
            prev_df (pd.DataFrame): The previous DataFrame state.
            cur_row (dict[str, int | float]): The current row values.
            
        Returns:
            dict[str, float]: A dictionary with the computed trend maintenance value.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().stream_handler(
            base_series=base_series,
            sma=sma,
            prev_sma=prev_sma,
            window=window,
            name=names[0],
            prev_df=prev_df,
            cur_row=cur_row
        )

class SMAadjust(_SMAadjust):
    """
    Adjusts the SMA based on an adjustment series.
    """

    name = "sma_adjust"
    @classmethod
    def vector_endpoint(
        cls, 
        base_series:pd.Series,
        adj_series:pd.Series,
        window:int,
        name:Optional[str]=None
    )->pd.DataFrame:
        """
        Execute historical vectorized matrix calculations for SMA adjustment.
        
        Args:
            base_series (pd.Series[float]): The base price series.
            adj_series (pd.Series[float]): The adjustment series.
            window (int): The rolling window size.
            name (str): The column name for the output DataFrame. Defaults to "sma_adjust".
            
        Returns:
            pd.DataFrame: A DataFrame containing the adjusted SMA values.
        """

        name = name or cls.name
        names = cls.output_keys(name)
        return super().vector_endpoint(
            base_series=base_series,
            adj_series=adj_series,
            window=window,
            name=names[0]
        )

    @classmethod
    def stream_endpoint(
        cls, 
        cur_base:float, 
        cur_adj:float, 
        window:int, 
        name:Optional[str]=None
    )->dict[str, float]:
        """
        Compute the next step SMA adjustment value using O(1) math.
        
        Args:
            cur_base (float): The current base price.
            cur_adj (float): The current adjustment value.
            window (int): The rolling window size.
            name (str): The key name for the output dictionary. Defaults to "sma_adjust".
            
        Returns:
            dict[str, float]: A dictionary with the computed adjusted SMA.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().stream_endpoint(
            cur_base=cur_base,
            cur_adj=cur_adj,
            window=window,
            name=names[0]
        )

    @classmethod
    def stream_handler(
        cls,
        base_series:pd.Series,
        adj_series:pd.Series,
        window:int,
        prev_df:pd.DataFrame,
        cur_row:dict[str, int|float],
        name:Optional[str]=None,
    )->dict[str, float]:
        """
        Process the next stream step SMA adjustment using the previous DataFrame state.
        
        Args:
            base_series (pd.Series[float]): The base price series.
            adj_series (pd.Series[float]): The adjustment series.
            window (int): The rolling window size.
            name (str): The key name for the output dictionary. Defaults to "sma_adjust".
            prev_df (pd.DataFrame): The previous DataFrame state.
            cur_row (dict[str, int | float]): The current row values.
            
        Returns:
            dict[str, float]: A dictionary with the computed adjusted SMA.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().stream_handler(
            base_series=base_series,
            adj_series=adj_series,
            window=window,
            name=names[0],
            prev_df=prev_df,
            cur_row=cur_row
        )
    
# ---- from .ema ----
class EMACalc(_EMACalc):
    """
    Calculates the Exponential Moving Average (EMA).
    """

    name = "ema_calc"
    @classmethod
    def vector_endpoint(
        cls, 
        base_series:pd.Series, 
        window:int, 
        smoothing:Optional[float]=None,
        name:Optional[str]=None
    )->pd.DataFrame:
        """
        Execute historical vectorized matrix calculations for EMA.
        
        Args:
            base_series (pd.Series[float]): The input series to calculate EMA for.
            window (int): The window size for the calculation.
            smoothing (float): The smoothing factor (alpha = smoothing / (1 + window)). Defaults to 2.
            name (str): The column name for the output DataFrame. Defaults to "ema_calc".
            
        Returns:
            pd.Series: A Series containing the calculated EMA.
        """
        smoothing = smoothing or 2
        name = name or cls.name
        names = cls.output_keys(name)
        return super().vector_endpoint(
            base_series=base_series,
            window=window,
            smoothing=smoothing,
            name=names[0]
        )
    
    @classmethod
    def stream_endpoint(
        cls, 
        prev_ema:float, 
        cur_base:float, 
        window:int, 
        smoothing:Optional[float]=None, 
        name:Optional[str]=None
    )->dict[str, float]:
        """
        Compute the next step EMA using a low-latency O(1) recursive equation.
        
        Args:
            prev_ema (float): The previous step's EMA value.
            cur_base (float): The current base price entering the calculation.
            window (int): The window size.
            smoothing (float): The smoothing factor (alpha = smoothing / (1 + window)). Defaults to 2.
            name (str): The key name for the output dictionary. Defaults to "ema_calc".
            
        Returns:
            dict[str, float]: A dictionary with the computed EMA.
        """
        smoothing = smoothing or 2
        name = name or cls.name
        names = cls.output_keys(name)
        return super().stream_endpoint(
            prev_ema=prev_ema,
            cur_base=cur_base,
            window=window,
            smoothing=smoothing,
            name=names[0]
        )

    @classmethod
    def stream_handler(
        cls,
        base_series:pd.Series,
        window:int,
        prev_df:pd.DataFrame,
        cur_row:dict[str, int|float],
        smoothing:Optional[float]=None,
        name:Optional[str]=None,
    )->dict[str, float]:
        """
        Process the next stream step EMA using the previous DataFrame state.
        
        Args:
            base_series (pd.Series[float]): The input series history.
            window (int): The window size for the calculation.
            smoothing (float): The smoothing factor. Defaults to 2.
            name (str): The key name for the output dictionary. Defaults to "ema_calc".
            prev_df (pd.DataFrame): The previous DataFrame state.
            cur_row (dict[str, int | float]): The current row values.
            
        Returns:
            dict[str, float]: A dictionary with the computed EMA.
        """
        smoothing = smoothing or 2
        name = name or cls.name
        names = cls.output_keys(name)
        return super().stream_handler(
            base_series=base_series,
            window=window,
            smoothing=smoothing,
            name=names[0],
            prev_df=prev_df,
            cur_row=cur_row
        )
    
class MACDCalc(_MACDCalc):
    """
    Calculates the Moving Average Convergence Divergence (MACD), including the MACD line, signal line, and histogram.
    """

    name = "macd_calc"
    output_key_parts= (
        ("", ""),
        ("", "_signal"),
        ("", "_hist")
    )
    @classmethod
    def vector_endpoint(
        cls, 
        fast_ema:pd.Series, 
        slow_ema:pd.Series, 
        signal:int,
        name:Optional[str]=None
    )->pd.DataFrame:
        """
        Execute historical vectorized matrix calculations for MACD.
        
        Args:
            fast_ema (pd.Series[float]): The fast EMA series.
            slow_ema (pd.Series[float]): The slow EMA series.
            signal (int): The window size for the signal line EMA.
            name (str): The base column name for the outputs. Defaults to "macd_calc".
            
        Returns:
            pd.DataFrame: A DataFrame containing the MACD line, signal line, and histogram.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().vector_endpoint(
            fast_ema=fast_ema,
            slow_ema=slow_ema,
            signal=signal,
            name=names[0],
            signal_name=names[1],
            hist_name=names[2]
        )

    @classmethod
    def stream_endpoint(
        cls, 
        cur_fast_ema:float, 
        cur_slow_ema:float,
        signal:int,
        prev_signal_line:float,
        name:Optional[str]=None
    )->dict[str, float]:
        """
        Compute the next step MACD components using low-latency O(1) calculations.
        
        Args:
            cur_fast_ema (float): The current fast EMA value.
            cur_slow_ema (float): The current slow EMA value.
            signal (int): The window size for the signal line EMA.
            prev_signal_line (float): The previous step's signal line value.
            name (str): The base key name for the output dictionary. Defaults to "macd_calc".
            
        Returns:
            dict[str, float]: A dictionary with the computed MACD line, signal line, and histogram.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().stream_endpoint(
            cur_fast_ema=cur_fast_ema,
            cur_slow_ema=cur_slow_ema,
            signal=signal,
            prev_signal_line=prev_signal_line,
            name=names[0],
            signal_name=names[1],
            hist_name=names[2]
        )

    @classmethod
    def stream_handler(
        cls,
        fast_ema:pd.Series,
        slow_ema:pd.Series,
        signal:int,
        prev_df:pd.DataFrame,
        cur_row:dict[str, int|float],
        name:Optional[str]=None,
    )->dict[str, float]:
        """
        Process the next stream step MACD components using the previous DataFrame state.
        
        Args:
            fast_ema (pd.Series[float]): The fast EMA series.
            slow_ema (pd.Series[float]): The slow EMA series.
            signal (int): The window size for the signal line EMA.
            name (str): The base key name for the output dictionary. Defaults to "macd_calc".
            signal_name (str): The key name for the signal line output. Defaults to "macd_calc_signal".
            hist_name (str): The key name for the histogram output. Defaults to "macd_calc_hist".
            prev_df (pd.DataFrame): The previous DataFrame state.
            cur_row (dict[str, int | float]): The current row values.
            
        Returns:
            dict[str, float]: A dictionary with the computed MACD line, signal line, and histogram.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().stream_handler(
            fast_ema=fast_ema,
            slow_ema=slow_ema,
            signal=signal,
            name=names[0],
            signal_name=names[1],
            hist_name=names[2],
            prev_df=prev_df,
            cur_row=cur_row
        )

# ---- from .relation ----
class CrossType(_CrossType):
    """
    Evaluates crossover types between two series based on boundaries and standards.
    Returns 1 for a golden cross, -1 for a death cross, 2 for both, and 0 for no cross.
    """

    name = "cross_type"
    @classmethod
    def vector_endpoint(
        cls, 
        s1:pd.Series, 
        s2:pd.Series, 
        prev_s1:pd.Series, 
        prev_s2:pd.Series,
        upper_bound:Optional[pd.Series]=None,
        lower_bound:Optional[pd.Series]=None, 
        upper_standard:Optional[pd.Series]=None, 
        lower_standard:Optional[pd.Series]=None,
        name:Optional[str]=None
    )->pd.DataFrame:
        """
        Execute historical vectorized calculations for determining cross types.
        
        Args:
            s1 (pd.Series[float]): The first series.
            s2 (pd.Series[float]): The second series.
            prev_s1 (pd.Series[float]): The previous step's first series.
            prev_s2 (pd.Series[float]): The previous step's second series.
            upper_bound (Optional[pd.Series[float]]): The upper drift boundary within a step. Defaults to s1 if None.
            lower_bound (Optional[pd.Series[float]]): The lower drift boundary within a step. Defaults to s2 if None.
            upper_standard (Optional[pd.Series[float]]): The upper standard required to cross. Defaults to s2 if None.
            lower_standard (Optional[pd.Series[float]]): The lower standard required to cross. Defaults to s1 if None.
            name (str): The column name for the output DataFrame. Defaults to "cross_type".
            
        Returns:
            pd.DataFrame: A DataFrame containing the integer cross type identifiers.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().vector_endpoint(
            s1=s1,
            s2=s2,
            prev_s1=prev_s1,
            prev_s2=prev_s2,
            upper_bound=upper_bound,
            lower_bound=lower_bound,
            upper_standard=upper_standard,
            lower_standard=lower_standard,
            name=names[0]
        )
    
    @classmethod
    def stream_endpoint(
        cls,
        cur_s1:float,
        cur_s2:float,
        prev_s1:float,
        prev_s2:float,
        cur_upper_bound:Optional[float]=None,
        cur_upper_standard:Optional[float]=None,
        cur_lower_bound:Optional[float]=None,
        cur_lower_standard:Optional[float]=None,
        name:Optional[str]=None
    )->dict[str, int]:
        """
        Compute the next step cross type using O(1) boolean logic.
        
        Args:
            cur_s1 (float): The current first series value.
            cur_s2 (float): The current second series value.
            prev_s1 (float): The previous first series value.
            prev_s2 (float): The previous second series value.
            cur_upper_bound (Optional[float]): The current upper boundary. Defaults to cur_s1 if None.
            cur_upper_standard (Optional[float]): The current upper standard. Defaults to cur_s2 if None.
            cur_lower_bound (Optional[float]): The current lower boundary. Defaults to cur_s2 if None.
            cur_lower_standard (Optional[float]): The current lower standard. Defaults to cur_s1 if None.
            name (str): The key name for the output dictionary. Defaults to "cross_type".
            
        Returns:
            dict[str, int]: A dictionary with the computed cross type (1, -1, 2, or 0).
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().stream_endpoint(
            cur_s1=cur_s1,
            cur_s2=cur_s2,
            prev_s1=prev_s1,
            prev_s2=prev_s2,
            cur_upper_bound=cur_upper_bound,
            cur_upper_standard=cur_upper_standard,
            cur_lower_bound=cur_lower_bound,
            cur_lower_standard=cur_lower_standard,
            name=names[0]
        )

    @classmethod
    def stream_handler(
        cls,
        s1:pd.Series,
        s2:pd.Series,
        prev_s1:pd.Series,
        prev_s2:pd.Series,
        prev_df:pd.DataFrame=None,
        cur_row:dict[str, int|float]=None,
        upper_bound:Optional[pd.Series]=None,
        lower_bound:Optional[pd.Series]=None,
        upper_standard:Optional[pd.Series]=None,
        lower_standard:Optional[pd.Series]=None,
        name:Optional[str]=None,
    )->dict[str, int]:
        """
        Process the next stream step cross type using the previous DataFrame state.
        
        Args:
            s1 (pd.Series[float]): The first series.
            s2 (pd.Series[float]): The second series.
            prev_s1 (pd.Series[float]): The previous step's first series.
            prev_s2 (pd.Series[float]): The previous step's second series.
            upper_bound (Optional[pd.Series[float]]): The upper drift boundary. Defaults to s1 if None.
            lower_bound (Optional[pd.Series[float]]): The lower drift boundary. Defaults to s2 if None.
            upper_standard (Optional[pd.Series[float]]): The upper cross standard. Defaults to s2 if None.
            lower_standard (Optional[pd.Series[float]]): The lower cross standard. Defaults to s1 if None.
            name (str): The key name for the output dictionary. Defaults to "cross_type".
            prev_df (pd.DataFrame): The previous DataFrame state.
            cur_row (dict[str, int | float]): The current row values.
            
        Returns:
            dict[str, int]: A dictionary with the computed cross type.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().stream_handler(
            s1=s1,
            s2=s2,
            prev_s1=prev_s1,
            prev_s2=prev_s2,
            upper_bound=upper_bound,
            lower_bound=lower_bound,
            upper_standard=upper_standard,
            lower_standard=lower_standard,
            name=names[0],
            prev_df=prev_df,
            cur_row=cur_row
        )

class CrossVal(_CrossVal):
    """
    Evaluates the price or standard at which a crossover occurred.
    """

    name = "cross_val"
    @classmethod
    def vector_endpoint(
        cls, 
        s1:pd.Series, 
        s2:pd.Series,
        base_series:pd.Series,
        cross_type:pd.Series,
        upper_bound:Optional[pd.Series]=None,
        lower_bound:Optional[pd.Series]=None, 
        upper_standard:Optional[pd.Series]=None, 
        lower_standard:Optional[pd.Series]=None, 
        name:Optional[str]=None
    )->pd.DataFrame:
        """
        Execute historical vectorized calculations for cross values.
        
        Args:
            s1 (pd.Series[float]): The first series.
            s2 (pd.Series[float]): The second series.
            base_series (pd.Series[float]): The base price series.
            cross_type (pd.Series[int]): The series of cross types (1 for golden, -1 for death).
            upper_bound (Optional[pd.Series[float]]): The upper drift boundary. Defaults to s1 if None.
            lower_bound (Optional[pd.Series[float]]): The lower drift boundary. Defaults to s2 if None.
            upper_standard (Optional[pd.Series[float]]): The upper cross standard. Defaults to s2 if None.
            lower_standard (Optional[pd.Series[float]]): The lower cross standard. Defaults to s1 if None.
            name (str): The column name for the output DataFrame. Defaults to "cross_val".
            
        Returns:
            pd.DataFrame: A DataFrame containing the cross values.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().vector_endpoint(
            s1=s1,
            s2=s2,
            base_series=base_series,
            cross_type=cross_type,
            upper_bound=upper_bound,
            lower_bound=lower_bound,
            upper_standard=upper_standard,
            lower_standard=lower_standard,
            name=names[0]
        )
    
    @classmethod
    def stream_endpoint(
        cls, 
        cur_s1:float, 
        cur_s2:float,
        cur_base:float,
        cur_cross_type:int,
        cur_upper_bound:Optional[float]=None,
        cur_lower_bound:Optional[float]=None, 
        cur_upper_standard:Optional[float]=None, 
        cur_lower_standard:Optional[float]=None, 
        name:Optional[str]=None
    )->dict[str, float]:
        """
        Compute the next step cross value using O(1) selection logic.
        
        Args:
            cur_s1 (float): The current first series value.
            cur_s2 (float): The current second series value.
            cur_base (float): The current base price.
            cur_cross_type (int): The current cross type (1 for golden, -1 for death).
            cur_upper_bound (Optional[float]): The current upper boundary. Defaults to cur_s1 if None.
            cur_lower_bound (Optional[float]): The current lower boundary. Defaults to cur_s2 if None.
            cur_upper_standard (Optional[float]): The current upper standard. Defaults to cur_s2 if None.
            cur_lower_standard (Optional[float]): The current lower standard. Defaults to cur_s1 if None.
            name (str): The key name for the output dictionary. Defaults to "cross_val".
            
        Returns:
            dict[str, float]: A dictionary with the computed cross value.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().stream_endpoint(
            cur_s1=cur_s1,
            cur_s2=cur_s2,
            cur_base=cur_base,
            cur_cross_type=cur_cross_type,
            cur_upper_bound=cur_upper_bound,
            cur_lower_bound=cur_lower_bound,
            cur_upper_standard=cur_upper_standard,
            cur_lower_standard=cur_lower_standard,
            name=names[0]
        )

    @classmethod
    def stream_handler(
        cls,
        s1:pd.Series,
        s2:pd.Series,
        base_series:pd.Series,
        cross_type:pd.Series,
        upper_bound:Optional[pd.Series]=None,
        lower_bound:Optional[pd.Series]=None,
        upper_standard:Optional[pd.Series]=None,
        lower_standard:Optional[pd.Series]=None,
        name:Optional[str]=None,
        prev_df:pd.DataFrame=None,
        cur_row:dict[str, int|float]=None
    )->dict[str, float]:
        """
        Process the next stream step cross value using the previous DataFrame state.
        
        Args:
            s1 (pd.Series[float]): The first series.
            s2 (pd.Series[float]): The second series.
            base_series (pd.Series[float]): The base price series.
            cross_type (pd.Series[int]): The series of cross types.
            upper_bound (Optional[pd.Series[float]]): The upper drift boundary. Defaults to s1 if None.
            lower_bound (Optional[pd.Series[float]]): The lower drift boundary. Defaults to s2 if None.
            upper_standard (Optional[pd.Series[float]]): The upper cross standard. Defaults to s2 if None.
            lower_standard (Optional[pd.Series[float]]): The lower cross standard. Defaults to s1 if None.
            name (str): The key name for the output dictionary. Defaults to "cross_val".
            prev_df (pd.DataFrame): The previous DataFrame state.
            cur_row (dict[str, int | float]): The current row values.
            
        Returns:
            dict[str, float]: A dictionary with the computed cross value.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().stream_handler(
            s1=s1,
            s2=s2,
            base_series=base_series,
            cross_type=cross_type,
            upper_bound=upper_bound,
            lower_bound=lower_bound,
            upper_standard=upper_standard,
            lower_standard=lower_standard,
            name=names[0],
            prev_df=prev_df,
            cur_row=cur_row
        )

class TrendType(_TrendType):
    """
    Determines the trend direction based on upper and lower bounds compared to a threshold.
    Returns 1 for long trend, -1 for short trend, and 0 for flat trend.
    """

    name = "trend_type"
    @classmethod
    def vector_endpoint(
        cls, 
        prev_base_series:pd.Series,
        upper_bound:pd.Series,
        lower_bound:pd.Series, 
        thresh:float, 
        trend_len:int,
        name:Optional[str]=None
    )->pd.DataFrame:
        """
        Execute historical vectorized calculations for determining trend types.
        
        Args:
            upper_bound (pd.Series[float]): The upper boundary series.
            lower_bound (pd.Series[float]): The lower boundary series.
            thresh (float): The flatness threshold percentage.
            trend_len (int): The length of the window to confirm the trend.
            prev_base_series (pd.Series[float]): The previous step's base series.
            name (str): The column name for the output DataFrame. Defaults to "trend_type".
            
        Returns:
            pd.DataFrame: A DataFrame containing the integer trend type identifiers.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().vector_endpoint(
            upper_bound=upper_bound,
            lower_bound=lower_bound,
            thresh=thresh,
            trend_len=trend_len,
            prev_base_series=prev_base_series,
            name=names[0]
        )
    
    @classmethod
    def stream_endpoint(
        cls, 
        upper_bound:pd.Series,
        lower_bound:pd.Series,
        thresh:float,
        trend_len:int,
        prev_base_series:pd.Series, 
        name:Optional[str]=None
    )->dict[str, int]:
        """
        Compute the next step trend type. Currently uses a tail calculation approach.
        
        Args:
            upper_bound (pd.Series[float]): The recent upper boundary series history.
            lower_bound (pd.Series[float]): The recent lower boundary series history.
            thresh (float): The flatness threshold percentage.
            trend_len (int): The length of the window to confirm the trend.
            prev_base_series (pd.Series[float]): The recent previous base series history.
            name (str): The key name for the output dictionary. Defaults to "trend_type".
            
        Returns:
            dict[str, int]: A dictionary with the computed trend type.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().stream_endpoint(
            upper_bound=upper_bound,
            lower_bound=lower_bound,
            thresh=thresh,
            trend_len=trend_len,
            prev_base_series=prev_base_series,
            name=names[0]
        )

    @classmethod
    def stream_handler(
        cls,
        prev_base_series:pd.Series,
        upper_bound:pd.Series,
        lower_bound:pd.Series,
        thresh:float,
        trend_len:int,
        prev_df:pd.DataFrame,
        cur_row:dict[str, int|float],
        name:Optional[str]=None,
    )->dict[str, int]:
        """
        Process the next stream step trend type using the previous DataFrame state.
        
        Args:
            prev_base_series (pd.Series[float]): The previous base series history.
            upper_bound (pd.Series[float]): The upper boundary series.
            lower_bound (pd.Series[float]): The lower boundary series.
            thresh (float): The flatness threshold percentage.
            trend_len (int): The length of the window to confirm the trend.
            name (str): The key name for the output dictionary. Defaults to "trend_type".
            prev_df (pd.DataFrame): The previous DataFrame state.
            cur_row (dict[str, int | float]): The current row values.
            
        Returns:
            dict[str, int]: A dictionary with the computed trend type.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().stream_handler(
            prev_base_series=prev_base_series,
            upper_bound=upper_bound,
            lower_bound=lower_bound,
            thresh=thresh,
            trend_len=trend_len,
            name=names[0],
            prev_df=prev_df,
            cur_row=cur_row
        )

    @classmethod
    def tail(
        cls,
        prev_base_series:pd.Series,
        upper_bound:pd.Series,
        lower_bound:pd.Series,
        thresh:float,
        trend_len:int,
        name:Optional[str]=None
    )->dict[str, int]:
        """
        Calculate the trend type for the tail of a series.
        
        Args:
            prev_base_series (pd.Series[float]): The recent previous base series history.
            upper_bound (pd.Series[float]): The recent upper boundary series history.
            lower_bound (pd.Series[float]): The recent lower boundary series history.
            thresh (float): The flatness threshold percentage.
            trend_len (int): The length of the window to confirm the trend.
            name (str): The key name for the output dictionary. Defaults to "trend_type".
            
        Returns:
            dict[str, int]: A dictionary with the computed tail trend type.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().tail(
            prev_base_series=prev_base_series,
            upper_bound=upper_bound,
            lower_bound=lower_bound,
            thresh=thresh,
            trend_len=trend_len,
            name=names[0]
        )

class TrendVal(_TrendVal):
    """
    Evaluates the value associated with a specific trend direction.
    """

    name = "trend_val"
    @classmethod
    def vector_endpoint(
        cls, 
        upper_bound:pd.Series,
        lower_bound:pd.Series,
        upper_standard:pd.Series,
        lower_standard:pd.Series,
        trend_type:pd.Series,
        base_series:pd.Series,
        name:Optional[str]=None
    )->pd.DataFrame:
        """
        Execute historical vectorized calculations for trend values.
        
        Args:
            upper_bound (pd.Series[float]): The upper boundary series.
            lower_bound (pd.Series[float]): The lower boundary series.
            upper_standard (pd.Series[float]): The upper standard series.
            lower_standard (pd.Series[float]): The lower standard series.
            trend_type (pd.Series[int]): The series of trend types (1 for long, -1 for short).
            base_series (pd.Series[float]): The base price series.
            name (str): The column name for the output DataFrame. Defaults to "trend_val".
            
        Returns:
            pd.DataFrame: A DataFrame containing the trend values.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().vector_endpoint(
            upper_bound=upper_bound,
            lower_bound=lower_bound,
            upper_standard=upper_standard,
            lower_standard=lower_standard,
            trend_type=trend_type,
            base_series=base_series,
            name=names[0]
        )

    @classmethod
    def stream_endpoint(
        cls, 
        cur_upper_bound:float,
        cur_lower_bound:float,
        cur_upper_standard:float,
        cur_lower_standard:float,
        cur_trend_type:int,
        cur_base:float,
        name:Optional[str]=None
    )->dict[str, float]:
        """
        Compute the next step trend value using O(1) selection logic.
        
        Args:
            cur_upper_bound (float): The current upper boundary.
            cur_lower_bound (float): The current lower boundary.
            cur_upper_standard (float): The current upper standard.
            cur_lower_standard (float): The current lower standard.
            cur_trend_type (int): The current trend type (1 for long, -1 for short).
            cur_base (float): The current base price.
            name (str): The key name for the output dictionary. Defaults to "trend_val".
            
        Returns:
            dict[str, float]: A dictionary with the computed trend value.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().stream_endpoint(
            cur_upper_bound=cur_upper_bound,
            cur_lower_bound=cur_lower_bound,
            cur_upper_standard=cur_upper_standard,
            cur_lower_standard=cur_lower_standard,
            cur_trend_type=cur_trend_type,
            cur_base=cur_base,
            name=names[0]
        )

    @classmethod
    def stream_handler(
        cls,
        base_series:pd.Series,
        upper_bound:pd.Series,
        lower_bound:pd.Series,
        upper_standard:pd.Series,
        lower_standard:pd.Series,
        trend_type:pd.Series,
        prev_df:pd.DataFrame,
        cur_row:dict[str, int|float],
        name:Optional[str]=None,
    )->dict[str, float]:
        """
        Process the next stream step trend value using the previous DataFrame state.
        
        Args:
            base_series (pd.Series[float]): The base price series.
            upper_bound (pd.Series[float]): The upper boundary series.
            lower_bound (pd.Series[float]): The lower boundary series.
            upper_standard (pd.Series[float]): The upper standard series.
            lower_standard (pd.Series[float]): The lower standard series.
            trend_type (pd.Series[int]): The trend type series.
            name (str): The key name for the output dictionary. Defaults to "trend_val".
            prev_df (pd.DataFrame): The previous DataFrame state.
            cur_row (dict[str, int | float]): The current row values.
            
        Returns:
            dict[str, float]: A dictionary with the computed trend value.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().stream_handler(
            base_series=base_series,
            upper_bound=upper_bound,
            lower_bound=lower_bound,
            upper_standard=upper_standard,
            lower_standard=lower_standard,
            trend_type=trend_type,
            name=names[0],
            prev_df=prev_df,
            cur_row=cur_row
        )

class WindowMax(_WindowMax):
    """
    Calculates the rolling maximum over a specified window.
    """

    name = "win_max"
    @classmethod
    def vector_endpoint(
        cls, 
        base_series:pd.Series, 
        window:int,
        name:Optional[str]=None
    )->pd.DataFrame:
        """
        Execute historical vectorized calculations for window maximum.
        
        Args:
            base_series (pd.Series[float]): The input series.
            window (int): The rolling window size.
            name (str): The column name for the output DataFrame. Defaults to "win_max".
            
        Returns:
            pd.DataFrame: A DataFrame containing the rolling maximum.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().vector_endpoint(
            base_series=base_series, 
            window=window, 
            name=names[0]
        )
    
    @classmethod
    def stream_endpoint(
        cls, 
        base_series:pd.Series, 
        window:int,
        name:Optional[str]=None
    )->dict[str, float]:
        """
        Compute the next step window maximum. Currently uses a tail calculation approach.
        
        Args:
            base_series (pd.Series[float]): The recent input series history.
            window (int): The rolling window size.
            name (str): The key name for the output dictionary. Defaults to "win_max".
            
        Returns:
            dict[str, float]: A dictionary with the computed rolling maximum.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().stream_endpoint(
            base_series=base_series,
            window=window,
            name=names[0]
        )

    @classmethod
    def tail(
        cls, 
        base_series:pd.Series, 
        window:int,
        name:Optional[str]=None
    )->dict[str, float]:
        """
        Calculate the rolling maximum for the tail of a series.
        
        Args:
            base_series (pd.Series[float]): The input series.
            window (int): The rolling window size.
            name (str): The key name for the output dictionary. Defaults to "win_max".
            
        Returns:
            dict[str, float]: A dictionary with the computed tail rolling maximum.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().tail(
            base_series=base_series,
            window=window,
            name=names[0]
        )

    @classmethod
    def stream_handler(
        cls,
        base_series:pd.Series,
        window:int,
        prev_df:pd.DataFrame,
        cur_row:dict[str, int|float],
        name:Optional[str]=None,
    )->dict[str, float]:
        """
        Process the next stream step window maximum using the previous DataFrame state.
        
        Args:
            base_series (pd.Series[float]): The input series history.
            window (int): The rolling window size.
            name (str): The key name for the output dictionary. Defaults to "win_max".
            prev_df (pd.DataFrame): The previous DataFrame state.
            cur_row (dict[str, int | float]): The current row values.
            
        Returns:
            dict[str, float]: A dictionary with the computed rolling maximum.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().stream_handler(
            base_series=base_series,
            window=window,
            name=names[0],
            prev_df=prev_df,
            cur_row=cur_row
        )
    
class WindowMin(_WindowMin):
    """
    Calculates the rolling minimum over a specified window.
    """

    name = "win_min"
    @classmethod
    def vector_endpoint(
        cls,
        base_series:pd.Series,
        window:int,
        name:Optional[str]=None
    )->pd.DataFrame:
        """
        Execute historical vectorized calculations for window minimum.
        
        Args:
            base_series (pd.Series[float]): The input series.
            window (int): The rolling window size.
            name (str): The column name for the output DataFrame. Defaults to "win_min".
            
        Returns:
            pd.DataFrame: A DataFrame containing the rolling minimum.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().vector_endpoint(
            base_series=base_series,
            window=window,
            name=names[0]
        )
    
    @classmethod
    def stream_endpoint(
        cls,
        base_series:pd.Series,
        window:int,
        name:Optional[str]=None
    )->dict[str, float]:
        """
        Compute the next step window minimum. Currently uses a tail calculation approach.
        
        Args:
            base_series (pd.Series[float]): The recent input series history.
            window (int): The rolling window size.
            name (str): The key name for the output dictionary. Defaults to "win_min".
            
        Returns:
            dict[str, float]: A dictionary with the computed rolling minimum.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().stream_endpoint(
            base_series=base_series,
            window=window,
            name=names[0]
        )

    @classmethod
    def tail(
        cls, 
        base_series:pd.Series, 
        window:int, 
        name:Optional[str]=None
    )->dict[str, float]:
        """
        Calculate the rolling minimum for the tail of a series.
        
        Args:
            base_series (pd.Series[float]): The input series.
            window (int): The rolling window size.
            name (str): The key name for the output dictionary. Defaults to "win_min".
            
        Returns:
            dict[str, float]: A dictionary with the computed tail rolling minimum.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().tail(
            base_series=base_series,
            window=window,
            name=names[0]
        )

    @classmethod
    def stream_handler(
        cls,
        base_series:pd.Series,
        window:int,
        prev_df:pd.DataFrame,
        cur_row:dict[str, int|float],
        name:Optional[str]=None,
    )->dict[str, float]:
        """
        Process the next stream step window minimum using the previous DataFrame state.
        
        Args:
            base_series (pd.Series[float]): The input series history.
            window (int): The rolling window size.
            name (str): The key name for the output dictionary. Defaults to "win_min".
            prev_df (pd.DataFrame): The previous DataFrame state.
            cur_row (dict[str, int | float]): The current row values.
            
        Returns:
            dict[str, float]: A dictionary with the computed rolling minimum.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().stream_handler(
            base_series=base_series,
            window=window,
            name=names[0],
            prev_df=prev_df,
            cur_row=cur_row
        )
    
class Shift(_Shift):
    """
    Shifts an input series forward by a specified period.
    """

    name="shift"
    @classmethod
    def vector_endpoint(
        cls, 
        base_series:pd.Series, 
        period:int,
        name:Optional[str]=None
    )->pd.DataFrame:
        """
        Execute historical vectorized calculations for shifting a series.
        
        Args:
            base_series (pd.Series[float]): The input series.
            period (int): The number of steps to shift.
            name (str): The column name for the output DataFrame. Defaults to "shift".
            
        Returns:
            pd.DataFrame: A DataFrame containing the shifted series.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().vector_endpoint(
            base_series=base_series,
            period=period,
            name=names[0]
        )
    
    @classmethod
    def stream_endpoint(
        cls, 
        base_series:pd.Series, 
        period:int,
        name:Optional[str]=None
    )->dict[str, float]:
        """
        Compute the next step shifted value. Uses historical data to lookup the shifted value.
        
        Args:
            base_series (pd.Series[float]): The recent input series history.
            period (int): The number of steps to shift backward.
            name (str): The key name for the output dictionary. Defaults to "shift".
            
        Returns:
            dict[str, float]: A dictionary with the shifted value.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().stream_endpoint(
            base_series=base_series,
            period=period,
            name=names[0]
        )

    @classmethod
    def stream_handler(
        cls,
        base_series:pd.Series,
        period:int,
        prev_df:pd.DataFrame,
        cur_row:dict[str, int|float],
        name:Optional[str]=None,
    )->dict[str, float]:
        """
        Process the next stream step shifted value using the previous DataFrame state.
        
        Args:
            base_series (pd.Series[float]): The input series history.
            period (int): The number of steps to shift backward.
            name (str): The key name for the output dictionary. Defaults to "shift".
            prev_df (pd.DataFrame): The previous DataFrame state.
            cur_row (dict[str, int | float]): The current row values.
            
        Returns:
            dict[str, float]: A dictionary with the shifted value.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().stream_handler(
            base_series=base_series,
            period=period,
            name=names[0],
            prev_df=prev_df,
            cur_row=cur_row
        )

    @classmethod
    def tail(
        cls, 
        base_series:pd.Series,
        period:int,
        name:Optional[str]=None
    )->dict[str, float]:
        """
        Calculate the shifted value for the tail of a series.
        
        Args:
            base_series (pd.Series[float]): The input series.
            period (int): The number of steps to shift backward.
            name (str): The key name for the output dictionary. Defaults to "shift".
            
        Returns:
            dict[str, float]: A dictionary with the computed tail shifted value.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().tail(
            base_series=base_series,
            period=period,
            name=names[0]
        )

class RelativePosition(_RelativePosition):
    """
    Evaluates the relative position between two series.
    Returns 1 if s1 > s2, -1 if s1 < s2, and 0 if equal.
    """

    name = "relative_pos"
    @classmethod
    def vector_endpoint(
        cls, 
        s1:pd.Series, 
        s2:pd.Series, 
        name:Optional[str]=None
    )->pd.DataFrame:
        """
        Execute historical vectorized calculations for determining relative positions.
        
        Args:
            s1 (pd.Series[float]): The first series.
            s2 (pd.Series[float]): The second series.
            name (str): The column name for the output DataFrame. Defaults to "relative_pos".
            
        Returns:
            pd.DataFrame: A DataFrame containing the integer relative position identifiers.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().vector_endpoint(
            s1=s1,
            s2=s2,
            name=names[0]
        )
    
    @classmethod
    def stream_endpoint(
        cls,
        cur_s1:float,
        cur_s2:float,
        name:Optional[str]=None
    )->dict[str, int]:
        """
        Compute the next step relative position using O(1) boolean logic.
        
        Args:
            cur_s1 (float): The current first series value.
            cur_s2 (float): The current second series value.
            name (str): The key name for the output dictionary. Defaults to "relative_pos".
            
        Returns:
            dict[str, int]: A dictionary with the computed relative position (1, -1, or 0).
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().stream_endpoint(
            cur_s1=cur_s1,
            cur_s2=cur_s2,
            name=names[0]
        )

    @classmethod
    def stream_handler(
        cls,
        s1:pd.Series,
        s2:pd.Series,
        prev_df:pd.DataFrame=None,
        cur_row:dict[str, int|float]=None,
        name:Optional[str]=None,
    )->dict[str, int]:
        """
        Process the next stream step relative position using the previous DataFrame state.
        
        Args:
            s1 (pd.Series[float]): The first series.
            s2 (pd.Series[float]): The second series.
            name (str): The key name for the output dictionary. Defaults to "relative_pos".
            prev_df (pd.DataFrame): The previous DataFrame state.
            cur_row (dict[str, int | float]): The current row values.
            
        Returns:
            dict[str, int]: A dictionary with the computed relative position.
        """
        name = name or cls.name
        names = cls.output_keys(name)
        return super().stream_handler(
            s1=s1,
            s2=s2,
            name=names[0],
            prev_df=prev_df,
            cur_row=cur_row
        )
        
__all__ = [
    "SMACalc",
    "SMA2SMACrossStandard",
    "SMATrendMaintVal",
    "SMAadjust",
    "EMACalc",
    "MACDCalc",
    "CrossType",
    "CrossVal",
    "TrendType",
    "TrendVal",
    "WindowMax",
    "WindowMin",
    "Shift",
    "RelativePosition"
]