"""Reproduce bounded-state throughput; no universal latency guarantee is implied."""

import argparse
import json
import platform
from time import perf_counter

from ta_config import Config, IndexConfig, StreamEngine


def benchmark(events: int, symbols: int, window: int) -> dict:
    config = IndexConfig.model_validate(
        {
            "sma_calc": {"s": {"base": "x", "window": window}},
            "ema_calc": {"e": {"base": "x", "window": 12}},
            "window_max": {"hi": {"base": "x", "window": window}},
            "window_min": {"lo": {"base": "x", "window": window}},
        }
    )
    plan = Config.compile(config, ["x"])
    engines = [StreamEngine(plan, snapshot_size=0) for _ in range(symbols)]
    timings = []
    for block in range(2):
        start = perf_counter()
        for i in range(events):
            for engine in engines:
                engine.step({"x": float(i % 101)}, index=block * events + i)
        timings.append((perf_counter() - start) / (events * symbols) * 1e6)
    return {
        "symbols": symbols,
        "window": window,
        "events_per_symbol_per_block": events,
        "microseconds_per_event_first_later": timings,
        "retained_rows": sum(len(engine.snapshot()) for engine in engines),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=int, default=2000)
    args = parser.parse_args()
    print(
        json.dumps(
            {
                "python": platform.python_version(),
                "platform": platform.platform(),
                "cases": [
                    benchmark(args.events, symbols, window)
                    for symbols in (1, 8)
                    for window in (16, 128)
                ],
            },
            indent=2,
        )
    )
