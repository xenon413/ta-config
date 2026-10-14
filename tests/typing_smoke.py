"""A downstream consumer checked by mypy (not a runtime pytest test)."""

from typing import assert_type

import pandas as pd

from ta_config import Config, ExecutionPlan, IndexConfig, SMACalcConfig, StepResult, StreamEngine

config = IndexConfig(sma_calc={"s": SMACalcConfig(base="x", window=2)})
plan = Config.compile(config, ["x"])
assert_type(plan, ExecutionPlan)
frame = plan.vector(pd.DataFrame({"x": [1.0]}))
assert_type(frame, pd.DataFrame)
event = StreamEngine(plan).step({"x": 1.0}, index=0)
assert_type(event, StepResult)
assert_type(event.outputs["s"], float)
