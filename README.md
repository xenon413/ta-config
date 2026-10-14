# ta-config

Declarative technical indicators with strict configuration, an immutable execution plan,
and bounded streaming state. This is an in-process numerical library; it has no service endpoints.

## Install

Python 3.12-3.14 is the supported CI matrix. Runtime dependencies are pandas 2.3,
NumPy 2.x, and Pydantic 2.x within the ranges in pyproject.toml.

Build and install an immutable wheel from a reviewed commit:

```sh
python -m pip install build
python -m build
python -m pip install dist/ta_config-0.2.0-py3-none-any.whl
```

Version 0.2.0 is the version in this source tree; these instructions do not imply
that a release tag has already been published. Record the wheel SHA-256 for deployment.
After publishing, use a fixed release tag or commit rather than a mutable branch.

## Quick start

```python
import pandas as pd
from ta_config import Config, IndexConfig, StreamEngine

config = IndexConfig.model_validate(
    {
        "sma_calc": {"sma": {"base": "close", "window": 3}},
        "ema_calc": {"ema": {"base": "close", "window": 3}},
        "shift": {"previous": {"base": "close", "period": 1}},
    }
)
prices = pd.DataFrame({"close": [10.0, 20.0, 30.0]})
plan = Config.compile(config, prices.columns)
history = plan.vector(prices)
assert history["sma"].iloc[-1] == 20.0

engine = StreamEngine.from_frame(plan, prices, snapshot_size=100)
event = engine.step({"close": 40.0}, index=3, sequence=4)
assert event.outputs["sma"] == 30.0
assert event.ready["sma"]
# Replace the current bar using its full raw event. Repeated updates do not double-count.
event = engine.step({"close": 50.0}, index=3, mode="update", sequence=5)
assert event.outputs["sma"] == 100.0 / 3.0
snapshot = engine.snapshot()  # Retained raw inputs AND calculated outputs.
```

Compile once per raw schema and share the immutable plan across readers.
Each symbol/timeframe needs its own StreamEngine. Sequence counts include updates.

## JSON configuration

```python
from ta_config import IndexConfig

text = '{"sma_calc": {"sma": {"base": "close", "window": 3}}}'
config = IndexConfig.model_validate_json(text)
assert IndexConfig.model_validate_json(config.model_dump_json()) == config
# For a file: IndexConfig.model_validate_json(Path("strategy.json").read_text())
```

Use Config.vector_config(config, frame, include_original=False) for a one-off
historical calculation. The old include_orign spelling warns with DeprecationWarning;
passing both spellings is an error. IndexConfig is a data model, not an executor.

## Event and data contract

- Every event supplies exactly the complete raw schema; generated outputs cannot be supplied.
  Numeric real inputs are required. Booleans, strings, complex values, and infinity are rejected.
- Indexes are unique, increasing integer, string, or pandas Timestamp labels.
  Append requires a strictly newer comparable label. Duplicate appends are rejected.
  Updates require the latest existing label; historical corrections require replay.
- Sequence is optional; when supplied it must be the next integer, starting at 1.
  There is no automatic deduplication or retry acceptance.
- A failed step leaves state, sequence, and snapshots unchanged.
  A StreamEngine has one ordered writer. Overlapping steps raise ExecutionError;
  callers must order events externally. Independent engines may run concurrently.
- NaN represents unavailable input/output. Rolling mean/min/max require a complete valid
  window and recover after missing samples leave it. Shift uses NaN until history exists;
  period zero returns the current sample.
- EMA seeds from the first valid sample. Missing inputs emit NaN and leave its accumulator
  unchanged; the next valid sample resumes it (pandas adjust=False, ignore_na=True, with
  missing positions masked). MACD applies the same rule to its signal EMA.
- Relation signals propagate missing inputs. StepResult.ready reports availability for each
  output separately; zero is a valid no-signal/equal/flat result, never a warm-up substitute.
- Windows, signal periods and trend lengths are positive integers up to 100,000.
  Shifts are nonnegative. EMA alpha = smoothing/(window+1) must be in (0,1].
  Default smoothing is 2; explicit zero is invalid.
- Config maps, config items, plans and returned event mappings are immutable. The compiler
  aggregates graph diagnostics before calculation, including unresolved input references,
  task/output collisions, input shadowing and cycles. Runtime result-contract failures
  include task, mode, and (in streaming) index context.
