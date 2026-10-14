import pandas as pd

from .base_indicator import BaseIndicator


class SMACalc(BaseIndicator):
    name = "sma_calc"

    @classmethod
    def vector_endpoint(
        cls, base_series: pd.Series, window: int, name: str = "sma_calc"
    ) -> pd.DataFrame:
        return base_series.rolling(window).mean().to_frame(name)

    @classmethod
    def stream_endpoint(
        cls, prev_sma: float, prev_base: float, cur_base: float, window: int, name: str = "sma_calc"
    ) -> dict[str, float]:
        """prev_base is the OUTGOING sample x[t-window], not x[t-1]."""
        return {name: prev_sma + (cur_base - prev_base) / window}

    @classmethod
    def tail(cls, base_series: pd.Series, window: int, name: str = "sma_calc") -> dict[str, float]:
        return {
            name: float(base_series.rolling(window).mean().iloc[-1])
            if len(base_series)
            else float("nan")
        }


class SMA2SMACrossStandard(BaseIndicator):
    name = "sma2sma_cross_standard"

    @classmethod
    def vector_endpoint(
        cls,
        base_series: pd.Series,
        sma1: pd.Series,
        sma2: pd.Series,
        window1: int,
        window2: int,
        name: str = "sma2sma_cross_standard",
    ) -> pd.DataFrame:
        if window1 == window2:
            return base_series.copy().to_frame(name)
        return (base_series + window1 * window2 * (sma2 - sma1) / (window2 - window1)).to_frame(
            name
        )

    @classmethod
    def stream_endpoint(
        cls,
        cur_base: float,
        cur_sma1: float,
        cur_sma2: float,
        window1: int,
        window2: int,
        name: str = "sma2sma_cross_standard",
    ) -> dict[str, float]:
        return {
            name: cur_base
            if window1 == window2
            else cur_base + window1 * window2 * (cur_sma2 - cur_sma1) / (window2 - window1)
        }


class SMATrendMaintVal(BaseIndicator):
    name = "sma_trend_maint_val"

    @classmethod
    def vector_endpoint(
        cls,
        base_series: pd.Series,
        sma: pd.Series,
        prev_sma: pd.Series,
        window: int,
        name: str = "sma_trend_maint_val",
    ) -> pd.DataFrame:
        return (base_series + window * (prev_sma - sma)).to_frame(name)

    @classmethod
    def stream_endpoint(
        cls,
        cur_base: float,
        cur_sma: float,
        prev_sma: float,
        window: int,
        name: str = "sma_trend_maint_val",
    ) -> dict[str, float]:
        return {name: cur_base + window * (prev_sma - cur_sma)}


class SMAadjust(BaseIndicator):
    name = "sma_adjust"

    @classmethod
    def vector_endpoint(
        cls, base_series: pd.Series, adj_series: pd.Series, window: int, name: str = "sma_adjust"
    ) -> pd.DataFrame:
        return (base_series + (adj_series - base_series) / window).to_frame(name)

    @classmethod
    def stream_endpoint(
        cls, cur_base: float, cur_adj: float, window: int, name: str = "sma_adjust"
    ) -> dict[str, float]:
        return {name: cur_base + (cur_adj - cur_base) / window}
