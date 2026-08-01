import pytest
import pandas as pd
import numpy as np
import pandas.testing as pdt

from ta_config.core.indicators import (
    SMACalc,
    SMAadjust,
    SMATrendMaintVal,
    SMA2SMACrossStandard
)

@pytest.mark.unit
def test_sma_calc_with_csv(sample_df, warm_up_df):
    """Verify SMACalc against the precalculated sma_25 and sma_320 for 2026-06-13."""
    combined_df = pd.concat([warm_up_df, sample_df], ignore_index=True)

    # Calculate using the full warm-up + target-day history so the rolling
    # windows are initialized from prior data, then only compare the target day.
    res_25 = SMACalc.vector_endpoint(base_series=combined_df["close"], window=25, name="my_sma25")
    res_320 = SMACalc.vector_endpoint(base_series=combined_df["close"], window=320, name="my_sma320")
    
    # In the CSV, sma25 and sma320 are likely rounded to 1 decimal place.
    # Compare our results with the CSV
    target_slice = slice(len(warm_up_df), len(warm_up_df) + len(sample_df))
    calc_sma25 = res_25["my_sma25"].iloc[target_slice].reset_index(drop=True).round(1)
    calc_sma320 = res_320["my_sma320"].iloc[target_slice].reset_index(drop=True).round(1)
    expected_sma25 = sample_df["sma_25"]
    expected_sma320 = sample_df["sma_320"]

    # Rolling mean has NaN for the first `window-1` rows, filter them out before comparing
    mask_25 = calc_sma25.notna()
    pdt.assert_series_equal(
        calc_sma25[mask_25],
        expected_sma25[mask_25],
        check_names=False,
        # check_exact=True
    )

    mask_320 = calc_sma320.notna()
    pdt.assert_series_equal(
        calc_sma320[mask_320],
        expected_sma320[mask_320],
        check_names=False,
        # check_exact=True
    )

@pytest.mark.unit
def test_sma_calc_mock():
    """Mock test for SMACalc (all endpoints)"""
    base = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
    window = 3
    
    # 1. vector_endpoint
    expected = pd.Series([np.nan, np.nan, 20.0, 30.0, 40.0], name="test_sma")
    res_vec = SMACalc.vector_endpoint(base_series=base, window=window, name="test_sma")
    pdt.assert_series_equal(res_vec["test_sma"], expected)
    
    # 2. stream_endpoint
    # prev_sma = 20.0, prev_base = 30.0, cur_base = 40.0, window = 3
    # expect 20.0 + (40.0 - 30.0)/3 = 23.333...
    res_stream = SMACalc.stream_endpoint(prev_sma=20.0, prev_base=30.0, cur_base=40.0, window=window, name="test_sma")
    assert np.isclose(res_stream["test_sma"], 20.0 + 10.0/3)
    
    # 3. tail
    res_tail = SMACalc.tail(base_series=base, window=window, name="test_sma")
    # tail of [10.0, 20.0, 30.0, 40.0, 50.0] with window 3 is mean([30, 40, 50]) = 40.0
    assert res_tail["test_sma"] == 40.0

@pytest.mark.unit
def test_sma_adjust_mock():
    """Mock test for SMAadjust (all endpoints)"""
    base = pd.Series([10.0, 20.0, 30.0, 40.0])
    adj = pd.Series([12.0, 18.0, 30.0, 36.0])
    window = 2
    
    # 1. vector_endpoint
    expected = pd.Series([11.0, 19.0, 30.0, 38.0], name="test_adj")
    res_vec = SMAadjust.vector_endpoint(base_series=base, adj_series=adj, window=window, name="test_adj")
    pdt.assert_series_equal(res_vec["test_adj"], expected)
    
    # 2. stream_endpoint
    # cur_base = 40.0, cur_adj = 36.0, window = 2
    # expected 40.0 + (36.0 - 40.0)/2 = 38.0
    res_stream = SMAadjust.stream_endpoint(cur_base=40.0, cur_adj=36.0, window=window, name="test_adj")
    assert res_stream["test_adj"] == 38.0

@pytest.mark.unit
def test_sma_trend_maint_val_mock():
    """Mock test for SMATrendMaintVal (all endpoints)"""
    base = pd.Series([10.0, 12.0, 14.0])
    sma = pd.Series([5.0, 6.0, 7.0])
    prev_sma = pd.Series([4.0, 5.0, 8.0])
    window = 3
    
    # 1. vector_endpoint
    expected = pd.Series([7.0, 9.0, 17.0], name="test_trend")
    res_vec = SMATrendMaintVal.vector_endpoint(base_series=base, sma=sma, prev_sma=prev_sma, window=window, name="test_trend")
    pdt.assert_series_equal(res_vec["test_trend"], expected)
    
    # 2. stream_endpoint
    # cur_base=14.0, cur_sma=7.0, prev_sma=8.0, window=3
    # expect 14.0 + 3*(8.0 - 7.0) = 17.0
    res_stream = SMATrendMaintVal.stream_endpoint(cur_base=14.0, cur_sma=7.0, prev_sma=8.0, window=window, name="test_trend")
    assert res_stream["test_trend"] == 17.0

@pytest.mark.unit
def test_sma2sma_cross_standard_mock():
    """Mock test for SMA2SMACrossStandard (all endpoints)"""
    base = pd.Series([100.0, 105.0])
    sma1 = pd.Series([10.0, 12.0])
    sma2 = pd.Series([15.0, 10.0])
    window1 = 2
    window2 = 4
    
    # 1. vector_endpoint
    expected = pd.Series([120.0, 97.0], name="test_cross")
    res_vec = SMA2SMACrossStandard.vector_endpoint(base_series=base, sma1=sma1, window1=window1, sma2=sma2, window2=window2, name="test_cross")
    pdt.assert_series_equal(res_vec["test_cross"], expected)
    
    # 2. stream_endpoint
    # cur_base=105.0, cur_sma1=12.0, window1=2, cur_sma2=10.0, window2=4
    # expected 105.0 - 8.0 = 97.0
    res_stream = SMA2SMACrossStandard.stream_endpoint(cur_base=105.0, cur_sma1=12.0, window1=window1, cur_sma2=10.0, window2=window2, name="test_cross")
    assert res_stream["test_cross"] == 97.0
