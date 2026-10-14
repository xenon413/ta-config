import math

import numpy as np
import pandas as pd

from .base_indicator import BaseIndicator


def _masked(result: pd.Series, *inputs: pd.Series) -> pd.Series:
    valid = pd.Series(True, index=result.index)
    for value in inputs:
        valid &= value.notna()
    return result.where(valid)


class CrossType(BaseIndicator):
    name = "cross_type"

    @classmethod
    def vector_endpoint(
        cls,
        s1: pd.Series,
        s2: pd.Series,
        prev_s1: pd.Series,
        prev_s2: pd.Series,
        upper_bound: pd.Series | None = None,
        lower_bound: pd.Series | None = None,
        upper_standard: pd.Series | None = None,
        lower_standard: pd.Series | None = None,
        name: str = "cross_type",
    ) -> pd.DataFrame:
        ub = s1 if upper_bound is None else upper_bound
        lb = s2 if lower_bound is None else lower_bound
        us = s2 if upper_standard is None else upper_standard
        ls = s1 if lower_standard is None else lower_standard
        golden = (prev_s1 <= prev_s2) & (ub >= us)
        death = (prev_s1 >= prev_s2) & (lb <= ls)
        result = golden.astype(int) - death.astype(int)
        result[golden & death] = 2
        return _masked(result, s1, s2, prev_s1, prev_s2, ub, lb, us, ls).to_frame(name)

    @classmethod
    def stream_endpoint(
        cls,
        cur_s1: float,
        cur_s2: float,
        prev_s1: float,
        prev_s2: float,
        cur_upper_bound: float | None = None,
        cur_upper_standard: float | None = None,
        cur_lower_bound: float | None = None,
        cur_lower_standard: float | None = None,
        name: str = "cross_type",
    ) -> dict[str, float]:
        ub = cur_s1 if cur_upper_bound is None else cur_upper_bound
        lb = cur_s2 if cur_lower_bound is None else cur_lower_bound
        us = cur_s2 if cur_upper_standard is None else cur_upper_standard
        ls = cur_s1 if cur_lower_standard is None else cur_lower_standard
        if any(math.isnan(v) for v in (cur_s1, cur_s2, prev_s1, prev_s2, ub, lb, us, ls)):
            return {name: math.nan}
        golden = prev_s1 <= prev_s2 and ub >= us
        death = prev_s1 >= prev_s2 and lb <= ls
        return {name: 2 if golden and death else int(golden) - int(death)}


class CrossVal(BaseIndicator):
    name = "cross_val"

    @classmethod
    def vector_endpoint(
        cls,
        s1: pd.Series,
        s2: pd.Series,
        base_series: pd.Series,
        cross_type: pd.Series,
        upper_bound: pd.Series | None = None,
        lower_bound: pd.Series | None = None,
        upper_standard: pd.Series | None = None,
        lower_standard: pd.Series | None = None,
        name: str = "cross_val",
    ) -> pd.DataFrame:
        ub = s1 if upper_bound is None else upper_bound
        lb = s2 if lower_bound is None else lower_bound
        us = s2 if upper_standard is None else upper_standard
        ls = s1 if lower_standard is None else lower_standard
        golden = np.where(lb > us, base_series, us)
        death = np.where(ub < ls, base_series, ls)
        result = pd.Series(
            np.select(
                [cross_type == 1, cross_type == -1, cross_type == 2],
                [golden, death, np.nan],
                default=0,
            ),
            index=base_series.index,
        )
        return _masked(result, s1, s2, base_series, cross_type, ub, lb, us, ls).to_frame(name)

    @classmethod
    def stream_endpoint(
        cls,
        cur_s1: float,
        cur_s2: float,
        cur_base: float,
        cur_cross_type: float,
        cur_upper_bound: float | None = None,
        cur_lower_bound: float | None = None,
        cur_upper_standard: float | None = None,
        cur_lower_standard: float | None = None,
        name: str = "cross_val",
    ) -> dict[str, float]:
        ub = cur_s1 if cur_upper_bound is None else cur_upper_bound
        lb = cur_s2 if cur_lower_bound is None else cur_lower_bound
        us = cur_s2 if cur_upper_standard is None else cur_upper_standard
        ls = cur_s1 if cur_lower_standard is None else cur_lower_standard
        if cur_cross_type == 2 or any(
            math.isnan(v) for v in (cur_s1, cur_s2, cur_base, cur_cross_type, ub, lb, us, ls)
        ):
            return {name: math.nan}
        if cur_cross_type == 1:
            return {name: cur_base if lb > us else us}
        if cur_cross_type == -1:
            return {name: cur_base if ub < ls else ls}
        return {name: 0.0}


def trend_direction(upper: float, lower: float, base: float, thresh: float) -> float:
    if any(math.isnan(v) for v in (upper, lower, base)) or base == 0:
        return math.nan
    direction = 1 if upper >= base else 0
    if lower < base:
        direction = -1
    if abs(upper - base) / abs(base) < thresh or abs(lower - base) / abs(base) < thresh:
        direction = 0
    return float(direction)


