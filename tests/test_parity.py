import math

import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest

from ta_config import Config, IndexConfig, StreamEngine


def all_indicator_config(trend_len=3):
    return IndexConfig.model_validate(
        {
            "sma_calc": {"s": {"base": "x", "window": 3}, "l": {"base": "x", "window": 7}},
            "ema_calc": {"e": {"base": "x", "window": 3}, "f": {"base": "s", "window": 5}},
            "macd_calc": {"m": {"fast_ema": "e", "slow_ema": "f", "signal": 3}},
            "sma_trend": {"maint": {"base": "x", "sma": "s", "prev_sma": "l", "window": 3}},
            "sma_adjust": {"adj": {"base": "x", "adj": "hi", "window": 3}},
            "sma2sma_cross_standard": {
                "standard": {"base": "x", "sma1": "s", "sma2": "l", "window1": 3, "window2": 7},
                "equal": {"base": "x", "sma1": "s", "sma2": "s", "window1": 3, "window2": 3},
            },
            "shift": {
                "prev_s": {"base": "s", "period": 1},
                "prev_l": {"base": "l", "period": 1},
                "prev_x": {"base": "x", "period": 1},
                "same": {"base": "x", "period": 0},
            },
            "cross_type": {
                "cross": {
                    "s1": "s",
                    "s2": "l",
                    "prev_s1": "prev_s",
                    "prev_s2": "prev_l",
                    "upper_bound": "hi",
                    "lower_bound": "lo",
                    "upper_standard": "standard",
                    "lower_standard": "standard",
                }
            },
            "cross_val": {"price": {"s1": "s", "s2": "l", "base": "x", "cross_type": "cross"}},
            "trend_type": {
                "trend": {
                    "upper_bound": "hi",
                    "lower_bound": "lo",
                    "prev_base": "prev_x",
                    "thresh": 0.01,
                    "trend_len": trend_len,
                }
            },
            "trend_val": {
                "trend_price": {
                    "upper_bound": "hi",
                    "lower_bound": "lo",
                    "upper_standard": "s",
                    "lower_standard": "l",
                    "trend_type": "trend",
                    "base": "x",
                }
            },
            "window_max": {"max": {"base": "x", "window": 4}},
            "window_min": {"min": {"base": "x", "window": 4}},
            "relative_pos": {"pos": {"s1": "s", "s2": "l"}},
        }
    )


@pytest.mark.parametrize("trend_len", [1, 2, 3, 5])
@pytest.mark.parametrize("index_kind", ["integer", "timestamp"])
def test_every_indicator_every_step_updates_missing_and_handlers(trend_len, index_kind):
    rng = np.random.default_rng(417)
    x = rng.normal(100, 10, 65)
    x[[0, 10, 11, 32]] = np.nan
    x[20] = 0
    raw = pd.DataFrame({"x": x, "hi": x + 2, "lo": x - 2})
    raw.index = (
        pd.Index(np.arange(len(raw)) * 3 + 1)
        if index_kind == "integer"
        else pd.date_range("2026-01-01", periods=len(raw), freq="min", tz="UTC")
    )
    cfg = all_indicator_config(trend_len)
    plan = Config.compile(cfg, raw.columns)
    engine = StreamEngine(plan, snapshot_size=10)
    for i in range(len(raw)):
        row = raw.iloc[i].to_dict()
        result = engine.step(row, index=raw.index[i])
        expected = plan.vector(raw.iloc[: i + 1])
        np.testing.assert_allclose(
            list(result.outputs.values()),
            expected.iloc[-1, 3:],
            equal_nan=True,
            rtol=1e-10,
            atol=1e-10,
        )
        assert list(result.ready.values()) == list(expected.iloc[-1, 3:].notna())
        if i % 9 == 0:
            changed = {key: val + 3 for key, val in row.items()}
            edited = raw.iloc[: i + 1].copy()
            edited.iloc[-1] = pd.Series(changed)
            update = engine.step(changed, index=raw.index[i], mode="update")
            np.testing.assert_allclose(
                list(update.outputs.values()),
                plan.vector(edited).iloc[-1, 3:],
                equal_nan=True,
                rtol=1e-10,
                atol=1e-10,
            )
            engine.step(row, index=raw.index[i], mode="update")
        pdt.assert_frame_equal(
            engine.snapshot(),
            expected.tail(10),
            check_dtype=False,
            check_freq=False,
            rtol=1e-10,
            atol=1e-10,
        )
    # Every public history adapter must follow the same input convention.
    expected = plan.vector(raw)
    previous = expected.iloc[:-1]
    current = raw.iloc[-1].to_dict()
    for task in plan.tasks:
        values = task.spec.implementation.stream_handler(
            **{key: previous[ref] for key, ref in task.inputs},
            **task.config.parameters(),
            prev_df=previous,
            cur_row=current,
            name=task.name,
        )
        np.testing.assert_allclose(
            list(values.values()),
            expected.loc[raw.index[-1], list(task.outputs)],
            equal_nan=True,
            rtol=1e-10,
            atol=1e-10,
        )
        current.update(values)


