import math

import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest
from pydantic import ValidationError

from ta_config import (
    Config,
    ConfigError,
    CrossType,
    CrossVal,
    ExecutionError,
    IndexConfig,
    SMA2SMACrossStandard,
    SMACalc,
    StreamEngine,
    TrendVal,
)


def config(**kwargs):
    return IndexConfig.model_validate(kwargs)


def test_sma_outgoing_sample_and_raw_persistence():
    cfg = config(sma_calc={"s": {"base": "x", "window": 3}})
    raw = pd.DataFrame({"x": [10.0, 20.0, 30.0]}, index=pd.Index([1, 2, 3]))
    frame = Config.vector_config(cfg, raw)
    result = Config.stream_rotate(cfg, frame, {"x": 40.0}, index=4)
    assert result.loc[4, "s"] == 30
    assert result.loc[4, "x"] == 40
    result = Config.stream_rotate(cfg, result, {"x": 50.0}, index=5)
    assert result.loc[5, "s"] == 40
    assert len(frame) == 3
    assert SMACalc.stream_endpoint(20, 10, 40, 3)["sma_calc"] == 30


def test_current_extrema_shift_and_timestamp_chain():
    cfg = config(
        window_max={"max": {"base": "x", "window": 3}},
        window_min={"min": {"base": "x", "window": 3}},
        shift={f"shift{p}": {"base": "x", "period": p} for p in (0, 1, 3)},
    )
    raw = pd.DataFrame({"x": [1.0, 5.0, 2.0]}, index=pd.date_range("2026-01-01", periods=3))
    frame = Config.vector_config(cfg, raw)
    for i, x in enumerate([10.0, -4.0, 8.0], 3):
        index = pd.Timestamp("2026-01-01") + pd.Timedelta(days=i)
        frame = Config.stream_rotate(cfg, frame, {"x": x}, index=index)
        raw.loc[index] = x
        pdt.assert_frame_equal(frame, Config.vector_config(cfg, raw), check_freq=False)
    assert frame.iloc[3]["max"] == 10
    assert frame.iloc[3]["shift1"] == 2
    assert frame.iloc[3]["shift0"] == 10
    assert frame.iloc[3]["shift3"] == 1


def test_update_replaces_latest_atomically_and_repeatedly():
    cfg = config(
        ema_calc={"ema": {"base": "x", "window": 3}}, sma_calc={"sma": {"base": "x", "window": 2}}
    )
    raw = pd.DataFrame({"x": [10.0, 20.0, 30.0]})
    engine = StreamEngine.from_frame(Config.compile(cfg, raw.columns), raw)
    for x in [40.0, 50.0, 15.0]:
        result = engine.step({"x": x}, index=2, mode="update")
        raw.loc[2, "x"] = x
        expected = Config.vector_config(cfg, raw)
        np.testing.assert_allclose(list(result.outputs.values()), expected.iloc[-1, 1:])
        pdt.assert_frame_equal(engine.snapshot(), expected, check_dtype=False)
    before = engine.snapshot()
    sequence = engine.sequence
    for row, idx, mode in [
        ({"x": math.inf}, 3, "append"),
        ({"x": 1.0}, 1, "update"),
        ({"x": 1.0}, 2, "append"),
        ({}, 3, "append"),
    ]:
        with pytest.raises(ExecutionError):
            engine.step(row, index=idx, mode=mode)
    assert engine.sequence == sequence
    pdt.assert_frame_equal(before, engine.snapshot())


def test_independent_boundaries_and_indexes():
    index = pd.date_range("2026-01-01", periods=2)
    s = pd.Series([1.0, 2.0], index=index)
    equal = SMA2SMACrossStandard.vector_endpoint(s, s, s, 2, 2, name="eq")
    pdt.assert_series_equal(equal["eq"], s, check_names=False)
    assert SMA2SMACrossStandard.stream_endpoint(3, 2, 2, 2, 2)["sma2sma_cross_standard"] == 3
    cross = CrossType.stream_endpoint(1, 1, 1, 1)
    assert cross["cross_type"] == 2
    assert math.isnan(CrossVal.stream_endpoint(1, 1, 10, 2)["cross_val"])
    result = TrendVal.vector_endpoint(s, s + 10, s + 5, s + 8, s + 2, s * 0 - 1)
    assert result.index.equals(index)
    assert list(result.iloc[:, 0]) == [0, 0]


