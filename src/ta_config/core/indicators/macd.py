import pandas as pd

from .base_indicator import BaseIndicator
from .ema import EMACalc

# Overveiw
# MACDCalc: missing anchor, stream endpoint

class MACDCalc(BaseIndicator):
    @staticmethod
    def vector_endpoint(base_series:pd.Series[float], fast:int, slow:int, signal:int)->tuple[pd.Series[float], ...]:
        ema_fast = EMACalc.vector_endpoint(base_series, fast).mean()
        ema_slow = EMACalc.vector_endpoint(base_series, slow).mean()

        macd_line = ema_fast - ema_slow
        
        signal_line = EMACalc.vector_endpoint(macd_line, signal).mean()
        
        macd_hist = macd_line - signal_line
        
        return signal_line, macd_line, macd_hist

    @staticmethod
    def anchor_endpoint():...

    @staticmethod
    def stream_endpoint():...

