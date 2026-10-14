# `ta-config` Critical Code Review and Architectural Audit

Audit date: 2026-09-30  
Scope: the current `ta-config` working tree, including source, tests, packaging, and documentation.

## Audit basis and risk summary

This is a source-level audit, not a feature overview. The most serious conclusion is that vectorized and streaming execution are not equivalent. Several live calculations are mathematically wrong or one bar stale, and the stream executor does not persist the supplied raw event into the returned DataFrame. A pipeline can therefore look correct in a backtest, emit different live signals, and corrupt the state used by the next event. The current streaming API should not be trusted for trading decisions until the P0 items in the action plan are complete.

The existing test suite could not be executed in this environment. `.venv\Scripts\python.exe` points to a removed Microsoft Store Python interpreter, and no other Python executable is available on `PATH`. The command attempted was `.venv\Scripts\python.exe -m pytest -p no:cacheprovider`; it failed before pytest started. This is an environment limitation, not evidence that the tests fail. The defects below are supported by deterministic code paths and, where useful, concrete examples.

Severity used below:

- **Critical:** can silently produce or retain wrong trading data in ordinary use.
- **High:** can corrupt results, make valid-looking configurations behave ambiguously, or break a supported execution path.
- **Medium:** material maintainability, operability, compatibility, or production-hardening gap.
- **Low:** localized debt with limited immediate impact.

## 1. Architectural Weaknesses & Anti-Patterns

### A1. Critical — streaming is not modeled as a valid, atomic state transition

`Config.stream_update` separates `prev_df` from `row`, calculates with a temporary `cur_row`, and writes only calculated indicator outputs back to the last DataFrame row (`src/ta_config/core/core_logic.py:83-105`). It never copies the raw event fields into that row. `Config.stream_rotate` appends an all-`None` row and has the same defect (`src/ta_config/core/core_logic.py:110-133`). Consequently:

- `stream_update` silently assumes the caller already appended a placeholder row, but that contract is neither named nor validated. If a normal history frame is passed, the last real bar is excluded from history and overwritten.
- `stream_rotate` returns a new row whose OHLC/input fields remain `None`, even though its indicators were computed from the supplied `row` dictionary.
- Feeding either returned frame into the next call uses stale, zero, or `None` raw history. The API is therefore not safely chainable.
- `cur_df.loc[len(df)] = None` is label-based (`core_logic.py:113`). With index `[1, 2]`, `len(df) == 2`, so it overwrites label `2` rather than appending. With a `DatetimeIndex`, it inserts an integer label and destroys index consistency. There is no way to supply the new event's timestamp.

The two methods also expose ambiguous concepts: “update the current bar” and “close/append a new bar” require different event-time and state semantics, but both accept the same untyped `row: dict` and a full DataFrame.

**Required direction:** define an explicit atomic transition such as `step(state, event_with_index, mode) -> (new_state, outputs)`. Validate update-versus-append behavior, persist the complete raw event before dependent calculations, require or preserve a unique monotonic index, and make returned state immediately reusable.

### A2. High — the claimed low-latency/O(1) architecture is O(history size) per event

The public positioning promises low-latency O(1) streaming (`README.md:5-16`, `pyproject.toml:8`, and `src/ta_config/core/indicators/base_indicator.py:29-32`), but the pipeline does the following on every event:

- Copies the full DataFrame in `stream_update` and twice in `stream_rotate` (`core_logic.py:84`, `core_logic.py:111-112`).
- Rebuilds and topologically sorts the graph on every call (`core_logic.py:88`, `core_logic.py:116`).
- Passes full historical Series and DataFrames through every handler (`core_logic.py:95-101`, `core_logic.py:123-129`).
- Retains unbounded history.
- Scans tails for `TrendType`, `WindowMax`, and `WindowMin`; their source contains explicit O(1) TODOs (`src/ta_config/core/indicators/relation.py:251-300`, `relation.py:414-432`, `relation.py:464-482`).
- Decorates every primitive endpoint with logging, adding call overhead to the advertised hot path.

Each event is at least O(rows × columns), and processing an ever-growing history is cumulatively O(N²). This will become a monolithic bottleneck under multiple symbols/timeframes.

