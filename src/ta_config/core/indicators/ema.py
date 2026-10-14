import math

import pandas as pd

from .base_indicator import BaseIndicator


class EMACalc(BaseIndicator):
    name = "ema_calc"

    @classmethod
    def vector_endpoint(
        cls,
        base_series: pd.Series,
        window: int,
        smoothing: float | None = None,
        name: str = "ema_calc",
    ) -> pd.DataFrame:
        alpha = (2 if smoothing is None else smoothing) / (1 + window)
        result = base_series.ewm(alpha=alpha, adjust=False, ignore_na=True).mean()
        return result.where(base_series.notna()).to_frame(name)

    @classmethod
    def stream_endpoint(
        cls,
        prev_ema: float,
        cur_base: float,
        window: int,
        smoothing: float | None = None,
        name: str = "ema_calc",
    ) -> dict[str, float]:
        alpha = (2 if smoothing is None else smoothing) / (1 + window)
        if not 0 < alpha <= 1:
            raise ValueError("EMA alpha must be in (0, 1]")
        return {
            name: cur_base if math.isnan(prev_ema) else cur_base * alpha + prev_ema * (1 - alpha)
        }