def test_thousands_of_events_drift_and_constant_storage():
    rng = np.random.default_rng(7)
    raw = pd.DataFrame({"x": 1e6 + rng.normal(0, 10, 5000)})
    cfg = IndexConfig.model_validate(
        {
            "sma_calc": {"s": {"base": "x", "window": 31}},
            "ema_calc": {"e": {"base": "x", "window": 17}},
            "window_max": {"mx": {"base": "x", "window": 21}},
            "window_min": {"mn": {"base": "x", "window": 21}},
        }
    )
    plan = Config.compile(cfg, raw.columns)
    expected = plan.vector(raw, include_original=False)
    engine = StreamEngine(plan, snapshot_size=0)
    results = [dict(engine.step({"x": x}, index=i).outputs) for i, x in enumerate(raw.x)]
    pdt.assert_frame_equal(pd.DataFrame(results), expected, rtol=1e-12, atol=1e-8)
    assert engine.snapshot().empty
    assert len(engine._states[0].values) == 31
    assert len(engine._states[2].extrema) <= 21


def test_trend_confirmation_current_bar_and_zero_policy():
    cfg = IndexConfig.model_validate(
        {
            "trend_type": {
                "t": {
                    "upper_bound": "u",
                    "lower_bound": "l",
                    "prev_base": "b",
                    "thresh": 0.05,
                    "trend_len": 3,
                }
            }
        }
    )
    plan = Config.compile(cfg, ["u", "l", "b"])
    engine = StreamEngine(plan)
    results = [
        engine.step({"u": 12.0, "l": 11.0, "b": 10.0}, index=i).outputs["t"] for i in range(3)
    ]
    assert math.isnan(results[0]) and math.isnan(results[1])
    assert results[2] == 1
    assert engine.step({"u": 9.0, "l": 8.0, "b": 10.0}, index=3).outputs["t"] == 0
    assert math.isnan(engine.step({"u": 9.0, "l": 8.0, "b": 0.0}, index=4).outputs["t"])


def test_random_valid_graphs():
    for seed in range(12):
        rng = np.random.default_rng(seed)
        cfg = {"sma_calc": {}, "shift": {}, "relative_pos": {}}
        names = ["x"]
        for n in range(12):
            name = f"n{n}"
            source = str(rng.choice(names))
            kind = n % 3
            if kind == 0:
                cfg["sma_calc"][name] = {"base": source, "window": int(rng.integers(1, 5))}
            elif kind == 1:
                cfg["shift"][name] = {"base": source, "period": int(rng.integers(0, 4))}
            else:
                cfg["relative_pos"][name] = {"s1": source, "s2": "x"}
            names.append(name)
        plan = Config.compile(IndexConfig.model_validate(cfg), ["x"])
        raw = pd.DataFrame({"x": rng.normal(size=30)})
        engine = StreamEngine(plan)
        expected = plan.vector(raw, include_original=False)
        results = [dict(engine.step({"x": x}, index=i).outputs) for i, x in enumerate(raw.x)]
        pdt.assert_frame_equal(pd.DataFrame(results), expected, check_dtype=False, atol=1e-12)