**Required direction:** compile an immutable execution plan once, maintain a bounded typed state per indicator, use ring buffers/deques or monotonic queues for rolling extrema, and keep DataFrame snapshot generation outside the hot path. Until that exists, narrow the O(1) claims to the individual scalar formulas that actually meet them.

### A3. High — dependency resolution uses an unsafe global string namespace

The planner flattens all indicator categories into `tasks[field_name]` and all generated columns into `task_by_output[out_key]` (`core_logic.py:8-24`). Assignments overwrite prior entries without detecting collisions. Raw columns, task IDs, and generated outputs are indistinguishable strings. This permits several ambiguous configurations:

- An SMA and EMA with the same task name silently leave only the later task.
- A task named `foo_signal` can collide with the generated signal output of MACD task `foo`.
- An output can shadow an input DataFrame column. Later tasks read the generated value from `available_cols`, while the final concatenated frame can contain duplicate column labels.
- An unknown dependency is treated as a raw leaf (`core_logic.py:36-42`) and fails later with an uncontextualized `KeyError`, rather than at config compilation.
- DFS is recursive (`core_logic.py:31-49`), so a sufficiently deep valid graph can hit Python's recursion limit. The cycle error reports only one node, not the full cycle.

**Required direction:** introduce a compilation phase with explicit source references, globally unique node/output identifiers, validation against the input schema, collision detection, and iterative topological sorting. Compilation should return all diagnostics together before any calculation begins.

### A4. High — the indicator abstraction does not enforce the executor's contract

`BaseIndicator` declares `*args, **kwargs` and broad return types (`src/ta_config/core/indicators/base_indicator.py:44-67`). `Config` then dynamically combines Pydantic dumps, Series lookups, names, and stream state before calling an implementation (`core_logic.py:62-72`, `core_logic.py:92-101`). Neither static typing nor runtime validation checks that an indicator:

- accepts the configured inputs;
- returns a DataFrame with the same index in vector mode;
- returns a dictionary with exactly its declared keys in stream mode; or
- produces numeric values and consistent vector/stream semantics.

Existing code already violates those assumptions: equal-window `SMA2SMACrossStandard` returns a Series/scalar, and short-length `TrendType` returns incompatible types (details in section 2).

The implementation is also split across two class hierarchies. Real calculations live in `sma.py`, `ema.py`, `macd.py`, and `relation.py`, while `core/indicators/__init__.py` is a 1,720-line subclass façade that repeats nearly every signature and docstring just to add defaults and output naming. Some base handlers call lexical `__class__.stream_endpoint` rather than `cls.stream_endpoint` (for example `sma.py:45-60`, `ema.py:43-59`, and `macd.py:46-66`), bypassing consumer overrides and making import-path behavior and subclassing unreliable.

Adding one indicator requires synchronized edits to its implementation, façade, schema/config hierarchy, `IndexConfig`, and two export modules. This is tight coupling and a clear open/closed violation.

**Required direction:** use one public implementation per indicator behind a typed `IndicatorSpec`/protocol that declares config, input references, output keys, vector contract, and stream-state type. Register specs in one place and generate schema/export/documentation metadata from that registry. Validate every implementation result at the executor boundary.

### A5. Medium — apparent immutability and concurrency safety are misleading

`IndexConfig` is declared frozen, but its fields are mutable dictionaries containing mutable `BaseConfig` models (`src/ta_config/core/schema.py:25-34`, `schema.py:231-250`). A caller can mutate a task map or calculation parameter after validation; assignment validation is not enabled. One thread can mutate configuration while another is iterating it, and repeated calls can see different plans.

The executor is stateless, but recursive indicators require strictly ordered events. Concurrent calls made from the same prior DataFrame calculate competing snapshots; accepting one result loses the other event. No sequence number, timestamp monotonicity, idempotency rule, lock, or single-writer contract exists.

**Required direction:** normalize validated config to deeply immutable structures, compile it once, and explicitly choose one concurrency model: either a single-writer `StreamEngine` with sequence checks/locking, or a documented caller-owned synchronization contract. Reject duplicate/out-of-order events unless a deliberate bar-update policy handles them.

