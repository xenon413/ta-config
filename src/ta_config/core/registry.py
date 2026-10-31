"""The trusted registry owns implementation and state-construction metadata."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import cast

from . import schema as cfg
from .indicators.base_indicator import BaseIndicator
from .indicators.rsi import RSIAccumulator
from .state import (
    EMAState,
    IndicatorState,
    MACDState,
    RollingState,
    RSIState,
    ScalarState,
    ShiftState,
    TrendState,
)


@dataclass(frozen=True)
class IndicatorSpec:
    config_type: type[cfg.BaseConfig]
    state_factory: Callable[[str, cfg.BaseConfig], IndicatorState]

    @property
    def implementation(self) -> type[BaseIndicator]:
        return self.config_type.indicator_class

    @property
    def inputs(self) -> tuple[str, ...]:
        return self.config_type.input_fields


def scalar(name: str, config: cfg.BaseConfig) -> IndicatorState:
    return ScalarState(name, config.indicator_class, config.parameters())


def make_spec[C: cfg.BaseConfig](
    config_type: type[C], factory: Callable[[str, C], IndicatorState]
) -> IndicatorSpec:
    return IndicatorSpec(config_type, lambda name, config: factory(name, cast(C, config)))


REGISTRY: Mapping[str, IndicatorSpec] = MappingProxyType(
    {
        "sma_calc": make_spec(cfg.SMACalcConfig, lambda n, c: RollingState(n, c.window, "sma")),
        "rsi_calc": make_spec(
            cfg.RSICalcConfig, lambda n, c: RSIState(n, RSIAccumulator(c.window))
        ),
        "ema_calc": make_spec(
            cfg.EMACalcConfig,
            lambda n, c: EMAState(n, c.window, 2 if c.smoothing is None else c.smoothing),
        ),
        "macd_calc": make_spec(
            cfg.MACDCalcConfig, lambda n, c: MACDState(n, EMAState(f"{n}_signal", c.signal))
        ),
        "shift": make_spec(cfg.ShiftConfig, lambda n, c: ShiftState(n, c.period)),
        "trend_type": make_spec(
            cfg.TrendTypeConfig, lambda n, c: TrendState(n, c.trend_len, c.thresh)
        ),
        "window_max": make_spec(cfg.WindowMaxConfig, lambda n, c: RollingState(n, c.window, "max")),
        "window_min": make_spec(cfg.WindowMinConfig, lambda n, c: RollingState(n, c.window, "min")),
        "sma_trend": make_spec(cfg.SMATrendMaintValConfig, scalar),
        "sma_adjust": make_spec(cfg.SMAAdjustConfig, scalar),
        "sma2sma_cross_standard": make_spec(cfg.SMA2SMACrossStandardConfig, scalar),
        "cross_type": make_spec(cfg.CrossTypeConfig, scalar),
        "cross_val": make_spec(cfg.CrossValConfig, scalar),
        "trend_val": make_spec(cfg.TrendValConfig, scalar),
        "relative_pos": make_spec(cfg.RelativePositionConfig, scalar),
    }
)
