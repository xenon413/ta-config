import pytest
import pandas as pd
import numpy as np
import pandas.testing as pdt

from ta_config.core.indicators import EMACalc

@pytest.mark.unit
def test_ema_calc_mock():
    """Mock test for EMACalc (vector and stream endpoints)"""
    base = pd.Series([10.0, 20.0, 30.0])
    window = 3
    smoothing = 2.0
    
    # 1. vector_endpoint
    # alpha = smoothing / (1 + window) = 2.0 / (1 + 3) = 0.5
    # Pandas ewm(alpha=0.5, adjust=False) computes:
    # y_0 = x_0 = 10.0
    # y_1 = (1 - alpha) * y_0 + alpha * x_1 = 0.5 * 10.0 + 0.5 * 20.0 = 15.0
    # y_2 = 0.5 * y_1 + alpha * x_2 = 0.5 * 15.0 + 0.5 * 30.0 = 22.5
    expected = pd.Series([10.0, 15.0, 22.5], name="test_ema")
    
    res_vec = EMACalc.vector_endpoint(base_series=base, window=window, smoothing=smoothing, name="test_ema")
    pdt.assert_series_equal(res_vec["test_ema"], expected)
    
    # 2. stream_endpoint
    # Testing the O(1) step: cur_base = 30.0, prev_ema = 15.0
    # Expected alpha = 0.5, so 30.0 * 0.5 + 15.0 * 0.5 = 22.5
    res_stream = EMACalc.stream_endpoint(
        prev_ema=15.0, 
        cur_base=30.0, 
        window=window, 
        smoothing=smoothing, 
        name="test_ema"
    )
    
    assert res_stream["test_ema"] == 22.5
