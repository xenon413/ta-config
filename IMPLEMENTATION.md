# Implementation record

All five action-plan phases are implemented in this working tree. PLAN.md is retained
unchanged as the original audit. This is version 0.2.0 (unreleased).

## Phase 1: chainable streaming and numerical correctness

Complete raw events and labels are persisted. Append and update are explicit and atomic;
updates replay from the checkpoint before the latest bar. SMA removes the actual outgoing
sample, windows include the current sample, shifts use the declared lag, and all mapped
dependencies are evaluated at the current timestamp. Warm-up/missing outputs are NaN and
readiness is exposed separately.

## Phase 2: formula and execution contracts

Cross equality semantics are shared; ambiguous crosses remain type 2 with unavailable price.
Trend confirmation requires exactly the configured current-inclusive run. TrendVal's lower
boundary and the mapped prev_sma calculation are corrected. Equal SMA windows retain a
well-formed result. Vector indexes, output columns, scalar keys and numeric validity are
checked at execution boundaries. Independent examples and differential tests cover all
indicators and their compatibility handlers.

## Phase 3: semantic compiler

Config items and maps are immutable. Input-reference metadata is explicit, implementation
metadata is registry-owned/ClassVar, and parameters are strict, finite and bounded.
Compilation aggregates graph errors, detects global task/output collisions and unresolved
inputs, and uses iterative topological sorting. A compiled plan can be reused across readers.
Graph/state budgets and index/frame checks reject malformed inputs before numerical work.

## Phase 4: bounded state engine

One public implementation exists per indicator; the 1,720-line duplicate facade is removed.
The registry supplies typed state factories and generated reference/schema metadata.
EMA/MACD use accumulators, shifts use bounded queues, extrema use monotonic queues, and
trend confirmation uses scalar run counters. Snapshots are independent optional retention.

The engine intentionally uses bounded transactional copies for rollback. Whole-engine
cost is O(tasks + configured lookback), independent of elapsed history; it is not advertised
as universally O(1). Single-writer ordering, overlapping-call rejection and optional strict
event sequences are documented. DataFrame and direct handler compatibility adapters replay
history and have no latency guarantee. The original chunk/vector crossover research TODO
in core_logic.py is preserved.

## Phase 5: public API and release checks

README examples use Config/ExecutionPlan and execute in tests and against the installed wheel.
All concrete config types and RelativePosition are exported, py.typed is shipped, and the
include_orign deprecation alias remains. Documentation specifies numerical, missing-data,
ordering, failure and compatibility contracts. Logging avoids argument/data formatting.
Contributor dependencies and build tools are pinned to tested versions.

CI covers Windows/Linux and Python 3.12/3.13/3.14 with Ruff, mypy, unit/differential/property
tests, coverage, fixture hashes, build/install/example smoke tests and a dependency audit.
Source archives include tests and fixtures. Fixture text hashes normalize CRLF to LF.

## Verification and limits

Local interpreter: Windows, Python 3.12.10. The sandbox cannot access its Microsoft Store
base interpreter; checks run outside the sandbox with user authorization.

Final code verification passed 75 tests at 98.10% statement/branch coverage,
Ruff, formatting, mypy, wheel/sdist build and clean-wheel README/import/typing-marker checks.
Dependency auditing found no known vulnerabilities in auditable dependencies; the local,
unpublished ta-config package itself is not present on PyPI and is skipped by pip-audit.
Three pandas/NumPy timedelta deprecation warnings remain in a timestamp test; there are no test failures.

Representative benchmark: scripts/benchmark.py runs four indicators for 2,000 events per
symbol in two consecutive blocks, with snapshot retention disabled. On the local machine,
the initial measurements were:

| Engines | Lookback | First block, us/event | Later block, us/event |
| --- | ---: | ---: | ---: |
| 1 | 16 | 355 | 279 |
| 1 | 128 | 539 | 587 |
| 8 | 16 | 321 | 382 |
| 8 | 128 | 832 | 784 |

These are observations under local load, not deployment guarantees. Memory remains bounded
and timings reflect configured lookback rather than ever-growing history. The CI matrix
has been added but Linux and Python 3.13/3.14 have not been executed on this workstation.
No release has been published.