@pytest.mark.parametrize("window", [0, -1, True, "3", 1.5, 100001])
def test_strict_windows(window):
    with pytest.raises(ValidationError):
        config(sma_calc={"s": {"base": "x", "window": window}})


@pytest.mark.parametrize("smoothing", [0, -1, 5, float("nan"), float("inf"), True, "2"])
def test_strict_smoothing(smoothing):
    with pytest.raises(ValidationError):
        config(ema_calc={"e": {"base": "x", "window": 2, "smoothing": smoothing}})


def test_other_strict_fields():
    for data in [
        {"shift": {"s": {"base": "x", "period": -1}}},
        {
            "trend_type": {
                "t": {
                    "upper_bound": "x",
                    "lower_bound": "x",
                    "prev_base": "x",
                    "thresh": float("nan"),
                    "trend_len": 2,
                }
            }
        },
        {"sma_calc": {"": {"base": "x", "window": 2}}},
        {"sma_calc": {"s": {"base": " ", "window": 2}}},
        {"sma_calc": {"s": {"base": "x", "window": 2, "indicator_class": SMACalc}}},
    ]:
        with pytest.raises(ValidationError):
            IndexConfig.model_validate(data)


def test_compiler_aggregates_collisions_unknowns_cycles():
    cfg = config(
        sma_calc={
            "same": {"base": "absent", "window": 2},
            "loop1": {"base": "loop2", "window": 2},
            "loop2": {"base": "loop1", "window": 2},
        },
        ema_calc={"same": {"base": "also_absent", "window": 2}},
    )
    with pytest.raises(ConfigError) as error:
        Config.compile(cfg, ["same", "same"])
    message = str(error.value)
    for text in (
        "duplicate column",
        "duplicate task",
        "shadows raw",
        "unresolved",
        "loop1",
        "loop2",
    ):
        assert text in message


def test_multi_output_collision_and_deep_graph():
    cfg = config(
        macd_calc={"m": {"fast_ema": "x", "slow_ema": "x", "signal": 2}},
        shift={"m_signal": {"base": "x", "period": 1}},
    )
    with pytest.raises(ConfigError, match="duplicate output"):
        Config.compile(cfg, ["x"])
    cfg = config(
        shift={f"s{i}": {"base": "x" if i == 0 else f"s{i - 1}", "period": 0} for i in range(1500)}
    )
    assert len(Config.compile(cfg, ["x"]).tasks) == 1500


def test_config_and_plan_immutable_json():
    cfg = config(sma_calc={"s": {"base": "x", "window": 2}})
    with pytest.raises(TypeError):
        cfg.sma_calc["bad"] = cfg.sma_calc["s"]
    with pytest.raises(ValidationError):
        cfg.sma_calc["s"].window = 4
    restored = IndexConfig.model_validate_json(cfg.model_dump_json())
    assert restored == cfg
    plan = Config.compile(cfg, ["x"])
    with pytest.raises(AttributeError):
        plan.input_columns = ("y",)


@pytest.mark.parametrize(
    "frame",
    [
        pd.DataFrame([[1, 2]], columns=["x", "x"]),
        pd.DataFrame({"x": [1.0, 2.0]}, index=[1, 1]),
        pd.DataFrame({"x": [1.0, 2.0]}, index=[2, 1]),
        pd.DataFrame({"x": ["bad"]}),
        pd.DataFrame({"x": [True]}),
        pd.DataFrame({"x": [complex(1, 2)]}),
        pd.DataFrame({"x": [math.inf]}),
    ],
)
def test_bad_frames(frame):
    with pytest.raises(ConfigError):
        Config.vector_config(config(), frame)


