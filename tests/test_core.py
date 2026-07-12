import json
from pathlib import Path

import pandas as pd
import pandas.testing as pdt
import pytest

from ta_config.core.schema import IndexConfig
from ta_config.core.indicators import SMACalc, Shift, CrossType, CrossVal, EMACalc, MACDCalc


CONFIG_PATH = Path(__file__).parent / "data" / "config" / "test_config.json"


@pytest.fixture(scope="module")
def base_df():
    return pd.DataFrame(
        {
            "open": [10.0, 11.0, 12.0, 13.0, 14.0],
            "high": [11.0, 12.0, 13.0, 14.0, 15.0],
            "low": [9.0, 10.0, 11.0, 12.0, 13.0],
            "close": [10.0, 12.0, 11.0, 14.0, 13.0],
        }
    )


@pytest.fixture(scope="module")
def index_config():
    with CONFIG_PATH.open("r", encoding="utf-8") as fp:
        return IndexConfig.model_validate(json.load(fp))


@pytest.mark.unit
def test_vector_config_with_dependency_chain(base_df:pd.DataFrame, index_config:IndexConfig):
    res = index_config.config(base_df)

    expected_columns = {
        "sma_short",
        "sma_long",
        "prev_sma_short",
        "prev_sma_long",
        "cross_type",
        "cross_val",
        "ema_fast",
        "ema_slow",
        "macd",
        "macd_signal",
        "macd_hist",
    }
    assert expected_columns.issubset(set(res.columns))

    expected_sma_short = SMACalc.vector_endpoint(
        base_series=base_df["close"],
        window=2,
        name="sma_short",
    )["sma_short"]
    expected_sma_long = SMACalc.vector_endpoint(
        base_series=base_df["close"],
        window=3,
        name="sma_long",
    )["sma_long"]
    expected_prev_sma_short = Shift.vector_endpoint(
        base_series=expected_sma_short,
        period=1,
        name="prev_sma_short",
    )["prev_sma_short"]
    expected_prev_sma_long = Shift.vector_endpoint(
        base_series=expected_sma_long,
        period=1,
        name="prev_sma_long",
    )["prev_sma_long"]
    expected_cross_type = CrossType.vector_endpoint(
        s1=expected_sma_short,
        s2=expected_sma_long,
        prev_s1=expected_prev_sma_short,
        prev_s2=expected_prev_sma_long,
        upper_bound=None,
        lower_bound=None,
        upper_standard=None,
        lower_standard=None,
        name="cross_type",
    )["cross_type"]
    expected_cross_val = CrossVal.vector_endpoint(
        s1=expected_sma_short,
        s2=expected_sma_long,
        base_series=base_df["open"],
        cross_type=expected_cross_type,
        upper_bound=None,
        lower_bound=None,
        upper_standard=None,
        lower_standard=None,
        name="cross_val",
    )["cross_val"]
    expected_ema_fast = EMACalc.vector_endpoint(
        base_series=base_df["close"],
        window=2,
        smoothing=2,
        name="ema_fast",
    )["ema_fast"]
    expected_ema_slow = EMACalc.vector_endpoint(
        base_series=base_df["close"],
        window=3,
        smoothing=2,
        name="ema_slow",
    )["ema_slow"]
    expected_macd = MACDCalc.vector_endpoint(
        fast_ema=expected_ema_fast,
        slow_ema=expected_ema_slow,
        signal=2,
        name="macd",
    )

    pdt.assert_series_equal(res["sma_short"], expected_sma_short, check_names=False)
    pdt.assert_series_equal(res["sma_long"], expected_sma_long, check_names=False)
    pdt.assert_series_equal(res["prev_sma_short"], expected_prev_sma_short, check_names=False)
    pdt.assert_series_equal(res["prev_sma_long"], expected_prev_sma_long, check_names=False)
    pdt.assert_series_equal(res["cross_type"], expected_cross_type, check_names=False)
    pdt.assert_series_equal(res["cross_val"], expected_cross_val, check_names=False)
    pdt.assert_series_equal(res["ema_fast"], expected_ema_fast, check_names=False)
    pdt.assert_series_equal(res["ema_slow"], expected_ema_slow, check_names=False)
    pdt.assert_series_equal(res["macd"], expected_macd["macd"], check_names=False)
    pdt.assert_series_equal(res["macd_signal"], expected_macd["macd_signal"], check_names=False)
    pdt.assert_series_equal(res["macd_hist"], expected_macd["macd_hist"], check_names=False)
