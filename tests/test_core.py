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
    res = index_config.vector_config(base_df)

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


def _expected_stream_result(prev_df:pd.DataFrame, row:dict[str, float])->pd.Series:
    expected_sma_short = SMACalc.stream_endpoint(
        prev_sma=prev_df["sma_short"].iloc[-1],
        prev_base=prev_df["close"].iloc[-1],
        cur_base=row["close"],
        window=2,
        name="sma_short",
    )["sma_short"]
    expected_sma_long = SMACalc.stream_endpoint(
        prev_sma=prev_df["sma_long"].iloc[-1],
        prev_base=prev_df["close"].iloc[-1],
        cur_base=row["close"],
        window=3,
        name="sma_long",
    )["sma_long"]
    expected_prev_sma_short = Shift.stream_endpoint(
        base_series=prev_df["sma_short"],
        period=1,
        name="prev_sma_short",
    )["prev_sma_short"]
    expected_prev_sma_long = Shift.stream_endpoint(
        base_series=prev_df["sma_long"],
        period=1,
        name="prev_sma_long",
    )["prev_sma_long"]
    expected_cross_type = CrossType.stream_endpoint(
        cur_s1=expected_sma_short,
        cur_s2=expected_sma_long,
        prev_s1=expected_prev_sma_short,
        prev_s2=expected_prev_sma_long,
        cur_upper_bound=None,
        cur_upper_standard=None,
        cur_lower_bound=None,
        cur_lower_standard=None,
        name="cross_type",
    )["cross_type"]
    expected_cross_val = CrossVal.stream_endpoint(
        cur_s1=expected_sma_short,
        cur_s2=expected_sma_long,
        cur_base=row["open"],
        cur_cross_type=expected_cross_type,
        cur_upper_bound=None,
        cur_lower_bound=None,
        cur_upper_standard=None,
        cur_lower_standard=None,
        name="cross_val",
    )["cross_val"]
    expected_ema_fast = EMACalc.stream_endpoint(
        prev_ema=prev_df["ema_fast"].iloc[-1],
        cur_base=row["close"],
        window=2,
        smoothing=2,
        name="ema_fast",
    )["ema_fast"]
    expected_ema_slow = EMACalc.stream_endpoint(
        prev_ema=prev_df["ema_slow"].iloc[-1],
        cur_base=row["close"],
        window=3,
        smoothing=2,
        name="ema_slow",
    )["ema_slow"]
    expected_macd = MACDCalc.stream_endpoint(
        cur_fast_ema=expected_ema_fast,
        cur_slow_ema=expected_ema_slow,
        signal=2,
        prev_signal_line=prev_df["macd_signal"].iloc[-1],
        name="macd"
    )

    return pd.Series(
        {
            "sma_short": expected_sma_short,
            "sma_long": expected_sma_long,
            "prev_sma_short": expected_prev_sma_short,
            "prev_sma_long": expected_prev_sma_long,
            "cross_type": expected_cross_type,
            "cross_val": expected_cross_val,
            "ema_fast": expected_ema_fast,
            "ema_slow": expected_ema_slow,
            "macd": expected_macd["macd"],
            "macd_signal": expected_macd["macd_signal"],
            "macd_hist": expected_macd["macd_hist"],
        }
    )


@pytest.mark.unit
def test_stream_update_with_dependency_chain(index_config:IndexConfig):
    history_df = pd.DataFrame(
        {
            "open": [10.0, 11.0],
            "high": [11.0, 12.0],
            "low": [9.0, 10.0],
            "close": [10.0, 12.0],
            "sma_short": [10.0, 11.0],
            "sma_long": [10.0, 11.0],
            "prev_sma_short": [10.0, 10.0],
            "prev_sma_long": [10.0, 10.0],
            "cross_type": [0, 0],
            "cross_val": [0.0, 0.0],
            "ema_fast": [10.0, 11.0],
            "ema_slow": [10.0, 11.0],
            "macd": [0.0, 0.0],
            "macd_signal": [0.0, 0.0],
            "macd_hist": [0.0, 0.0],
        }
    )
    update_df = history_df.copy()
    update_df.loc[len(update_df)] = 0.0
    row = {
        "open": 13.0,
        "high": 14.0,
        "low": 12.0,
        "close": 14.0,
    }

    res = index_config.stream_update(update_df, row)
    expected = _expected_stream_result(update_df.iloc[:-1], row)

    result = res.iloc[-1][expected.index]
    pdt.assert_series_equal(result, expected, check_names=False)


@pytest.mark.unit
def test_stream_rotate_with_dependency_chain(index_config:IndexConfig):
    history_df = pd.DataFrame(
        {
            "open": [10.0, 11.0],
            "high": [11.0, 12.0],
            "low": [9.0, 10.0],
            "close": [10.0, 12.0],
            "sma_short": [10.0, 11.0],
            "sma_long": [10.0, 11.0],
            "prev_sma_short": [10.0, 10.0],
            "prev_sma_long": [10.0, 10.0],
            "cross_type": [0, 0],
            "cross_val": [0.0, 0.0],
            "ema_fast": [10.0, 11.0],
            "ema_slow": [10.0, 11.0],
            "macd": [0.0, 0.0],
            "macd_signal": [0.0, 0.0],
            "macd_hist": [0.0, 0.0],
        }
    )
    row = {
        "open": 13.0,
        "high": 14.0,
        "low": 12.0,
        "close": 14.0,
    }

    res = index_config.stream_rotate(history_df, row)
    expected = _expected_stream_result(history_df, row)

    result = res.iloc[-1][expected.index]
    pdt.assert_series_equal(result, expected, check_names=False)
