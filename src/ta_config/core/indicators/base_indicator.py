"""Shared compatibility adapters; concrete indicators own their formulas."""

from collections.abc import Callable, Mapping
from typing import Any, ClassVar, Protocol, cast

import pandas as pd


class IndicatorProtocol(Protocol):
    def vector(
        self, inputs: Mapping[str, pd.Series], parameters: Mapping[str, Any], name: str
    ) -> pd.DataFrame: ...


class BaseIndicator:
    name: ClassVar[str] = "indicator"
    output_key_parts: ClassVar[tuple[tuple[str, str], ...]] = (("", ""),)

    @classmethod
    def output_keys(cls, name: str) -> tuple[str, ...]:
        return tuple(f"{prefix}{name}{suffix}" for prefix, suffix in cls.output_key_parts)

    @classmethod
    def vector(
        cls, inputs: Mapping[str, pd.Series], parameters: Mapping[str, Any], name: str
    ) -> pd.DataFrame:
        series = list(inputs.values())
        if series and any(not s.index.equals(series[0].index) for s in series):
            raise ValueError("input Series must have identical indexes")
        endpoint = cast(Callable[..., pd.DataFrame], getattr(cls, "vector_endpoint"))
        return endpoint(**inputs, **parameters, name=name)

    @classmethod
    def stream_handler(
        cls,
        *,
        prev_df: pd.DataFrame,
        cur_row: Mapping[str, float],
        name: str | None = None,
        **kwargs: Any,
    ) -> dict[str, float]:
        """Compatibility replay: Series contain history EXCLUDING the current bar.

        Use StreamEngine for bounded state. Mapped previous-value inputs use the
        current mapped scalar, exactly as in vector mode.
        """
        inputs = {}
        parameters = {}
        for key, value in kwargs.items():
            if isinstance(value, pd.Series):
                inputs[key] = pd.Series(
                    [*value.to_numpy(dtype=float), cur_row[str(value.name)]], dtype=float
                )
            else:
                parameters[key] = value
        result = cls.vector(inputs, parameters, name or cls.name)
        return {str(key): float(value) for key, value in result.iloc[-1].items()}
