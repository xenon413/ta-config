from pathlib import Path

import pandas as pd
import pytest

DAY_PATH = Path(__file__).parent / "data/binance_kline/btcusdc_1m_future_2026_06_13.csv"
WARM_UP_PATH = Path(__file__).parent / "data/binance_kline/btcusdc_1m_future_2026_06_12_warm_up.csv"


@pytest.fixture(scope="module")
def sample_df():
    """Load the provided sample data for CSV verification"""
    return pd.read_csv(DAY_PATH)


@pytest.fixture(scope="module")
def warm_up_df():
    """Load the warm-up data used to seed rolling indicators."""
    return pd.read_csv(WARM_UP_PATH)