### A6. Medium — the public API and typing surface are internally inconsistent

- README advertises and calls `IndexConfig.vector_config(...)` (`README.md:15`, `README.md:57-74`), but `IndexConfig` has no execution method. The implementation is `Config.vector_config(index_config, df)` (`core_logic.py:53-80`), so the quick start raises `AttributeError`.
- The public keyword `include_orign` is misspelled (`core_logic.py:54`). Correcting it without a compatibility shim would itself be a breaking change.
- `RelativePosition` is implemented, available in the schema, and exported by the indicator façade, but omitted from `src/ta_config/core/__init__.py:1-35` and `src/ta_config/__init__.py:1-35`.
- Most concrete config types are not exposed through a documented public import surface.
- The package contains inline annotations but no `py.typed` marker, so installed-package type checkers cannot reliably consume them as PEP 561 package typing.
- Important types remain imprecise (`row: dict`, broad scalar unions, and variadic abstract methods).
- `requires-python = ">=3.12.10"` (`pyproject.toml:12`) excludes Python 3.12.0-3.12.9 even though the visible syntax appears compatible with earlier 3.12 patch releases and likely Python 3.10+. The actual supported minimum has not been tested or justified.

**Required direction:** choose one coherent executor API, publish and test the supported imports, add a deprecated alias for `include_orign` while introducing `include_original`, ship `py.typed`, and enforce the claimed Python/type surface in CI.

## 2. Silent Errors, Edge Cases & Bug Risks

### B1. Critical — streaming SMA removes the previous sample, not the outgoing window sample

The correct rolling recurrence is:

`SMA[t] = SMA[t-1] + (x[t] - x[t-window]) / window`

`SMACalc.stream_handler` passes `base_series.iloc[-1]` as `prev_base` (`src/ta_config/core/indicators/sma.py:53-60`). That is the immediately previous value, not the value leaving the rolling window. For history `[10, 20, 30]`, window `3`, prior SMA `20`, and current value `40`, the code returns `20 + (40 - 30) / 3 = 23.33`; the correct SMA of `[20, 30, 40]` is `30`.

This is silent numerical corruption and propagates into every downstream dependency. Worse, the current unit test explicitly blesses the incorrect result (`tests/test_sma.py:59-63`), and the core stream expectation invokes the same faulty endpoint (`tests/test_core.py:127-141`).

**Fix:** use the actual outgoing observation (`base_series.iloc[-window]` when history excludes the current value), define warm-up behavior, and periodically or deliberately rebase if floating-point recurrence drift matters.

### B2. Critical — multiple stream handlers calculate the wrong bar

The executor gives handlers Series from `prev_df` and the new value separately in `cur_row` (`core_logic.py:95-101`, `core_logic.py:123-129`), but several handlers ignore `cur_row`:

- `WindowMax` and `WindowMin` calculate only over old history (`relation.py:436-449`, `relation.py:486-499`). With history `[1, 5, 2]`, current `10`, and window `3`, streaming max returns `5` instead of `10`.
- `Shift.tail` uses `base_series.iloc[-(period + 1)]` (`relation.py:514-520`) as though the Series already contains the current sample. Under `Config`, it contains only prior samples. A period-1 shift returns `t-2` instead of `t-1`; period 0 returns the previous value instead of the current value.
- `TrendType.stream_handler` ignores `cur_row` entirely (`relation.py:304-323`), so the live trend is based on old bounds/base data.

The direct endpoint tests hide this mismatch by passing a Series that already includes the “current” value (`tests/test_relation.py:177-225`).

**Fix:** establish one history convention for every handler and enforce it. For a previous-history convention, incorporate the appropriate current scalar for rolling calculations; for shift period `p > 0`, read prior history at `iloc[-p]`, and use the current scalar for period `0`.

### B3. High — vector calculations lose the caller's index and corrupt alignment

