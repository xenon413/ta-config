from decimal import Decimal, ROUND_HALF_UP
import numpy as np
import pandas as pd
from typing import Callable, TypeVar, Any
from functools import wraps
import time
import logging
F = TypeVar("F", bound=Callable[..., Any])

# not complete 
class PrecisionAdapter:
    @staticmethod
    def get_decimal_place(d:Decimal)->int:
        exponent = d.as_tuple().exponent
        return abs(exponent) if isinstance(exponent, int) and exponent < 0 else 0
    
    @staticmethod
    def float_to_decimal(val:float, decimal_place:int)->Decimal:
        d = Decimal(str(val))
        return d.quantize("0."+"0"*decimal_place, rounding=ROUND_HALF_UP)

def log_lifecycle(logger: logging.Logger) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            logger.debug(f"enter {func.__name__} | Args: {args}")
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.info(f"EXCEPTION in {func.__name__}: {str(e)}")
                raise
            finally:
                end_time = time.perf_counter()
                logger.debug(f"exit {func.__name__} (duration: {end_time-start_time})")
        return wrapper
    return decorator