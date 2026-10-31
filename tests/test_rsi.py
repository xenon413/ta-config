import numpy as np
import pandas as pd
import pytest

from ta_config import Config, IndexConfig, RSICalc, StreamEngine


def test_wilder_seed_and_smoothing():
    # First three changes: +2, -1, +2 => gain 4/3, loss 1/3 => RSI 80.
    # Next change -2: gain 8/9, loss 8/9 => RSI 50.
    actual = RSICalc.vector_endpoint(pd.Series([10.0, 12.0, 11.0, 13.0, 11.0]), 3)
    np.testing.assert_allclose(actual.rsi_calc, [np.nan, np.nan, np.nan, 80, 50], equal_nan=True)


@pytest.mark.parametrize(
    "values,expected", [([1.0, 2.0, 3.0], 100), ([3.0, 2.0, 1.0], 0), ([2.0, 2.0, 2.0], 50)]
)
def test_extremes_and_flat_prices(values, expected):
    assert RSICalc.vector_endpoint(pd.Series(values), 2).iloc[-1, 0] == expected


def test_stream_append_and_repeated_open_candle_updates_match_vector():
    config = IndexConfig.model_validate({"rsi_calc": {"rsi": {"base": "close", "window": 3}}})
    raw = pd.DataFrame({"close": [10.0, 12.0, 11.0, 13.0, 11.0, np.nan, 14.0, 12.0, 16.0, 17.0]})
    plan = Config.compile(config, raw.columns)
    engine = StreamEngine(plan)
    for index, row in raw.iterrows():
        engine.step(row.to_dict(), index=index)
        for replacement in [15.0, 9.0, row.close]:
            updated = raw.iloc[: index + 1].copy()
            updated.iloc[-1, 0] = replacement
            result = engine.step({"close": replacement}, index=index, mode="update")
            expected = plan.vector(updated).rsi.iloc[-1]
            np.testing.assert_allclose(result.outputs["rsi"], expected, equal_nan=True)
    np.testing.assert_allclose(engine.snapshot().rsi, plan.vector(raw).rsi, equal_nan=True)


def test_rsi_missing_sample_restarts_warmup_and_preserves_index():
    raw = pd.Series([10.0, 11.0, 12.0, np.nan, 13.0, 14.0, 15.0], index=list("abcdefg"))
    actual = RSICalc.vector_endpoint(raw, 2, name="strength")
    assert actual.index.equals(raw.index)
    np.testing.assert_allclose(
        actual.strength, [np.nan, np.nan, 100, np.nan, np.nan, np.nan, 100], equal_nan=True
    )


def test_rsi_configuration_rejects_zero_window():
    with pytest.raises(ValueError):
        IndexConfig.model_validate({"rsi_calc": {"rsi": {"base": "close", "window": 0}}})
