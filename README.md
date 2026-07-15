# ta-config

A Python toolkit for building technical-indicator pipelines from declarative configuration.

`ta-config` focuses on two complementary execution styles:

- Vectorized calculations for historical dataframes
- Streaming-style, low-latency endpoints for online or event-driven use cases

The package is designed around `pandas` and `numpy`, with `pydantic` models that let you describe indicator dependencies in a JSON or Python config and automatically execute them in the correct order.

## Features

- Declarative indicator configuration with dependency tracking
- Vectorized historical computation via `IndexConfig.vector_config(...)`
- Streaming-style O(1) endpoints for selected indicators
- Built-in support for common technical analysis building blocks:
  - SMA and EMA calculations
  - MACD computation
  - Cross-type and cross-value logic
  - Trend state and maintenance-value indicators
  - Window max/min and shift operations

## Installation

Install from GitHub:

```bash
pip install git+https://github.com/xenon413/ta-config.git@main
```

For local development:

```bash
git clone https://github.com/xenon413/ta-config.git
cd ta-config
pip install -e .[test]
```

## Quick start

The simplest way to use the package is to define an indicator pipeline in configuration and run it against a dataframe.

```python
import pandas as pd
from ta_config.core.schema import IndexConfig

price_df = pd.DataFrame(
    {
        "open": [10.0, 11.0, 12.0, 13.0, 14.0],
        "high": [11.0, 12.0, 13.0, 14.0, 15.0],
        "low": [9.0, 10.0, 11.0, 12.0, 13.0],
        "close": [10.0, 12.0, 11.0, 14.0, 13.0],
    }
)

config = IndexConfig.model_validate(
    {
        "sma_calc": {
            "sma_short": {"base": "close", "window": 2},
            "sma_long": {"base": "close", "window": 3},
        },
        "ema_calc": {
            "ema_fast": {"base": "close", "window": 2, "smoothing": 2},
            "ema_slow": {"base": "close", "window": 3, "smoothing": 2},
        },
        "macd_calc": {
            "macd": {"fast_ema": "ema_fast", "slow_ema": "ema_slow", "signal": 2}
        },
    }
)

result = config.vector_config(price_df)
print(result[["close", "sma_short", "sma_long", "ema_fast", "ema_slow", "macd"]].tail())
```

You can also load the configuration from a JSON file and reuse it across datasets.

## Supported indicator building blocks

The package includes ready-to-use implementations for:

- `SMACalc` for simple moving averages
- `EMACalc` for exponential moving averages
- `MACDCalc` for MACD and signal/histogram outputs
- `CrossType` and `CrossVal` for bullish/bearish crossing logic
- `TrendType` and `TrendVal` for trend-state evaluation
- `WindowMax`, `WindowMin`, and `Shift` for rolling-window utilities

## Development and testing

Run the test suite with:

```bash
pytest
```

The repository includes unit tests for vectorized calculations, dependency ordering, and indicator behavior using both mock data and sample market data.

## License

See the repository `LICENSE` file for license details.
