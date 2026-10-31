"""Bounded per-indicator state. No pandas objects are retained by the engine."""

import math
from collections import deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Protocol, cast

from . import indicators as ind
from .indicators.base_indicator import BaseIndicator
from .indicators.relation import trend_direction
from .indicators.rsi import RSIAccumulator

NAN = float("nan")


class IndicatorState(Protocol):
    def feed(self, inputs: Mapping[str, float]) -> dict[str, float]: ...


@dataclass
class RollingState:
    name: str
    window: int
    kind: str
    values: deque[float] = field(default_factory=deque)
    extrema: deque[tuple[int, float]] = field(default_factory=deque)
    count: int = 0
    valid: int = 0
    total: float = 0.0

    def feed(self, inputs: Mapping[str, float]) -> dict[str, float]:
        value = inputs["base_series"]
        self.count += 1
        if len(self.values) == self.window:
            old = self.values.popleft()
            if not math.isnan(old):
                self.valid -= 1
                self.total -= old
        self.values.append(value)
        if not math.isnan(value):
            self.valid += 1
            self.total += value
        if self.kind == "sma":
            # Periodic fsum rebasing bounds long-run cancellation drift.
            if self.count % self.window == 0:
                self.total = math.fsum(v for v in self.values if not math.isnan(v))
            result = self.total / self.window
        else:
            while self.extrema and self.extrema[0][0] <= self.count - self.window:
                self.extrema.popleft()
            if not math.isnan(value):
                while self.extrema and (
                    (self.kind == "max" and self.extrema[-1][1] <= value)
                    or (self.kind == "min" and self.extrema[-1][1] >= value)
                ):
                    self.extrema.pop()
                self.extrema.append((self.count, value))
            result = self.extrema[0][1] if self.extrema else NAN
        return {self.name: result if self.valid == self.window else NAN}


@dataclass
class EMAState:
    name: str
    window: int
    smoothing: float = 2.0
    accumulator: float = NAN

    def feed(self, inputs: Mapping[str, float]) -> dict[str, float]:
        value = inputs["base_series"]
        if math.isnan(value):
            return {self.name: NAN}
        self.accumulator = ind.EMACalc.stream_endpoint(
            self.accumulator, value, self.window, self.smoothing, self.name
        )[self.name]
        return {self.name: self.accumulator}


@dataclass
class RSIState:
    name: str
    accumulator: RSIAccumulator

    def feed(self, inputs: Mapping[str, float]) -> dict[str, float]:
        return {self.name: self.accumulator.feed(inputs["base_series"])}


@dataclass
class MACDState:
    name: str
    signal: EMAState

    def feed(self, inputs: Mapping[str, float]) -> dict[str, float]:
        line = inputs["fast_ema"] - inputs["slow_ema"]
        signal = self.signal.feed({"base_series": line})[self.signal.name]
        return {self.name: line, f"{self.name}_signal": signal, f"{self.name}_hist": line - signal}


@dataclass
class ShiftState:
    name: str
    period: int
    values: deque[float] = field(default_factory=deque)

    def feed(self, inputs: Mapping[str, float]) -> dict[str, float]:
        value = inputs["base_series"]
        if not self.period:
            return {self.name: value}
        result = self.values.popleft() if len(self.values) == self.period else NAN
        self.values.append(value)
        return {self.name: result}


@dataclass
class TrendState:
    name: str
    length: int
    threshold: float
    direction: float = NAN
    run: int = 0
    valid_run: int = 0

    def feed(self, inputs: Mapping[str, float]) -> dict[str, float]:
        value = trend_direction(
            inputs["upper_bound"], inputs["lower_bound"], inputs["prev_base_series"], self.threshold
        )
        self.valid_run = min(self.length, self.valid_run + 1) if not math.isnan(value) else 0
        self.run = min(self.length, self.run + 1) if value == self.direction else 1
        self.direction = value
        result = value if self.run >= self.length else 0.0
        return {self.name: result if self.valid_run >= self.length else NAN}


# Explicit binding between declarative Series references and scalar endpoint arguments.
SCALAR_INPUTS = {
    "base_series": "cur_base",
    "adj_series": "cur_adj",
    "sma": "cur_sma",
    "sma1": "cur_sma1",
    "sma2": "cur_sma2",
    "prev_sma": "prev_sma",
    "s1": "cur_s1",
    "s2": "cur_s2",
    "prev_s1": "prev_s1",
    "prev_s2": "prev_s2",
    "upper_bound": "cur_upper_bound",
    "lower_bound": "cur_lower_bound",
    "upper_standard": "cur_upper_standard",
    "lower_standard": "cur_lower_standard",
    "cross_type": "cur_cross_type",
    "trend_type": "cur_trend_type",
}


@dataclass
class ScalarState:
    name: str
    implementation: type[BaseIndicator]
    parameters: dict[str, int | float]

    def feed(self, inputs: Mapping[str, float]) -> dict[str, float]:
        endpoint = cast(
            Callable[..., dict[str, float]], getattr(self.implementation, "stream_endpoint")
        )
        return endpoint(
            **{SCALAR_INPUTS[key]: value for key, value in inputs.items()},
            **self.parameters,
            name=self.name,
        )
