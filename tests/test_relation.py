import pytest
import pandas as pd
import numpy as np
import pandas.testing as pdt

from ta_config.core.indicators import (
    CrossType,
    CrossVal,
    TrendType,
    TrendVal,
    WindowMax,
    WindowMin,
    Shift,
)


@pytest.mark.unit
def test_cross_type_mock():
    """Mock test for CrossType (vector and stream endpoints)."""
    s1 = pd.Series([1.0, 2.0, 1.0, 3.0])
    s2 = pd.Series([2.0, 1.0, 2.0, 1.0])
    prev_s1 = pd.Series([0.5, 1.5, 1.5, 2.5])
    prev_s2 = pd.Series([1.5, 1.0, 1.0, 2.0])
    upper_bound = pd.Series([1.2, 2.2, 1.0, 3.2])
    lower_bound = pd.Series([0.8, 1.8, 0.8, 2.8])
    upper_standard = pd.Series([1.8, 1.8, 1.8, 1.8])
    lower_standard = pd.Series([1.2, 1.2, 1.2, 1.2])

    res_vec = CrossType.vector_endpoint(
        s1=s1,
        s2=s2,
        prev_s1=prev_s1,
        prev_s2=prev_s2,
        upper_bound=upper_bound,
        lower_bound=lower_bound,
        upper_standard=upper_standard,
        lower_standard=lower_standard,
        name="test_cross_type",
    )

    expected = pd.Series([1, -1, 1, -1], name="test_cross_type", dtype="int64")
    pdt.assert_series_equal(res_vec["test_cross_type"], expected)

    res_stream = CrossType.stream_endpoint(
        cur_s1=1.0,
        cur_s2=2.0,
        prev_s1=0.5,
        prev_s2=1.5,
        cur_upper_bound=1.2,
        cur_upper_standard=1.8,
        cur_lower_bound=0.8,
        cur_lower_standard=1.2,
        name="test_cross_type",
    )
    assert res_stream["test_cross_type"] == 1


@pytest.mark.unit
def test_cross_val_mock():
    """Mock test for CrossVal (vector and stream endpoints)."""
    s1 = pd.Series([1.0, 2.0, 1.0, 3.0])
    s2 = pd.Series([2.0, 1.0, 2.0, 1.0])
    base_series = pd.Series([10.0, 20.0, 30.0, 40.0])
    cross_type = pd.Series([1, -1, 1, -1])
    upper_bound = pd.Series([1.2, 2.2, 1.0, 3.2])
    lower_bound = pd.Series([0.8, 1.8, 0.8, 2.8])
    upper_standard = pd.Series([1.8, 1.8, 1.8, 1.8])
    lower_standard = pd.Series([1.2, 1.2, 1.2, 1.2])

    res_vec = CrossVal.vector_endpoint(
        s1=s1,
        s2=s2,
        base_series=base_series,
        cross_type=cross_type,
        upper_bound=upper_bound,
        lower_bound=lower_bound,
        upper_standard=upper_standard,
        lower_standard=lower_standard,
        name="test_cross_val",
    )

    expected = pd.Series([1.8, 1.2, 1.8, 1.2], name="test_cross_val")
    pdt.assert_series_equal(res_vec["test_cross_val"], expected)

    res_stream = CrossVal.stream_endpoint(
        cur_s1=1.0,
        cur_s2=2.0,
        cur_base=10.0,
        cur_cross_type=1,
        cur_upper_bound=1.2,
        cur_lower_bound=0.8,
        cur_upper_standard=1.8,
        cur_lower_standard=1.2,
        name="test_cross_val",
    )
    assert res_stream["test_cross_val"] == 1.8


@pytest.mark.unit
def test_trend_type_mock():
    """Mock test for TrendType (vector, tail, and stream endpoints)."""
    prev_base_series = pd.Series([10.0, 10.0, 10.0, 10.0])
    upper_bound = pd.Series([11.0, 10.0, 9.0, 12.0])
    lower_bound = pd.Series([9.0, 9.5, 8.5, 11.0])
    thresh = 0.05
    trend_len = 3

    res_vec = TrendType.vector_endpoint(
        prev_base_series=prev_base_series,
        upper_bound=upper_bound,
        lower_bound=lower_bound,
        thresh=thresh,
        trend_len=trend_len,
        name="test_trend_type",
    )

    expected = pd.Series([0, 0, 0, 0], name="test_trend_type")
    pdt.assert_series_equal(res_vec["test_trend_type"], expected)

    res_tail = TrendType.tail(
        prev_base_series=prev_base_series,
        upper_bound=upper_bound,
        lower_bound=lower_bound,
        thresh=thresh,
        trend_len=trend_len,
        name="test_trend_type",
    )
    assert res_tail["test_trend_type"] == 0

    res_stream = TrendType.stream_endpoint(
        prev_base_series=prev_base_series,
        upper_bound=upper_bound,
        lower_bound=lower_bound,
        thresh=thresh,
        trend_len=trend_len,
        name="test_trend_type",
    )
    assert res_stream["test_trend_type"] == 0


