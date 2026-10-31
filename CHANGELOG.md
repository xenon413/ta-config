# Changelog

## 0.2.1 — unreleased

- Add `rsi_calc`, `RSICalc`, and `RSICalcConfig` with Wilder smoothing, a simple-average
  seed, and constant-size streaming state supporting repeated current-candle updates.
- Define flat RSI as 50 and reset RSI warm-up after missing samples.
- Extend the public registry reference and configuration JSON schema for RSI.

## 0.2.0 — unreleased

- Correct current-bar streaming, SMA outgoing observations, shifted references, trend
  confirmation, TrendVal boundaries, output shapes and index preservation.
- Add strict immutable config, aggregated semantic compilation and bounded atomic StreamEngine.
- Define complete event persistence, append/update ordering, sequence checks, readiness,
  missing-data recovery and explicit ambiguous-cross output.
- Consolidate indicator implementations and expose all indicators/config models with py.typed.
- Add include_original while deprecating include_orign.
- Add independent regressions, generated-graph/property and long-run parity tests,
  fixture integrity, executable examples, wheel smoke checks, CI and dependency constraints.

Compatibility: update replaces the last actual bar; append needs an explicit label for
non-RangeIndex inputs. Warm-up and missing relation outputs are NaN. CrossType equality
can produce 2 (both crosses), and CrossVal then produces NaN. TrendType confirms exactly
trend_len current-inclusive directions. EMA resumes its valid accumulator after missing inputs.
