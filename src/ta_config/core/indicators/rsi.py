"""Wilder RSI, seeded with the simple average of the first window changes."""

import math
from dataclasses import dataclass

import pandas as pd

from .base_indicator import BaseIndicator


@dataclass
class RSIAccumulator:
    window: int
    previous: float = math.nan
    count: int = 0
    gain: float = 0.0
    loss: float = 0.0

    def feed(self, value: float) -> float:
        if math.isnan(value):
            self.previous, self.count, self.gain, self.loss = math.nan, 0, 0.0, 0.0
            return math.nan
        previous, self.previous = self.previous, value
        if math.isnan(previous):
            return math.nan
        change = value - previous
        gain, loss = max(change, 0.0), max(-change, 0.0)
        if self.count < self.window:
            self.count += 1
            self.gain += gain / self.window
            self.loss += loss / self.window
            if self.count < self.window:
                return math.nan
        else:
            self.gain += (gain - self.gain) / self.window
            self.loss += (loss - self.loss) / self.window
        if self.loss == 0:
            return 100.0 if self.gain > 0 else 50.0
        return 100.0 - 100.0 / (1.0 + self.gain / self.loss)


class RSICalc(BaseIndicator):
    name = "rsi_calc"

    @classmethod
    def vector_endpoint(
        cls, base_series: pd.Series, window: int, name: str = "rsi_calc"
    ) -> pd.DataFrame:
        if window <= 0:
            raise ValueError("RSI window must be positive")
        accumulator = RSIAccumulator(window)
        return pd.DataFrame(
            {name: [accumulator.feed(float(value)) for value in base_series]},
            index=base_series.index,
            dtype=float,
        )
