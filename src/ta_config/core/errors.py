"""Contextual errors raised at configuration and execution boundaries."""


class ConfigError(ValueError):
    def __init__(self, diagnostics: list[str]):
        self.diagnostics = tuple(diagnostics)
        super().__init__("Invalid pipeline:\n- " + "\n- ".join(diagnostics))


class ExecutionError(ValueError):
    """An input, event, or indicator violated its execution contract."""
