"""DataFrame convenience API. Reuse compile()/StreamEngine on streaming hot paths."""

import warnings
from collections.abc import Hashable, Iterable, Mapping

import pandas as pd

from .errors import ExecutionError
from .planning import ExecutionPlan, compile_plan, validate_frame
from .schema import BaseConfig, IndexConfig


class Config:
    @staticmethod
    def compile(index_config: IndexConfig, input_columns: Iterable[str]) -> ExecutionPlan:
        return compile_plan(index_config, input_columns)

    @staticmethod
    def config_order(index_config: IndexConfig) -> list[tuple[str, BaseConfig]]:
        # Compatibility ordering API has no frame schema. Full validation requires compile().
        tasks = [item for _, group in index_config for item in (group or {}).items()]
        outputs = {key for name, item in tasks for key in item.indicator_class.output_keys(name)}
        raw = sorted({ref for _, item in tasks for ref in item.column_mapping().values()} - outputs)
        return [(task.name, task.config) for task in compile_plan(index_config, raw).tasks]

    @staticmethod
    def vector_config(
        index_config: IndexConfig,
        df: pd.DataFrame,
        include_orign: bool | None = None,
        *,
        include_original: bool | None = None,
    ) -> pd.DataFrame:
        if include_orign is not None:
            warnings.warn(
                "include_orign is deprecated; use include_original",
                DeprecationWarning,
                stacklevel=2,
            )
            if include_original is not None:
                raise TypeError("pass only include_original, not both spellings")
            include_original = include_orign
        return compile_plan(index_config, df.columns).vector(
            df, include_original=True if include_original is None else include_original
        )

    @staticmethod
    def _raw(index_config: IndexConfig, df: pd.DataFrame) -> pd.DataFrame:
        if not df.columns.is_unique:
            raise ExecutionError("frame: duplicate column labels")
        outputs = {
            key
            for _, group in index_config
            for name, item in (group or {}).items()
            for key in item.indicator_class.output_keys(name)
        }
        return df.loc[:, [key for key in df.columns if key not in outputs]].copy()

    @classmethod
    def stream_update(
        cls,
        index_config: IndexConfig,
        df: pd.DataFrame,
        row: Mapping[str, float],
        *,
        index: Hashable | None = None,
    ) -> pd.DataFrame:
        """Replace the latest bar with a COMPLETE raw event; omitted index preserves its label."""
        raw = cls._raw(index_config, df)
        validate_frame(raw, tuple(raw.columns))
        if raw.empty:
            raise ExecutionError("update requires an existing bar")
        if index is not None and index != raw.index[-1]:
            raise ExecutionError("update requires the latest existing index")
        cls._validate_row(raw, row)
        raw.iloc[-1] = pd.Series(row)
        return cls.vector_config(index_config, raw)

    @classmethod
    def stream_rotate(
        cls,
        index_config: IndexConfig,
        df: pd.DataFrame,
        row: Mapping[str, float],
        *,
        index: Hashable | None = None,
    ) -> pd.DataFrame:
        """Append a COMPLETE raw event. Only RangeIndex can infer an omitted index."""
        raw = cls._raw(index_config, df)
        validate_frame(raw, tuple(raw.columns))
        cls._validate_row(raw, row)
        if index is None:
            if not isinstance(raw.index, pd.RangeIndex):
                raise ExecutionError("append requires an explicit index for non-RangeIndex frames")
            index = raw.index[-1] + raw.index.step if len(raw) else raw.index.start
        event = pd.DataFrame(
            [row], index=pd.Index([index], name=raw.index.name), columns=raw.columns
        )
        combined = pd.concat([raw, event])
        if isinstance(raw.index, pd.RangeIndex) and index == raw.index.stop:
            combined.index = pd.RangeIndex(
                raw.index.start,
                raw.index.stop + raw.index.step,
                raw.index.step,
                name=raw.index.name,
            )
        return cls.vector_config(index_config, combined)

    @staticmethod
    def _validate_row(raw: pd.DataFrame, row: Mapping[str, float]) -> None:
        if set(row) != set(raw.columns):
            raise ExecutionError("event fields must exactly match all raw columns")
        validate_frame(pd.DataFrame([row], columns=raw.columns), tuple(raw.columns))


# TODO: support data streaming using vector config chunck by chunck
# do research on where the thresh for using row by row or vector to config data are more efficient
