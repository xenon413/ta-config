import numpy as np
import pandas as pd
from hypothesis import given, settings
from hypothesis import strategies as st

from ta_config import Config, IndexConfig, StreamEngine


@settings(max_examples=40, deadline=None)
@given(
    st.lists(
        st.one_of(
            st.floats(-10000, 10000, allow_nan=False, allow_infinity=False), st.just(float("nan"))
        ),
        min_size=1,
        max_size=50,
    ),
    st.integers(1, 12),
    st.integers(0, 12),
    st.integers(-10000, 10000),
)
def test_random_windows_missing_samples_and_indexes(values, window, period, start):
    cfg = IndexConfig.model_validate(
        {
            "sma_calc": {"s": {"base": "x", "window": window}},
            "window_max": {"hi": {"base": "x", "window": window}},
            "window_min": {"lo": {"base": "x", "window": window}},
            "ema_calc": {"e": {"base": "x", "window": window}},
            "shift": {"previous": {"base": "x", "period": period}},
        }
    )
    raw = pd.DataFrame({"x": values}, index=pd.RangeIndex(start, start + len(values)))
    plan = Config.compile(cfg, raw.columns)
    engine = StreamEngine(plan, snapshot_size=0)
    expected = plan.vector(raw, include_original=False)
    for i, value in enumerate(values):
        actual = engine.step({"x": value}, index=start + i)
        np.testing.assert_allclose(
            list(actual.outputs.values()), expected.iloc[i], equal_nan=True, rtol=1e-10, atol=1e-10
        )