- Limits: 4,096 tasks and 1,000,000 configured state samples; snapshot_size is 0-100,000.
  Memory remains bounded by configured state and retained snapshot size. Set snapshot_size=0
  for no frame retention; archive emitted values externally if a full history is needed.

## Formula and signal definitions

| Indicator | Definition / boundary |
| --- | --- |
| SMACalc | Arithmetic mean of the last window samples, including current. Scalar prev_base is the outgoing x[t-window]. |
| EMACalc | alpha*x + (1-alpha)*previous EMA, seeded from first valid x. |
| MACDCalc | fast EMA - slow EMA; outputs name, name_signal, name_hist. |
| SMA2SMACrossStandard | base + w1*w2*(sma2-sma1)/(w2-w1). Equal windows return base in the same output shape. |
| SMATrendMaintVal | base + window*(mapped prev_sma - sma). The mapped value is read at the current bar. |
| SMAadjust | base + (adjustment-base)/window. |
| CrossType | Golden: prev_s1<=prev_s2 and upper_bound>=upper_standard. Death: prev_s1>=prev_s2 and lower_bound<=lower_standard. Golden=1, death=-1, both=2, neither=0. |
| CrossVal | Golden/death use the corresponding standard, or base when the full range has passed it. CrossType=2 emits NaN because intrabar ordering is unknown. |
| TrendType | Short when lower<previous base (takes precedence); otherwise long when upper>=previous base; flat when either relative distance is below threshold. Requires trend_len consecutive valid directions; only an identical signed run is confirmed. Zero base emits NaN. |
| TrendVal | Uses upper/lower standard or base if the full range passed it; emits zero when the requested boundary was not reached. |
| WindowMax / WindowMin | Current-inclusive full rolling window extrema. |
| Shift | Value from period bars ago. |
| RelativePosition | sign(s1-s2); equal=0, missing=NaN. |

The optional cross bounds default to s1/s2; upper standard defaults to s2 and lower
standard to s1. Prev references are explicit mapped Series at the current timestamp:
use Shift in your graph when you need the previous bar.

## Compatibility adapters and performance

Config.stream_rotate appends a full raw row; Config.stream_update replaces the
latest full raw row. Both return a complete reusable DataFrame and leave the input untouched.
Append requires index= for a non-RangeIndex; a RangeIndex can infer its next label.
Update preserves the latest index if index= is omitted. No placeholder row is required.
These adapters recompute the historical frame, so cost grows with history.

Direct stream_handler adapters accept history excluding the current event and replay
that indicator's vector calculation. Direct tail and Series-based stream_endpoint
methods instead receive a Series including the current bar. Use StreamEngine for
bounded live processing, not these convenience adapters.

The engine does no DataFrame construction on its step path. Rolling extrema use monotonic
queues, and EMA, scalar relations and trend confirmation retain constant scalar state.
Atomic transitions copy bounded indicator state, so the complete engine step costs
O(tasks + configured lookback), independent of elapsed stream length. There is no
blanket O(1), microsecond, or production latency guarantee. Snapshot construction costs
O(retained rows * columns) and is optional. Run scripts/benchmark.py for reproducible
single/multiple-engine measurements; measure your actual configuration before deployment.

## Development and verification

```sh
python -m pip install -c constraints-dev.txt -e ".[test]"
python -m pytest --cov=ta_config --cov-report=term-missing
python -m ruff check .
python -m mypy
python -m build
python scripts/wheel_smoke.py dist/ta_config-0.2.0-py3-none-any.whl
python -m pip_audit
python scripts/benchmark.py
```

The constraints file records the tested contributor environment. CI tests Windows and
Linux on Python 3.12/3.13/3.14, builds and installs a wheel in a clean venv, executes
README examples away from the source tree, verifies CSV/archive fixture hashes,
checks lint/types/coverage, and audits dependencies. Formula tests use independent
examples; differential/property tests cover all handlers, missing data and generated graphs.

Version 0.2 intentionally changes incorrect 0.1 streaming, warm-up and boundary behavior.
The misspelled keyword remains through the 0.2 series; removal requires a later documented
release. Direct imports from ta_config, ta_config.core, and implementation modules refer
to the same indicator classes. All concrete config models and RelativePosition are public.
See [CHANGELOG.md](CHANGELOG.md) and [IMPLEMENTATION.md](IMPLEMENTATION.md) for validation details.
Generated [registry reference](docs/api.md) and [JSON schema](docs/config.schema.json) describe the supported configuration surface.

## License

MIT. See LICENSE.
