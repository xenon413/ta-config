import pandas as pd

from .base_indicator import BaseIndicator
from .ema import EMACalc

class MACDCalc(BaseIndicator):
    @classmethod
    def vector_endpoint(cls, fast_ema:pd.Series[float], slow_ema:pd.Series[float], signal:int, name:str)->pd.DataFrame:
        macd_line = fast_ema - slow_ema
        signal_line = EMACalc.vector_endpoint(macd_line, signal, 2, "ema")["ema"]
        macd_hist = macd_line - signal_line
        return pd.DataFrame({name:macd_line, f"{name}_signal":signal_line, f"{name}_hist":macd_hist})

    @classmethod
    def stream_endpoint(
            cls,
            cur_fast_ema:float, 
            cur_slow_ema:float, 
            signal:int,
            prev_signal_line:float,
            name:str
        )->dict[str, float]:
        cur_macd = cur_fast_ema - cur_slow_ema
        cur_signal = EMACalc.stream_endpoint(prev_signal_line, cur_macd, signal, 2)[0]
        cur_hist = cur_macd - cur_signal
        return {name:cur_macd, f"{name}_signal":cur_signal,f"{name}_hist":cur_hist}
    
