"""Strict immutable configuration. Input references are explicit class metadata."""

from collections.abc import Mapping
from types import MappingProxyType
from typing import Annotated, ClassVar, Self

from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator

from . import indicators as ind
from .indicators.base_indicator import BaseIndicator

Identifier = Annotated[str, Field(min_length=1, pattern=r"^\S(?:.*\S)?$")]
Window = Annotated[int, Field(gt=0, le=100_000)]
Period = Annotated[int, Field(ge=0, le=100_000)]
Threshold = Annotated[float, Field(ge=0, allow_inf_nan=False)]


class BaseConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True, populate_by_name=True)
    indicator_class: ClassVar[type[BaseIndicator]] = BaseIndicator
    input_fields: ClassVar[tuple[str, ...]] = ()

    def column_mapping(self) -> dict[str, str]:
        return {
            key: getattr(self, key) for key in self.input_fields if getattr(self, key) is not None
        }

    def parameters(self) -> dict[str, int | float]:
        return self.model_dump(exclude=set(self.input_fields), exclude_none=True)


class SMACalcConfig(BaseConfig):
    indicator_class = ind.SMACalc
    input_fields = ("base_series",)
    base_series: Identifier = Field(alias="base")
    window: Window


class SMA2SMACrossStandardConfig(BaseConfig):
    indicator_class = ind.SMA2SMACrossStandard
    input_fields = ("base_series", "sma1", "sma2")
    base_series: Identifier = Field(alias="base")
    sma1: Identifier
    sma2: Identifier
    window1: Window
    window2: Window


class SMATrendMaintValConfig(BaseConfig):
    indicator_class = ind.SMATrendMaintVal
    input_fields = ("base_series", "sma", "prev_sma")
    base_series: Identifier = Field(alias="base")
    sma: Identifier
    prev_sma: Identifier
    window: Window


class SMAAdjustConfig(BaseConfig):
    indicator_class = ind.SMAadjust
    input_fields = ("base_series", "adj_series")
    base_series: Identifier = Field(alias="base")
    adj_series: Identifier = Field(alias="adj")
    window: Window


class EMACalcConfig(BaseConfig):
    indicator_class = ind.EMACalc
    input_fields = ("base_series",)
    base_series: Identifier = Field(alias="base")
    window: Window
    smoothing: Annotated[float, Field(gt=0, allow_inf_nan=False)] | None = None

    @model_validator(mode="after")
    def valid_alpha(self) -> Self:
        if (2 if self.smoothing is None else self.smoothing) > self.window + 1:
            raise ValueError("smoothing / (window + 1) must be in (0, 1]")
        return self


class MACDCalcConfig(BaseConfig):
    indicator_class = ind.MACDCalc
    input_fields = ("fast_ema", "slow_ema")
    fast_ema: Identifier
    slow_ema: Identifier
    signal: Window


class RSICalcConfig(BaseConfig):
    indicator_class = ind.RSICalc
    input_fields = ("base_series",)
    base_series: Identifier = Field(alias="base")
    window: Window


class CrossTypeConfig(BaseConfig):
    indicator_class = ind.CrossType
    input_fields = (
        "s1",
        "s2",
        "prev_s1",
        "prev_s2",
        "upper_bound",
        "lower_bound",
        "upper_standard",
        "lower_standard",
    )
    s1: Identifier
    s2: Identifier
    prev_s1: Identifier
    prev_s2: Identifier
    upper_bound: Identifier | None = None
    lower_bound: Identifier | None = None
    upper_standard: Identifier | None = None
    lower_standard: Identifier | None = None


class CrossValConfig(BaseConfig):
    indicator_class = ind.CrossVal
    input_fields = (
        "s1",
        "s2",
        "base_series",
        "cross_type",
        "upper_bound",
        "lower_bound",
        "upper_standard",
        "lower_standard",
    )
    s1: Identifier
    s2: Identifier
    base_series: Identifier = Field(alias="base")
    cross_type: Identifier
    upper_bound: Identifier | None = None
    lower_bound: Identifier | None = None
    upper_standard: Identifier | None = None
    lower_standard: Identifier | None = None


class TrendTypeConfig(BaseConfig):
    indicator_class = ind.TrendType
    input_fields = ("upper_bound", "lower_bound", "prev_base_series")
    upper_bound: Identifier
    lower_bound: Identifier
    prev_base_series: Identifier = Field(alias="prev_base")
    thresh: Threshold
    trend_len: Window


class TrendValConfig(BaseConfig):
    indicator_class = ind.TrendVal
    input_fields = (
        "upper_bound",
        "lower_bound",
        "upper_standard",
        "lower_standard",
        "trend_type",
        "base_series",
    )
    upper_bound: Identifier
    lower_bound: Identifier
    upper_standard: Identifier
    lower_standard: Identifier
    trend_type: Identifier
    base_series: Identifier = Field(alias="base")


class RelativePositionConfig(BaseConfig):
    indicator_class = ind.RelativePosition
    input_fields = ("s1", "s2")
    s1: Identifier
    s2: Identifier


class WindowMaxConfig(BaseConfig):
    indicator_class = ind.WindowMax
    input_fields = ("base_series",)
    base_series: Identifier = Field(alias="base")
    window: Window


class WindowMinConfig(BaseConfig):
    indicator_class = ind.WindowMin
    input_fields = ("base_series",)
    base_series: Identifier = Field(alias="base")
    window: Window


class ShiftConfig(BaseConfig):
    indicator_class = ind.Shift
    input_fields = ("base_series",)
    base_series: Identifier = Field(alias="base")
    period: Period


class IndexConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    sma_calc: Mapping[Identifier, SMACalcConfig] | None = None
    sma_trend: Mapping[Identifier, SMATrendMaintValConfig] | None = None
    sma_adjust: Mapping[Identifier, SMAAdjustConfig] | None = None
    ema_calc: Mapping[Identifier, EMACalcConfig] | None = None
    macd_calc: Mapping[Identifier, MACDCalcConfig] | None = None
    rsi_calc: Mapping[Identifier, RSICalcConfig] | None = None
    sma2sma_cross_standard: Mapping[Identifier, SMA2SMACrossStandardConfig] | None = None
    cross_type: Mapping[Identifier, CrossTypeConfig] | None = None
    cross_val: Mapping[Identifier, CrossValConfig] | None = None
    trend_type: Mapping[Identifier, TrendTypeConfig] | None = None
    trend_val: Mapping[Identifier, TrendValConfig] | None = None
    window_max: Mapping[Identifier, WindowMaxConfig] | None = None
    window_min: Mapping[Identifier, WindowMinConfig] | None = None
    shift: Mapping[Identifier, ShiftConfig] | None = None
    relative_pos: Mapping[Identifier, RelativePositionConfig] | None = None

    @model_validator(mode="after")
    def freeze_maps(self) -> Self:
        for key in type(self).model_fields:
            value = getattr(self, key)
            if value is not None:
                object.__setattr__(self, key, MappingProxyType(dict(value)))
        return self

    @field_serializer("*")
    def serialize_maps(self, value):
        return None if value is None else dict(value)