def test_output_contracts_and_atomic_failure(monkeypatch):
    cfg = config(sma_calc={"s": {"base": "x", "window": 2}})
    raw = pd.DataFrame({"x": [1.0, 2.0]})
    plan = Config.compile(cfg, raw.columns)
    for bad in [
        pd.Series([1, 2]),
        pd.DataFrame({"wrong": [1, 2]}),
        pd.DataFrame({"s": [1, 2]}, index=[2, 3]),
        pd.DataFrame({"s": ["bad", "bad"]}),
        pd.DataFrame({"s": [1, math.inf]}),
    ]:
        monkeypatch.setattr(SMACalc, "vector_endpoint", lambda **kwargs: bad)
        with pytest.raises(ExecutionError, match="task 's'"):
            plan.vector(raw)
    from ta_config.core.state import RollingState

    engine = StreamEngine(plan)
    engine.step({"x": 1.0}, index=0)
    before = engine.snapshot()
    monkeypatch.setattr(RollingState, "feed", lambda self, inputs: {"wrong": 1})
    with pytest.raises(ExecutionError, match="task 's'.*index 1"):
        engine.step({"x": 2.0}, index=1)
    assert engine.sequence == 1
    pdt.assert_frame_equal(before, engine.snapshot())


def test_empty_frames_and_alias_and_complete_rows():
    cfg = config(sma_calc={"s": {"base": "x", "window": 2}})
    empty = pd.DataFrame({"x": pd.Series(dtype=float)})
    assert list(Config.vector_config(cfg, empty).columns) == ["x", "s"]
    with pytest.warns(DeprecationWarning):
        assert list(Config.vector_config(cfg, empty, include_orign=False)) == ["s"]
    with pytest.warns(DeprecationWarning), pytest.raises(TypeError):
        Config.vector_config(cfg, empty, False, include_original=True)
    with pytest.raises(ExecutionError):
        Config.stream_update(cfg, empty, {"x": 1})
    with pytest.raises(ExecutionError):
        Config.stream_rotate(cfg, empty, {"wrong": 1})
    assert Config.vector_config(config(), empty, include_original=False).empty


def test_sequence_snapshot_bound_and_handlers():
    cfg = config(window_max={"mx": {"base": "x", "window": 3}})
    engine = StreamEngine(Config.compile(cfg, ["x"]), snapshot_size=2)
    for i in range(10):
        engine.step({"x": float(i)}, index=i, sequence=i + 1)
    assert len(engine.snapshot()) == 2
    assert len(engine._states[0].values) == 3
    with pytest.raises(ExecutionError, match="sequence"):
        engine.step({"x": 10.0}, index=10, sequence=10)
    frame = pd.DataFrame({"x": [1.0, 5.0, 2.0]})
    task = engine.plan.tasks[0]
    result = task.spec.implementation.stream_handler(
        base_series=frame.x, window=3, prev_df=frame, cur_row={"x": 10.0}, name="mx"
    )
    assert result["mx"] == 10


def test_range_append_chain_and_dataframe_updates():
    cfg = config(sma_calc={"s": {"base": "x", "window": 2}})
    frame = Config.vector_config(cfg, pd.DataFrame({"x": [1.0, 2.0]}))
    for x in [3.0, 4.0]:
        frame = Config.stream_rotate(cfg, frame, {"x": x})
    assert isinstance(frame.index, pd.RangeIndex)
    assert frame.iloc[-1]["s"] == 3.5
    before = frame.copy()
    result = Config.stream_update(cfg, frame, {"x": 10.0})
    assert result.iloc[-1]["s"] == 6.5
    pdt.assert_frame_equal(before, frame)
    with pytest.raises(ExecutionError):
        Config.stream_update(cfg, frame, {"x": 10.0}, index=1)
    with pytest.raises(ExecutionError):
        Config.stream_rotate(cfg, frame.set_axis([2, 4, 6, 8]), {"x": 10.0})
    assert [name for name, _ in Config.config_order(cfg)] == ["s"]


