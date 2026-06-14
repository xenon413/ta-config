from abc import ABC, abstractmethod

class BaseIndicator(ABC):
    """
    Abstract Base Class for low-latency quantitative technical indicators.

    This interface enforces a unified three-tiered execution layout (Vector, 
    Anchor, and Stream endpoints) to seamlessly handle both high-throughput 
    historical backtesting and microsecond-level live streaming execution loops.

    Design Philosophy:
    ------------------
    1. Stateful Accumulators (e.g., SMA, EMA):
       Require different implementations for historical setup (Vector/Anchor) 
       vs. live streaming (Stream) to utilize fast O(1) recursive shortcuts.
    2. Stateless Transformers (e.g., CrossType, SMACrossStandard):
       Evaluate point-in-time relationships between existing metrics. The 
       Anchor and Stream endpoints for these indicators naturally share the 
       same O(1) execution path.

    Methods:
    --------
    vector_endpoint(*args, **kwargs):
        Processes static historical matrices (typically pandas Series or DataFrames).
        Optimized for vectorized math operations during backtesting.
        Complexity: O(N) or O(N * W).

    anchor_endpoint(*args, **kwargs):
        Establishes the initial state or bootstrap value of an indicator 
        at system startup using a trailing snapshot of history. Connects the 
        historical backtest state to the live streaming loop.
        Complexity: O(W) for stateful accumulators, O(1) for stateless relations.

    stream_endpoint(*args, **kwargs):
        Evaluates a single incoming real-time market tick or bar update.
        Must be hard-optimized to eliminate loops, slice operations, or lookbacks.
        Complexity: Strictly O(1).
    """

    @staticmethod
    @abstractmethod
    def vector_endpoint(*args, **kwargs):
        """Execute historical vectorized matrix calculations."""
        pass

    @staticmethod
    @abstractmethod
    def anchor_endpoint(*args, **kwargs):
        """Calculate the bootstrap state at system startup or engine reset."""
        pass

    @staticmethod
    @abstractmethod
    def stream_endpoint(*args, **kwargs):
        """Compute the next step metric using low-latency O(1) recursive or scalar math."""
        pass