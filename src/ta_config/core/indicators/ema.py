import pandas as pd
from .base_indicator import BaseIndicator

# Overveiw
# EMACalc: missing anchor, stream endpoint

class EMACalc(BaseIndicator):
    @staticmethod
    def vector_endpoint(base_series: pd.Series[float], window: int, smoothing: float = 2.0) -> pd.Series[float]:
        # Manually calculate alpha using the custom smoothing value
        alpha = smoothing / (1 + window)
        
        # Pass alpha directly to Pandas instead of using span
        return base_series.ewm(alpha=alpha, adjust=False).mean()

    @staticmethod
    def anchor_endpoint(prev_ema: float, cur_price: float, window: int, smoothing: float = 2.0) -> float:
        # Calculate alpha using your custom smoothing parameter
        alpha = smoothing / (1 + window)
        
        # Run the identical recursive equation
        return (cur_price * alpha) + (prev_ema * (1 - alpha))
    
    @staticmethod
    def stream_endpoint(prev_ema: float, cur_price: float, window: int, smoothing: float = 2.0) -> float:
        return EMACalc.anchor_endpoint(prev_ema, cur_price, window, smoothing)
    