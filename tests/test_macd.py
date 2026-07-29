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
    expected_hist = (expected_macd - expected_signal).rename(f"{name}_hist")

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

ATOL = 0.11

@pytest.mark.unit
def test_macd_calc_with_csv(sample_df, warm_up_df):
    """Verify MACDCalc against the precalculated macd for 2026-06-13."""
    combined_df = pd.concat([warm_up_df, sample_df], ignore_index=True)

    res_12 = EMACalc.vector_endpoint(base_series=combined_df["close"], window=12, name="ema_12")
    res_26 = EMACalc.vector_endpoint(base_series=combined_df["close"], window=26, name="ema_26")
    
    res_macd = MACDCalc.vector_endpoint(
        fast_ema=res_12["ema_12"],
        slow_ema=res_26["ema_26"],
        signal=9,
        name="macd_12_26_9"
    )

    target_slice = slice(len(warm_up_df), len(warm_up_df) + len(sample_df))
    
    calc_macd = res_macd["macd_12_26_9"].iloc[target_slice].reset_index(drop=True).round(1)
    calc_signal = res_macd["macd_12_26_9_signal"].iloc[target_slice].reset_index(drop=True).round(1)
    calc_hist = res_macd["macd_12_26_9_hist"].iloc[target_slice].reset_index(drop=True).round(1)
    
    expected_macd = sample_df["macd_12_26_9"]
    expected_signal = sample_df["macd_signal_12_26_9"]
    expected_hist = sample_df["macd_hist_12_26_9"]

    mask = calc_macd.notna()
    pdt.assert_series_equal(calc_macd[mask], expected_macd[mask], check_names=False, atol=ATOL)
    pdt.assert_series_equal(calc_signal[mask], expected_signal[mask], check_names=False, atol=ATOL)
    pdt.assert_series_equal(calc_hist[mask], expected_hist[mask], check_names=False, atol=ATOL)
