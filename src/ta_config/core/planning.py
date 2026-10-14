"""Immutable compilation and preflight/result-contract validation."""

import math
from collections import deque
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from numbers import Integral, Real
from typing import Any

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_complex_dtype, is_numeric_dtype

from .errors import ConfigError, ExecutionError
from .registry import REGISTRY, IndicatorSpec
from .schema import BaseConfig, IndexConfig

MAX_TASKS = 4096
MAX_STATE_SAMPLES = 1_000_000


@dataclass(frozen=True)
class Task:
    name: str
    spec: IndicatorSpec
    config: BaseConfig
    inputs: tuple[tuple[str, str], ...]
    outputs: tuple[str, ...]


@dataclass(frozen=True)
class ExecutionPlan:
    tasks: tuple[Task, ...]
    input_columns: tuple[str, ...]
    output_columns: tuple[str, ...]
    state_samples: int

    def vector(self, df: pd.DataFrame, *, include_original: bool = True) -> pd.DataFrame:
        validate_frame(df, self.input_columns)
        available = {key: df[key] for key in self.input_columns}
        results = [df.copy()] if include_original else []
        for task in self.tasks:
            try:
                result = task.spec.implementation.vector(
                    {key: available[ref] for key, ref in task.inputs},
                    task.config.parameters(),
                    task.name,
                )
                validate_vector(result, task, df.index)
            except Exception as exc:
                raise ExecutionError(f"task {task.name!r}, vector mode: {exc}") from exc
            results.append(result)
            available.update({key: result[key] for key in task.outputs})
        return pd.concat(results, axis=1) if results else pd.DataFrame(index=df.index)


def compile_plan(config: IndexConfig, input_columns: Iterable[str]) -> ExecutionPlan:
    columns = tuple(input_columns)
    errors: list[str] = []
    if len(columns) != len(set(columns)):
        errors.append("input schema: duplicate column labels")
    if any(not isinstance(c, str) or not c.strip() for c in columns):
        errors.append("input schema: expected nonempty string column labels")
    tasks: dict[str, Task] = {}
    owners: dict[str, str] = {}
    samples = 0
    for category, spec in REGISTRY.items():
        for name, item in (getattr(config, category) or {}).items():
            if type(item) is not spec.config_type:
                errors.append(f"task {name!r}: expected trusted {spec.config_type.__name__}")
                continue
            # Revalidate to catch model_construct/model_copy bypasses.
            try:
                item = spec.config_type.model_validate(item.model_dump())
            except ValueError as exc:
                errors.append(f"task {name!r}: {exc}")
                continue
            if name in tasks:
                errors.append(f"task {name!r}: duplicate task identifier")
            outputs = spec.implementation.output_keys(name)
            tasks[name] = Task(name, spec, item, tuple(item.column_mapping().items()), outputs)
            for output in outputs:
                if output in owners:
                    errors.append(f"task {name!r}, output {output!r}: duplicate output")
                if output in columns:
                    errors.append(f"task {name!r}, output {output!r}: shadows raw input")
                owners[output] = name
            samples += max(
                (
                    int(v)
                    for k, v in item.parameters().items()
                    if k in ("window", "period", "trend_len")
                ),
                default=1,
            )
    if len(tasks) > MAX_TASKS:
        errors.append(f"graph exceeds {MAX_TASKS} tasks")
    if samples > MAX_STATE_SAMPLES:
        errors.append(f"graph exceeds {MAX_STATE_SAMPLES} state samples")
    for name in tasks:
        if name in owners and owners[name] != name:
            errors.append(f"task {name!r}: identifier collides with output of {owners[name]!r}")
        if name in columns:
            errors.append(f"task {name!r}: identifier collides with raw input")
    dependencies: dict[str, set[str]] = {}
    followers: dict[str, list[str]] = {name: [] for name in tasks}
    for name, task in tasks.items():
        dependencies[name] = set()
        for field, ref in task.inputs:
            if ref in owners:
                dependencies[name].add(owners[ref])
            elif ref not in columns:
                errors.append(
                    f"task {name!r}, field {field!r}, reference {ref!r}: unresolved input"
                )
        for dep in sorted(dependencies[name]):
            followers[dep].append(name)
    queue = deque(name for name in tasks if not dependencies[name])
    ordered = []
    while queue:
        name = queue.popleft()
        ordered.append(tasks[name])
        for follower in followers[name]:
            dependencies[follower].remove(name)
            if not dependencies[follower]:
                queue.append(follower)
    remaining = [name for name in tasks if dependencies[name]]
    if remaining:
        edges = [f"{name} -> {','.join(sorted(dependencies[name]))}" for name in remaining]
        errors.append("cyclic dependency (including blocked dependents): " + "; ".join(edges))
    if errors:
        raise ConfigError(errors)
    return ExecutionPlan(
        tuple(ordered), columns, tuple(key for task in ordered for key in task.outputs), samples
    )


def validate_frame(df: pd.DataFrame, columns: tuple[str, ...]) -> None:
    errors = []
    if not df.columns.is_unique:
        errors.append("frame: duplicate column labels")
    if tuple(df.columns) != columns:
        errors.append(f"frame schema: expected columns {columns!r}")
    if (
        isinstance(df.index, pd.MultiIndex)
        or not df.index.is_unique
        or not df.index.is_monotonic_increasing
    ):
        errors.append("frame index: expected unique, increasing, single-level labels")
    if not isinstance(df.index, pd.MultiIndex) and df.index.hasnans:
        errors.append("frame index: missing labels are forbidden")
    if any(
        not isinstance(label, (str, Integral, pd.Timestamp))
        or isinstance(label, (bool, np.bool_))
        or label == ""
        for label in df.index
    ):
        errors.append("frame index: expected integer, string, or Timestamp labels")
    for key in df.columns.unique():
        value = df[key]
        if isinstance(value, pd.DataFrame):
            continue
        if (
            not is_numeric_dtype(value.dtype)
            or is_bool_dtype(value.dtype)
            or is_complex_dtype(value.dtype)
        ):
            errors.append(f"column {key!r}: expected real numeric dtype")
        elif np.isinf(value.to_numpy(dtype=float, na_value=np.nan)).any():
            errors.append(f"column {key!r}: infinity is forbidden")
    if errors:
        raise ConfigError(errors)


def validate_vector(result: Any, task: Task, index: pd.Index) -> None:
    if not isinstance(result, pd.DataFrame):
        raise ExecutionError("expected a DataFrame")
    if tuple(result.columns) != task.outputs or not result.columns.is_unique:
        raise ExecutionError(f"expected output keys {task.outputs!r}")
    if not result.index.equals(index):
        raise ExecutionError("output index/length differs from input")
    for key in task.outputs:
        values = result[key]
        if (
            not is_numeric_dtype(values.dtype)
            or is_bool_dtype(values.dtype)
            or is_complex_dtype(values.dtype)
        ):
            raise ExecutionError(f"output {key!r}: expected real numeric values")
        if np.isinf(values.to_numpy(dtype=float, na_value=np.nan)).any():
            raise ExecutionError(f"output {key!r}: infinity is forbidden")


def validate_scalars(result: Any, task: Task) -> dict[str, float]:
    if not isinstance(result, Mapping) or set(result) != set(task.outputs):
        raise ExecutionError(f"expected output keys {task.outputs!r}")
    normalized = {}
    for key, value in result.items():
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real) or math.isinf(value):
            raise ExecutionError(f"output {key!r}: expected real finite scalar or NaN")
        normalized[key] = float(value)
    return normalized
