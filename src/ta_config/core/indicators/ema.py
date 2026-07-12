import pandas as pd
from .base_indicator import BaseIndicator

class EMACalc(BaseIndicator):
    @classmethod
    def vector_endpoint(
            cls, 
            base_series:pd.Series,
            window:int,
            smoothing:float,
            name:str
        )->pd.DataFrame:
        # Manually calculate alpha using the custom smoothing value
        alpha = smoothing / (1 + window)
        
        # Pass alpha directly to Pandas instead of using span
        return base_series.ewm(alpha=alpha, adjust=False).mean().to_frame(name)
    
    @classmethod
    def stream_endpoint(
            cls, 
            prev_ema:float, 
            cur_base:float, 
            window:int, 
            smoothing:float, 
            name:str
        )->dict[str, float]:
        # Calculate alpha using your custom smoothing parameter
        alpha = smoothing / (1 + window)
        
        # Run the identical recursive equation
        return {name:(cur_base * alpha) + (prev_ema * (1 - alpha))}
    