`CrossVal.vector_endpoint` and `TrendVal.vector_endpoint` construct new Series from NumPy arrays without specifying an index (`relation.py:136-147`, `relation.py:338-350`). Pandas assigns a new `RangeIndex`. When the source frame has a `DatetimeIndex` or any custom index, `Config.vector_config` concatenates by label (`core_logic.py:72-80`), producing extra rows and `NaN`-filled misalignment. Downstream indicators can then consume shifted/corrupted series.

**Fix:** preserve a canonical input index on every result and validate that all input Series have identical, unique indexes. The executor should reject an indicator result whose index differs from the source index.

### B4. High — vector and stream formulas disagree

There are several confirmed parity defects:

- `TrendVal` checks `lower_bound > lower_bound` in vector mode (`relation.py:342`), a condition that cannot be true. Stream mode checks `cur_lower_bound > cur_lower_standard` and emits zero (`relation.py:367-368`). Short-trend results therefore differ between backtest and live execution.
- `CrossType` requires `prev_s1 > prev_s2` for a vectorized death cross but `prev_s1 >= prev_s2` in streaming (`relation.py:43-44`, `relation.py:73-74`). Equality can generate different signals, including a live “both crossed” value.
- `TrendType` vector mode confirms a run through rolling/shift logic (`relation.py:234-247`), while `tail` checks only `trend_len - 1` observations (`relation.py:279-285`) and the stream handler omits the current bar. This is off by at least one relative to the vector contract.
- `SMATrendMaintVal.stream_handler` accepts a configured `prev_sma` dependency but ignores it and uses `sma.iloc[-1]` (`src/ta_config/core/indicators/sma.py:150-167`). Vector mode uses the mapped `prev_sma` Series (`sma.py:126-134`), so a valid nonstandard mapping diverges.

**Fix:** specify the boundary semantics once and derive vector and stream behavior from a shared transition where practical. Add differential/property tests that compare vector recomputation with every streamed step.

### B5. High — valid schema values trigger return-type violations and executor crashes

- When the two SMA windows are equal, `SMA2SMACrossStandard.vector_endpoint` returns a bare Series and its stream endpoint returns a bare scalar (`sma.py:74-98`). The executor expects `.columns` in vector mode (`core_logic.py:75`) and a mapping for `cur_row.update` in stream mode (`core_logic.py:102`). Equality is currently permitted by the schema.
- When `trend_len <= 2`, `TrendType.vector_endpoint` returns a Series rather than a DataFrame (`relation.py:231-232`). `TrendType.tail` calls `trend.iloc(-1)` and adds a trailing comma (`relation.py:276-277`), yielding an exception/incompatible tuple rather than the promised dictionary.
- Empty or short histories reach `.iloc[-1]`/window-relative indexing throughout SMA, EMA, MACD, Shift, and Trend handlers without guards.
- Stream methods require every output column to exist before assignment (`core_logic.py:104`, `core_logic.py:132`) but provide no initializer or preflight explaining that requirement.

**Fix:** reject mathematically undefined parameter combinations or return the declared type on every branch; validate minimum state before execution; and add central result-contract checks with the task/output name in the error.

### B6. High — warm-up, `NaN`, and non-finite values can silently become permanent or valid-looking signals

- Recursive SMA/EMA/MACD use the last accumulator without checking whether it is initialized (`sma.py:54`, `ema.py:53`, `macd.py:61`). A `NaN` prior SMA remains `NaN` even when enough observations have arrived unless a cold-start fallback recalculates it.
- `CrossType` comparisons involving missing values become false and are converted to zero/no-cross (`relation.py:43-54`).
- `RelativePosition` treats both comparisons with `NaN` as false, returning `0`, which is indistinguishable from genuine equality (`relation.py:558-572`).
- `TrendType` divides by `prev_base_series` without a zero policy (`relation.py:220-229`, `relation.py:265-274`). Zero can yield infinity/`NaN` and then an apparently flat result.

For trading logic, “unavailable,” “equal,” “flat,” and “no signal” must not be conflated accidentally.

**Fix:** define a package-wide warm-up and missing-data policy. Either preserve nullable results until state is valid, explicitly reseed accumulators, or fail fast according to configurable policy. Validate finiteness where required and expose readiness separately from signal value.

### B7. Medium — multi-cross events are detected and then silently erased