@pytest.mark.parametrize(
    "index",
    [
        pd.MultiIndex.from_tuples([(1, 2)]),
        pd.Index([math.nan]),
        pd.Index([1.5]),
        pd.Index([True]),
        pd.Index([""]),
    ],
)
def test_unsupported_frame_indexes(index):
    with pytest.raises(ConfigError):
        Config.vector_config(config(), pd.DataFrame({"x": [1.0]}, index=index))


def test_engine_guards_index_names_and_read_only_results():
    cfg = config(sma_calc={"s": {"base": "x", "window": 2}})
    raw = pd.DataFrame({"x": [1.0]}, index=pd.Index(["a"], name="bar"))
    plan = Config.compile(cfg, ["x"])
    engine = StreamEngine.from_frame(plan, raw)
    assert engine.last_index == "a"
    assert engine.snapshot().index.name == "bar"
    with pytest.raises(AttributeError):
        engine.plan = plan
    for index, mode in [
        (1.5, "append"),
        (True, "append"),
        ("", "append"),
        (pd.NaT, "append"),
        ("b", "unknown"),
    ]:
        with pytest.raises(ExecutionError):
            engine.step({"x": 2.0}, index=index, mode=mode)
    with pytest.raises(ValueError):
        StreamEngine(plan, snapshot_size=-1)
    engine._lock.acquire()
    try:
        with pytest.raises(ExecutionError, match="overlapping"):
            engine.step({"x": 2.0}, index="b")
    finally:
        engine._lock.release()
    result = engine.step({"x": 2.0}, index="b")
    with pytest.raises(TypeError):
        result.outputs["s"] = 100
    with pytest.raises(TypeError):
        result.ready["s"] = False
    changed = engine.snapshot()
    changed.loc["b", "x"] = 100
    assert engine.snapshot().loc["b", "x"] == 2


def test_resource_limits_and_bypassed_models(monkeypatch):
    from ta_config import SMACalcConfig
    from ta_config.core import planning

    monkeypatch.setattr(planning, "MAX_TASKS", 1)
    monkeypatch.setattr(planning, "MAX_STATE_SAMPLES", 2)
    cfg = config(sma_calc={"s": {"base": "x", "window": 3}, "t": {"base": "x", "window": 3}})
    with pytest.raises(ConfigError) as error:
        Config.compile(cfg, ["x"])
    assert "tasks" in str(error.value) and "state samples" in str(error.value)
    bad = IndexConfig.model_construct(
        sma_calc={"s": SMACalcConfig.model_construct(base_series="x", window=0)}
    )
    with pytest.raises(ConfigError, match="task 's'"):
        Config.compile(bad, ["x"])
    wrong = IndexConfig.model_construct(sma_calc={"s": "untrusted"})
    with pytest.raises(ConfigError, match="trusted"):
        Config.compile(wrong, ["x"])


def test_scalar_contracts_and_series_alignment():
    from ta_config.core.planning import validate_scalars

    task = Config.compile(config(sma_calc={"s": {"base": "x", "window": 1}}), ["x"]).tasks[0]
    for bad in [{"s": True}, {"s": math.inf}, {"s": "x"}, {"s": [1]}, []]:
        with pytest.raises(ExecutionError):
            validate_scalars(bad, task)
    from ta_config import RelativePosition

    with pytest.raises(ValueError, match="identical indexes"):
        RelativePosition.vector(
            {"s1": pd.Series([1], index=[1]), "s2": pd.Series([1], index=[2])}, {}, "r"
        )


def test_timezone_mismatch_rejected_atomically():
    engine = StreamEngine(Config.compile(config(), ["x"]))
    engine.step({"x": 1.0}, index=pd.Timestamp("2026-01-01", tz="UTC"))
    with pytest.raises(ExecutionError):
        engine.step({"x": 2.0}, index=pd.Timestamp("2026-01-02"))
    assert engine.sequence == 1