class TrendType(BaseIndicator):
    name = "trend_type"

    @classmethod
    def vector_endpoint(
        cls,
        upper_bound: pd.Series,
        lower_bound: pd.Series,
        prev_base_series: pd.Series,
        thresh: float,
        trend_len: int,
        name: str = "trend_type",
    ) -> pd.DataFrame:
        trend = pd.Series(0.0, index=prev_base_series.index)
        trend[upper_bound >= prev_base_series] = 1
        trend[lower_bound < prev_base_series] = -1
        denominator = prev_base_series.abs().replace(0, np.nan)
        flat = ((upper_bound - prev_base_series).abs() / denominator < thresh) | (
            (lower_bound - prev_base_series).abs() / denominator < thresh
        )
        trend[flat] = 0
        trend = _masked(trend, upper_bound, lower_bound, denominator)
        total = trend.rolling(trend_len).sum()
        result = pd.Series(
            np.select([total == trend_len, total == -trend_len], [1.0, -1.0], default=0.0),
            index=trend.index,
        )
        return result.where(total.notna()).to_frame(name)

    @classmethod
    def tail(
        cls,
        prev_base_series: pd.Series,
        upper_bound: pd.Series,
        lower_bound: pd.Series,
        thresh: float,
        trend_len: int,
        name: str = "trend_type",
    ) -> dict[str, float]:
        result = cls.vector_endpoint(
            upper_bound, lower_bound, prev_base_series, thresh, trend_len, name
        )
        return {name: float(result[name].iloc[-1]) if len(result) else math.nan}

    stream_endpoint = tail


class TrendVal(BaseIndicator):
    name = "trend_val"

    @classmethod
    def vector_endpoint(
        cls,
        base_series: pd.Series,
        upper_bound: pd.Series,
        lower_bound: pd.Series,
        upper_standard: pd.Series,
        lower_standard: pd.Series,
        trend_type: pd.Series,
        name: str = "trend_val",
    ) -> pd.DataFrame:
        upper = np.where(lower_bound > upper_standard, base_series, upper_standard)
        upper = np.where(upper_bound < upper_standard, 0, upper)
        lower = np.where(upper_bound < lower_standard, base_series, lower_standard)
        lower = np.where(lower_bound > lower_standard, 0, lower)
        result = pd.Series(
            np.select([trend_type == 1, trend_type == -1], [upper, lower], default=0),
            index=base_series.index,
        )
        return _masked(
            result,
            base_series,
            upper_bound,
            lower_bound,
            upper_standard,
            lower_standard,
            trend_type,
        ).to_frame(name)

    @classmethod
    def stream_endpoint(
        cls,
        cur_upper_bound: float,
        cur_lower_bound: float,
        cur_upper_standard: float,
        cur_lower_standard: float,
        cur_trend_type: float,
        cur_base: float,
        name: str = "trend_val",
    ) -> dict[str, float]:
        if any(
            math.isnan(v)
            for v in (
                cur_upper_bound,
                cur_lower_bound,
                cur_upper_standard,
                cur_lower_standard,
                cur_trend_type,
                cur_base,
            )
        ):
            return {name: math.nan}
        if cur_trend_type == 1:
            value = cur_base if cur_lower_bound > cur_upper_standard else cur_upper_standard
            return {name: 0.0 if cur_upper_bound < cur_upper_standard else value}
        if cur_trend_type == -1:
            value = cur_base if cur_upper_bound < cur_lower_standard else cur_lower_standard
            return {name: 0.0 if cur_lower_bound > cur_lower_standard else value}
        return {name: 0.0}


class WindowMax(BaseIndicator):
    name = "win_max"

    @classmethod
    def vector_endpoint(
        cls, base_series: pd.Series, window: int, name: str = "win_max"
    ) -> pd.DataFrame:
        return base_series.rolling(window).max().to_frame(name)

    @classmethod
    def tail(cls, base_series: pd.Series, window: int, name: str = "win_max") -> dict[str, float]:
        return {
            name: float(base_series.rolling(window).max().iloc[-1])
            if len(base_series)
            else math.nan
        }

    stream_endpoint = tail


class WindowMin(BaseIndicator):
    name = "win_min"

    @classmethod
    def vector_endpoint(
        cls, base_series: pd.Series, window: int, name: str = "win_min"
    ) -> pd.DataFrame:
        return base_series.rolling(window).min().to_frame(name)

    @classmethod
    def tail(cls, base_series: pd.Series, window: int, name: str = "win_min") -> dict[str, float]:
        return {
            name: float(base_series.rolling(window).min().iloc[-1])
            if len(base_series)
            else math.nan
        }

    stream_endpoint = tail


class Shift(BaseIndicator):
    name = "shift"

    @classmethod
    def vector_endpoint(
        cls, base_series: pd.Series, period: int, name: str = "shift"
    ) -> pd.DataFrame:
        return base_series.shift(period).to_frame(name)

    @classmethod
    def tail(cls, base_series: pd.Series, period: int, name: str = "shift") -> dict[str, float]:
        return {
            name: float(base_series.iloc[-period - 1]) if len(base_series) > period else math.nan
        }

    stream_endpoint = tail


class RelativePosition(BaseIndicator):
    name = "relative_pos"

    @classmethod
    def vector_endpoint(
        cls, s1: pd.Series, s2: pd.Series, name: str = "relative_pos"
    ) -> pd.DataFrame:
        result = (s1 > s2).astype("int8") - (s1 < s2).astype("int8")
        return _masked(result, s1, s2).to_frame(name)

    @classmethod
    def stream_endpoint(
        cls, cur_s1: float, cur_s2: float, name: str = "relative_pos"
    ) -> dict[str, float]:
        if math.isnan(cur_s1) or math.isnan(cur_s2):
            return {name: math.nan}
        return {name: int(cur_s1 > cur_s2) - int(cur_s1 < cur_s2)}