`CrossType` deliberately emits `2` when both golden and death-cross conditions occur in one bar (`relation.py:47-52`, `relation.py:76-81`). `CrossVal` handles only `1` and `-1` and maps every other value to `0` (`relation.py:139-147`, `relation.py:173-177`). A recognized ambiguous/multiple-cross event therefore becomes indistinguishable from no cross.

**Fix:** define a structured result for multi-cross ordering/prices, preserve an explicit ambiguous/unknown value, or reject the unsupported case. Do not silently turn a detected event into zero.

### B8. Medium — exception handling rethrows without useful domain context

There are no swallowed broad exceptions, which is positive, but the only generic wrapper logs exceptions at `INFO` with `str(e)` and no traceback (`src/ta_config/core/helper.py:22-35`). Low-level `KeyError`, `IndexError`, pandas errors, and divide-by-zero errors reach users without the configured task, input reference, output, row index, or execution mode. Because validation happens during execution, diagnosing a large graph is unnecessarily difficult.

**Fix:** perform preflight validation, introduce contextual library exceptions, and chain original exceptions. Log unexpected failures with traceback at an appropriate level while keeping full frame values out of logs.

## 3. Missing Features, Components & Security Best Practices

### C1. High — configuration validation is syntactic, not semantic

`extra="forbid"` is a useful baseline (`schema.py:25-29`, `schema.py:231-235`), but every numeric parameter is otherwise an unconstrained `int` or `float` (`schema.py:52-224`). Current models allow:

- zero/negative SMA, EMA, MACD, and rolling windows;
- negative/future-looking shifts (look-ahead leakage in a trading system);
- `NaN`/infinite thresholds and smoothing values;
- EMA smoothing that produces alpha outside `(0, 1]`;
- empty column/output names;
- booleans or strings coerced into numeric fields by non-strict validation;
- equal SMA-cross windows even though the special branch violates contracts.

Vector mode may reject some values inside pandas while stream mode performs nonsensical arithmetic. In addition, the public façade uses `smoothing = smoothing or 2` (`src/ta_config/core/indicators/__init__.py:503`, `indicators/__init__.py:535`, `indicators/__init__.py:570`), silently changing an explicitly supplied zero into the default.

`indicator_class` is modeled as a user-settable Pydantic field (`schema.py:31-34`) even though it is executable implementation metadata. It is not directly injectable through ordinary JSON as a class object, but in Python it lets callers replace the declared implementation and defeats a trustworthy registry boundary.

**Required controls:** strict constrained fields, finite-number enforcement, cross-field invariants, nonempty identifiers, an explicit policy for shift `0`, and `ClassVar`/registry-owned implementation metadata. Add a DataFrame/row preflight for required unique columns, numeric types, input indexes, readiness/history length, and output-state columns.

### C2. High — tests are self-referential and omit failure-path coverage

The suite mainly verifies happy paths:

- There are no `pytest.raises` tests for invalid parameters, missing dependencies, cycles, collisions, short history, or malformed frames.
- `tests/test_core.py:53-112` and `tests/test_core.py:127-194` build expected values by calling the same production endpoints used by the executor. Shared formula defects therefore pass.
- `tests/test_sma.py:59-63` explicitly asserts the faulty SMA recurrence.
- Stream tests cover one event, not a returned-state chain, so they do not detect missing raw-row persistence.
- Relation tests call endpoints directly rather than exercising their `stream_handler` through `Config`, masking the previous-history/current-value mismatch.
- Tests use only default `RangeIndex`, unique column names, finite values, and adequate positive windows.
- Several configured indicator families never participate in an end-to-end dependency graph test.
- CSV fixture paths use CWD-dependent Windows strings (`tests/conftest.py:4-10`), which is fragile from a parent directory and non-portable to Linux.

**Required test strategy:**

1. Build independent golden examples rather than deriving expectations from implementation methods.
2. For every indicator, stream a long sequence one event at a time and assert at every step that the result equals a fresh vector recomputation, including warm-up and missing-data behavior.
3. Add property-based coverage for boundary equality, arbitrary indexes, `NaN`/infinity policy, random valid graphs, and numerical drift over thousands of events.
4. Exercise every handler through the real compiled executor, including multiple consecutive updates/appends.
5. Add negative tests for all validation rules, name/output collisions, unresolved inputs, duplicate DataFrame labels, cycles, empty/short frames, out-of-order timestamps, and return-contract violations.

