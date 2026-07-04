import pandas as pd

from .base_indicator import BaseIndicator
from .ema import EMACalc

class MACDCalc(BaseIndicator):
    @classmethod
    def vector_endpoint(
            cls, 
            fast_ema:pd.Series, 
            slow_ema:pd.Series, 
            signal:int, 
            name:str,
            signal_name:str,
            hist_name:str
        )->pd.DataFrame:
        macd_line = fast_ema - slow_ema
        signal_line = EMACalc.vector_endpoint(base_series=macd_line, window=signal, smoothing=2, name="ema")["ema"]
        macd_hist = macd_line - signal_line
        return pd.DataFrame({name:macd_line, signal_name:signal_line, hist_name:macd_hist})

    @classmethod
    def stream_endpoint(
            cls,
            cur_fast_ema:float, 
            cur_slow_ema:float, 
            signal:int,
            prev_signal_line:float,
            name:str,
            signal_name:str,
            hist_name:str
        )->dict[str, float]:
        cur_macd = cur_fast_ema - cur_slow_ema
        cur_signal = EMACalc.stream_endpoint(prev_signal_line, cur_macd, signal, 2, "ema")["ema"]
        cur_hist = cur_macd - cur_signal
        return {name:cur_macd, signal_name:cur_signal, hist_name:cur_hist}
    
