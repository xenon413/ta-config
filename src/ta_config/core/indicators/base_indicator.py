from abc import ABC, abstractmethod
import pandas as pd

class BaseIndicator(ABC):
    """
    Abstract Base Class for low-latency quantitative technical indicators.

    This interface enforces a unified two-tiered execution layout (Vector and 
    Stream endpoints) to seamlessly handle both high-throughput historical 
    backtesting and microsecond-level live streaming execution loops.

    Design Philosophy:
    ------------------
    1. Stateful Accumulators (e.g., SMA, EMA):
       Require different implementations for historical setup (Vector) 
       vs. live streaming (Stream) to utilize fast O(1) recursive shortcuts.
    2. Stateless Transformers (e.g., CrossType, SMACrossStandard):
       Evaluate point-in-time relationships between existing metrics. The 
       Stream endpoint for these indicators naturally uses the same O(1) 
       execution path.

    Methods:
    --------
    vector_endpoint(*args, **kwargs):
        Processes static historical matrices (typically pandas Series or DataFrames).
        Optimized for vectorized math operations during backtesting.
        Complexity: O(N) or O(N * W).

    stream_endpoint(*args, **kwargs):
        Evaluates a single incoming real-time market tick or bar update.
        Must be hard-optimized to eliminate loops, slice operations, or lookbacks.
        Complexity: Strictly O(1).

    stream_handler(*args, **kwargs):
        Unified middleman method that prepares data for stream_endpoint.
        Produces a dictionary that can be directly passed to stream_endpoint.
    """
    name = "indicator"
    # (prefix, suffix)
    output_key_parts = (
        ("", ""),
    )

    @classmethod
    def output_keys(cls, name:str)->tuple[str, ...]:
        return tuple(f"{prefix}{name}{suffix}" for prefix, suffix in cls.output_key_parts)

    @classmethod
    @abstractmethod
    def vector_endpoint(cls, *args, **kwargs)->pd.DataFrame:
        """Execute historical vectorized matrix calculations."""
        pass

    @classmethod
    @abstractmethod
    def stream_endpoint(cls, *args, **kwargs)->dict[str, int|float]:
        """Compute the next step metric using low-latency O(1) recursive or scalar math."""
        pass

    @classmethod
    @abstractmethod
    def stream_handler(cls, prev_df, cur_row)->dict[str, int|float]:
        """
        Unified middleman method owned by each class.
        Produces a dictionary that can be directly passed to stream_endpoint.
        """
        pass