### C3. Medium — logging creates confidentiality/performance risk without adequate observability

`log_lifecycle` eagerly formats positional arguments in an f-string even when debug logging is disabled (`helper.py:22-35`). Public endpoints can be called positionally with whole Series/DataFrames, causing expensive stringification and potentially logging proprietary strategy/market data. At the same time, failure logs omit traceback and task context.

**Required controls:** lazy structured logging, `logger.isEnabledFor` guards for expensive metadata, shapes/names rather than data values, `exc_info=True` for unexpected failures, and pipeline-level task/output/index context. Expose optional metrics/hooks rather than configuring application logging from the library.

### C4. Medium — CI, build, type, dependency, and release controls are absent

The tracked repository has no CI workflow, formatter/linter config, static type check, coverage threshold, dependency audit, compatibility matrix, or clean wheel/sdist installation test. Specific risks include:

- `pythonpath = ["src"]` lets tests import the source tree directly and can miss packaging defects (`pyproject.toml:28-34`).
- Runtime/build dependencies have only lower bounds and contributor environments have no constraints/lock file, so future incompatible releases can enter untested (`pyproject.toml:1-3`, `pyproject.toml:13-23`). `pytest-mock` is declared but unused.
- There is no `py.typed` marker or downstream typing smoke test.
- README recommends installing mutable `main` (`README.md:24-38`) rather than a tagged/released artifact or pinned commit.
- The checksum helper covers only one raw ZIP, prints a mismatch, and still exits successfully; it is not run by pytest and does not validate the CSV fixtures actually consumed (`tests/data/binance_kline/raw/checksum_validate.py:3-42`).

**Required controls:** Windows/Linux CI across the supported Python range; Ruff or equivalent linting; a type checker with pandas typing; coverage gates; build, install, import, and README-example smoke tests against the wheel; dependency auditing; reproducible contributor/release constraints; and release-tag installation instructions. Either integrate deterministic fixture integrity checks that fail the build or remove unused raw archives/tooling.

### C5. Medium — production behavior and public compatibility are undocumented

The README does not define:

- how to initialize streaming state;
- the distinction between bar update and bar append;
- required output columns/history depth;
- timestamp/order requirements;
- warm-up and missing-value semantics;
- behavior on duplicate input/output names;
- numerical definitions and boundary semantics for each signal;
- thread-safety and event-order responsibility;
- a working JSON loading example despite claiming JSON reuse.

The quick start itself is broken as described in A6. The derivation referenced from an implementation comment (`sma.py:78`) lives only in repository-root `equation.pdf`/`equation.md`, not necessarily in an installed package's accessible documentation.

**Required controls:** make executable documentation part of CI, publish a versioned API/behavior contract, state compatibility/deprecation policy, and document every state/readiness/error invariant before presenting the package as production-ready.

### C6. Security scope assessment

No hardcoded credentials, unsafe deserialization, network client, authentication surface, or service endpoint was found. Authentication, authorization, and rate limiting are therefore not applicable inside this in-process numerical library. The relevant security concerns are:

- malformed or adversarial configurations causing resource exhaustion or incorrect trading behavior;
- full-frame copying/unbounded history and recursive graph traversal as denial-of-service vectors when inputs are externally supplied;
- sensitive values leaking through lifecycle logs;
- mutable-branch installation and unreproducible dependency/build resolution;
- executable implementation metadata being accepted as a Pydantic instance field in Python.

These should be handled through bounded semantic validation, compiled resource limits, safe logging, immutable registries, and reproducible release practices rather than web-service controls.

## 4. Prioritized Action Plan

### 1. P0 — stop live/backtest divergence and make streaming state chainable

**Scope:** `core_logic.py`, `sma.py`, `relation.py`, and stream tests.