@pytest.mark.unit
def test_trend_val_mock():
    """Mock test for TrendVal (vector and stream endpoints)."""
    base_series = pd.Series([10.0, 10.0, 10.0, 10.0])
    upper_bound = pd.Series([11.0, 10.0, 9.0, 12.0])
    lower_bound = pd.Series([9.0, 9.5, 8.5, 11.0])
    upper_standard = pd.Series([10.5, 10.5, 10.5, 10.5])
    lower_standard = pd.Series([9.5, 9.5, 9.5, 9.5])
    trend_type = pd.Series([1, -1, 0, 1])

    res_vec = TrendVal.vector_endpoint(
        base_series=base_series,
        upper_bound=upper_bound,
        lower_bound=lower_bound,
        upper_standard=upper_standard,
        lower_standard=lower_standard,
        trend_type=trend_type,
        name="test_trend_val",
    )

    expected = pd.Series([10.5, 9.5, 0.0, 10.5], name="test_trend_val")
    pdt.assert_series_equal(res_vec["test_trend_val"], expected)

    res_stream = TrendVal.stream_endpoint(
        cur_upper_bound=11.0,
        cur_lower_bound=9.0,
        cur_upper_standard=10.5,
        cur_lower_standard=9.5,
        cur_trend_type=1,
        cur_base=10.0,
        name="test_trend_val",
    )
    assert res_stream["test_trend_val"] == 10.5


@pytest.mark.unit
def test_window_max_mock():
    """Mock test for WindowMax (vector, tail, and stream endpoints)."""
    base = pd.Series([1.0, 3.0, 2.0, 5.0, 4.0])
    window = 3

    res_vec = WindowMax.vector_endpoint(base_series=base, window=window, name="test_win_max")
    expected = pd.Series([np.nan, np.nan, 3.0, 5.0, 5.0], name="test_win_max")
    pdt.assert_series_equal(res_vec["test_win_max"], expected)

    res_tail = WindowMax.tail(base_series=base, window=window, name="test_win_max")
    assert res_tail["test_win_max"] == 5.0

    res_stream = WindowMax.stream_endpoint(base_series=base, window=window, name="test_win_max")
    assert res_stream["test_win_max"] == 5.0


@pytest.mark.unit
def test_window_min_mock():
    """Mock test for WindowMin (vector, tail, and stream endpoints)."""
    base = pd.Series([1.0, 3.0, 2.0, 5.0, 4.0])
    window = 3

    res_vec = WindowMin.vector_endpoint(base_series=base, window=window, name="test_win_min")
    expected = pd.Series([np.nan, np.nan, 1.0, 2.0, 2.0], name="test_win_min")
    pdt.assert_series_equal(res_vec["test_win_min"], expected)

    res_tail = WindowMin.tail(base_series=base, window=window, name="test_win_min")
    assert res_tail["test_win_min"] == 2.0

    res_stream = WindowMin.stream_endpoint(base_series=base, window=window, name="test_win_min")
    assert res_stream["test_win_min"] == 2.0


@pytest.mark.unit
def test_shift_mock():
    """Mock test for Shift (vector, tail, and stream endpoints)."""
    base = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
    period = 2

    res_vec = Shift.vector_endpoint(base_series=base, period=period, name="test_shift")
    expected = pd.Series([np.nan, np.nan, 10.0, 20.0, 30.0], name="test_shift")
    pdt.assert_series_equal(res_vec["test_shift"], expected)

    res_tail = Shift.tail(base_series=base, period=period, name="test_shift")
    assert res_tail["test_shift"] == 20.0

    res_stream = Shift.stream_endpoint(base_series=base, period=period, name="test_shift")
    assert res_stream["test_shift"] == 20.0
