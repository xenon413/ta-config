import pandas as pd

from .base_indicator import BaseIndicator
from .ema import EMACalc


class MACDCalc(BaseIndicator):
    name = "macd_calc"
    output_key_parts = (("", ""), ("", "_signal"), ("", "_hist"))

    @classmethod
    def vector_endpoint(
        cls,
        fast_ema: pd.Series,
        slow_ema: pd.Series,
        signal: int,
        name: str = "macd_calc",
        signal_name: str | None = None,
        hist_name: str | None = None,
    ) -> pd.DataFrame:
        line = fast_ema - slow_ema
        sig = EMACalc.vector_endpoint(line, signal)["ema_calc"]
        return pd.DataFrame(
            {
                name: line,
                signal_name or f"{name}_signal": sig,
                hist_name or f"{name}_hist": line - sig,
            }
        )

    @classmethod
    def stream_endpoint(
        cls,
        cur_fast_ema: float,
        cur_slow_ema: float,
        signal: int,
        prev_signal_line: float,
        name: str = "macd_calc",
        signal_name: str | None = None,
        hist_name: str | None = None,
    ) -> dict[str, float]:
        line = cur_fast_ema - cur_slow_ema
        sig = EMACalc.stream_endpoint(prev_signal_line, line, signal)["ema_calc"]
        return {
            name: line,
            signal_name or f"{name}_signal": sig,
            hist_name or f"{name}_hist": line - sig,
        }
