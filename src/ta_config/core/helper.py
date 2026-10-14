import logging
import time
from decimal import ROUND_HALF_UP, Decimal
from functools import wraps
from typing import Any, Callable, TypeVar, cast

F = TypeVar("F", bound=Callable[..., Any])


class PrecisionAdapter:
    @staticmethod
    def get_decimal_place(d: Decimal) -> int:
        exponent = d.as_tuple().exponent
        return abs(exponent) if isinstance(exponent, int) and exponent < 0 else 0

    @staticmethod
    def float_to_decimal(val: float, decimal_place: int) -> Decimal:
        return Decimal(str(val)).quantize(Decimal(1).scaleb(-decimal_place), rounding=ROUND_HALF_UP)


def log_lifecycle(logger: logging.Logger) -> Callable[[F], F]:
    """Opt-in metadata-only diagnostics; arguments and market data are never logged."""

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            debug = logger.isEnabledFor(logging.DEBUG)
            start = time.perf_counter() if debug else 0.0
            if debug:
                logger.debug("enter function=%s", func.__qualname__)
            try:
                return func(*args, **kwargs)
            finally:
                if debug:
                    logger.debug(
                        "exit function=%s duration=%f",
                        func.__qualname__,
                        time.perf_counter() - start,
                    )

        return cast(F, wrapper)

    return decorator