- First add independent failing regression tests for the SMA `[10, 20, 30] -> 40` case, current-bar window extrema, shift periods 0/1/N, TrendType current-bar behavior, multiple consecutive stream events, and non-Range indexes.
- Replace the two ambiguous stream paths with explicitly specified update-current-bar and append-closed-bar transitions, or one method with an enum whose semantics are validated.
- Persist the full event and index atomically; never append with `.loc[len(df)]`.
- Fix SMA's outgoing sample and all handlers that omit/misplace the current value.
- Define cold-start/readiness and missing-data behavior.

**Done when:** for every supported indicator and a long multi-event sequence, each streamed result and returned full state match independent vector recomputation at the same timestamp, and the returned state can be fed directly into the next call.

### 2. P0 — repair vector/stream formula, index, and return-contract defects

**Scope:** all indicator implementations and the executor boundary.

- Fix the `TrendVal` self-comparison, CrossType equality rule, TrendType confirmation/off-by-one logic, and ignored `prev_sma` mapping.
- Preserve source indexes in every vector result.
- Decide whether equal SMA windows are invalid; otherwise return the required DataFrame/dict shapes.
- Make every branch, including `trend_len <= 2`, honor declared output keys and types.
- Give multi-cross events an explicit nonzero/structured meaning.
- Add central executor assertions for output keys, DataFrame length/index, duplicate columns, and scalar validity.

**Done when:** parity/property tests cover all boundary branches and no indicator can return a shape, index, key set, or type that violates the executor contract.

### 3. P1 — add a semantic compiler and strict validation layer

**Scope:** `schema.py` and a new planning/validation component.

- Replace MRO-derived column mapping (`schema.py:41-43`) with explicit typed input-reference metadata.
- Enforce positive/finite parameter constraints and cross-field invariants without truthiness-based defaults.
- Compile one immutable execution plan; reject duplicate task/output names, input/output shadowing, unresolved references, duplicate DataFrame labels, invalid cycles, and unsupported state before execution.
- Return aggregated, contextual diagnostics with task, field, reference, and expected contract.
- Bound graph size/history/resource use if configs can come from external users.

**Done when:** every malformed config/frame identified in C1/C2 fails before calculation with a deterministic domain error, while the plan is safe to cache and share across readers.

### 4. P1 — replace the façade/full-DataFrame hot path with a typed state engine

**Scope:** indicator API, registry, compiled plan, and streaming storage.

- Collapse the duplicate public/internal class hierarchies into one implementation/spec per indicator.
- Replace variadic abstract methods with typed protocols and explicit per-indicator state.
- Cache the compiled topological order and maintain only bounded lookback/accumulator state; implement monotonic queues for min/max where O(1) is claimed.
- Separate hot-path scalar outputs from optional DataFrame snapshots.
- Specify single-writer/thread-safety, sequence, duplicate, and out-of-order-event behavior.
- Benchmark representative symbol/timeframe counts before restoring broad performance claims.

**Done when:** per-event cost is independent of retained history for indicators advertised as O(1), memory is bounded by configured lookback/state, and benchmark/complexity claims are reproducible.

### 5. P1 — harden the public API and release pipeline

**Scope:** README, exports, packaging, logging, and CI.

- Correct and execute-test the README API; document streaming initialization, warm-up, index/order, missing-data, errors, and JSON loading.
- Introduce `include_original` with a deprecation path for `include_orign`; make exports including `RelativePosition` coherent.
- Add `py.typed`, precise public types, a supported-Python/dependency matrix, and clean built-wheel tests.
- Add cross-platform CI with lint, type, unit/property/integration tests, coverage gates, dependency audit, README smoke tests, and fixture-integrity handling.
- Replace eager/data-bearing lifecycle logs with safe structured context.
- Point production installation guidance at immutable releases/tags rather than `main`.

**Done when:** a fresh environment can build and install the artifact, run documented examples and the full verification matrix, consume its type information, and reproduce the tested dependency set without relying on the source checkout.

## Release recommendation

Treat the current package as experimental and do not deploy its streaming outputs into live trading or compare them directly with vectorized backtests until priorities 1 and 2 are complete. Priorities 3-5 are required before describing the library as production-ready or low-latency.
