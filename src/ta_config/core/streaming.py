"""Atomic, single-writer streaming with bounded indicator state and optional snapshots."""

import math
from collections import deque
from collections.abc import Hashable, Mapping
from copy import deepcopy
from dataclasses import dataclass
from enum import StrEnum
from numbers import Integral, Real
from threading import Lock
from types import MappingProxyType

import numpy as np
import pandas as pd

from .errors import ExecutionError
from .planning import ExecutionPlan, validate_frame, validate_scalars
from .state import IndicatorState


class StepMode(StrEnum):
    APPEND = "append"
    UPDATE = "update"


@dataclass(frozen=True)
class StepResult:
    index: Hashable
    sequence: int
    outputs: Mapping[str, float]
    ready: Mapping[str, bool]


class StreamEngine:
    """Serialize calls externally in event order; overlapping calls are rejected.

    A failed event commits nothing. Updates replay from the checkpoint BEFORE
    the latest bar. State and snapshot retention have independent fixed bounds.
    """

    def __init__(self, plan: ExecutionPlan, *, snapshot_size: int = 256):
        if type(snapshot_size) is not int or not 0 <= snapshot_size <= 100_000:
            raise ValueError("snapshot_size must be an integer in [0, 100000]")
        self._plan = plan
        self._states = [task.spec.state_factory(task.name, task.config) for task in plan.tasks]
        self._before_last: list[IndicatorState] | None = None
        self._last_index: Hashable | None = None
        self._index_name: Hashable | None = None
        self._sequence = 0
        self._records: deque[tuple[Hashable, dict[str, float]]] = deque(maxlen=snapshot_size)
        self._lock = Lock()

    @property
    def plan(self) -> ExecutionPlan:
        return self._plan

    @property
    def sequence(self) -> int:
        return self._sequence

    @property
    def last_index(self) -> Hashable | None:
        return self._last_index

    @classmethod
    def from_frame(
        cls, plan: ExecutionPlan, df: pd.DataFrame, *, snapshot_size: int = 256
    ) -> "StreamEngine":
        validate_frame(df, plan.input_columns)
        engine = cls(plan, snapshot_size=snapshot_size)
        engine._index_name = df.index.name
        for index, values in zip(df.index, df.itertuples(index=False, name=None), strict=True):
            engine.step(dict(zip(plan.input_columns, values, strict=True)), index=index)
        return engine

    def step(
        self,
        row: Mapping[str, float],
        *,
        index: Hashable,
        mode: StepMode | str = StepMode.APPEND,
        sequence: int | None = None,
    ) -> StepResult:
        if not self._lock.acquire(blocking=False):
            raise ExecutionError("overlapping calls: StreamEngine requires one ordered writer")
        try:
            try:
                selected_mode = StepMode(mode)
            except ValueError as exc:
                raise ExecutionError("mode must be append or update") from exc
            return self._step(row, index=index, mode=selected_mode, sequence=sequence)
        finally:
            self._lock.release()

    def _step(
        self, row: Mapping[str, float], *, index: Hashable, mode: StepMode, sequence: int | None
    ) -> StepResult:
        if sequence is not None and (type(sequence) is not int or sequence != self._sequence + 1):
            raise ExecutionError(f"expected event sequence {self._sequence + 1}")
        if not isinstance(index, (str, Integral, pd.Timestamp)) or isinstance(
            index, (bool, np.bool_)
        ):
            raise ExecutionError("event index must be an integer, string, or pandas Timestamp")
        if pd.isna(index) or index == "":
            raise ExecutionError("event index must not be missing or empty")
        if mode == StepMode.UPDATE:
            if self._last_index is None or index != self._last_index:
                raise ExecutionError("update requires the latest existing index")
            source = self._before_last
            assert source is not None
        else:
            if self._last_index is not None:
                try:
                    ordered = False
                    if isinstance(index, Integral) and isinstance(self._last_index, Integral):
                        ordered = int(index) > int(self._last_index)
                    elif isinstance(index, str) and isinstance(self._last_index, str):
                        ordered = index > self._last_index
                    elif isinstance(index, pd.Timestamp) and isinstance(
                        self._last_index, pd.Timestamp
                    ):
                        ordered = index > self._last_index
                except TypeError as exc:
                    raise ExecutionError("event index is incompatible with previous index") from exc
                if not ordered:
                    raise ExecutionError("append requires a new, strictly increasing index")
            source = self._states
        if set(row) != set(self.plan.input_columns):
            raise ExecutionError(
                f"event fields must exactly match raw schema {self.plan.input_columns!r}"
            )
        current: dict[str, float] = {}
        for key, value in row.items():
            if value is pd.NA or value is None:
                value = math.nan
            if (
                isinstance(value, (bool, np.bool_))
                or not isinstance(value, Real)
                or math.isinf(value)
            ):
                raise ExecutionError(f"event field {key!r}: expected real finite scalar or NaN")
            current[key] = float(value)
        # Transactional copies are bounded by configured lookback, never historical row count.
        candidate = deepcopy(source)
        outputs: dict[str, float] = {}
        for task, state in zip(self.plan.tasks, candidate, strict=True):
            try:
                values = state.feed({key: current[ref] for key, ref in task.inputs})
                values = validate_scalars(values, task)
            except Exception as exc:
                raise ExecutionError(
                    f"task {task.name!r}, {mode.value} mode, index {index!r}: {exc}"
                ) from exc
            current.update(values)
            outputs.update(values)
        if mode == StepMode.APPEND:
            self._before_last = self._states
        self._states = candidate
        self._last_index = index
        self._sequence += 1
        if self._records.maxlen:
            if mode == StepMode.UPDATE:
                self._records.pop()
            self._records.append((index, current))
        return StepResult(
            index,
            self._sequence,
            MappingProxyType(outputs),
            MappingProxyType({key: not math.isnan(value) for key, value in outputs.items()}),
        )

    def snapshot(self) -> pd.DataFrame:
        """Copy retained raw inputs and outputs; never used for computing the next event."""
        with self._lock:
            return pd.DataFrame(
                [dict(row) for _, row in self._records],
                index=pd.Index([index for index, _ in self._records], name=self._index_name),
                columns=(*self.plan.input_columns, *self.plan.output_columns),
            )
