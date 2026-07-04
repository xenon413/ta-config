import pytest
import pandas as pd
import numpy as np
import pandas.testing as pdt

from ta_config.core.indicators import EMACalc, MACDCalc

@pytest.mark.unit
def test_macd_calc_mock():
    """Mock test for MACDCalc (vector and stream endpoints)."""
    fast_ema = pd.Series([12.0, 13.0, 14.0, 15.0], name="fast_ema")
    slow_ema = pd.Series([10.0, 11.0, 12.0, 13.0], name="slow_ema")
    signal = 3
    name = "test_macd"

    res_vec = MACDCalc.vector_endpoint(
        fast_ema=fast_ema,
        slow_ema=slow_ema,
        signal=signal,
        name=name,
    )

    expected_macd = pd.Series([2.0, 2.0, 2.0, 2.0], name=name)
    expected_signal = EMACalc.vector_endpoint(
        base_series=expected_macd,
        window=signal,
        smoothing=2,
        name=f"{name}_signal",
    )[f"{name}_signal"]
    expected_hist = expected_macd - expected_signal

    pdt.assert_series_equal(res_vec[name], expected_macd)
    pdt.assert_series_equal(res_vec[f"{name}_signal"], expected_signal)
    pdt.assert_series_equal(res_vec[f"{name}_hist"], expected_hist)

    res_stream = MACDCalc.stream_endpoint(
        cur_fast_ema=15.0,
        cur_slow_ema=13.0,
        signal=signal,
        prev_signal_line=2.0,
        name=name,
    )

    expected_cur_macd = 2.0
    expected_cur_signal = EMACalc.stream_endpoint(
        prev_ema=2.0,
        cur_base=expected_cur_macd,
        window=signal,
        smoothing=2,
        name="ema",
    )["ema"]
    expected_cur_hist = expected_cur_macd - expected_cur_signal

    assert np.isclose(res_stream[name], expected_cur_macd)
    assert np.isclose(res_stream[f"{name}_signal"], expected_cur_signal)
    assert np.isclose(res_stream[f"{name}_hist"], expected_cur_hist)
