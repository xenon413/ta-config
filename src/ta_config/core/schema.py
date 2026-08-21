from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from typing import Type
from functools import cached_property
import pandas as pd

from .indicators import(
    SMACalc, 
    SMA2SMACrossStandard,
    SMATrendMaintVal,
    SMAadjust,
    EMACalc,
    MACDCalc,
    CrossType,
    CrossVal,
    TrendType,
    TrendVal,
    WindowMax,
    WindowMin,
    Shift,
    RelativePosition,
)
from .indicators.base_indicator import BaseIndicator

class BaseConfig(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    indicator_class:Type[BaseIndicator] = Field(
        default=BaseIndicator,
        exclude=True
    )

    # @abstractmethod
    # def generate(self)->tuple[str, ...]:
    #     """returns the field name that returns after executing"""
    #     pass
        
    def column_mapping(self) -> dict[str, str]:
        column_class = next(c for c in self.__class__.__mro__ if BaseConfig in c.__bases__)
        return self.model_dump(include=set(column_class.model_fields.keys()), exclude_none=True)

# NOTE: use inherit to have the column mapping,
# the base class contains the field that are column names
# and the child have the field that are pure value
# by doing so the child could access column_mapping function that only contain the fields -> field name

# add alias if perfer other name
# ---- sma ----
class _SMACalcColumn(BaseConfig):
    base_series:str = Field(alias="base")
    
class SMACalcConfig(_SMACalcColumn):
    window:int

    indicator_class:Type[BaseIndicator] = Field(
        default=SMACalc,
        exclude=True
    )

class _SMA2SMACrossStandardColumn(BaseConfig):
    base_series:str = Field(alias="base")
    sma1:str
    sma2:str
    
class SMA2SMACrossStandardConfig(_SMA2SMACrossStandardColumn):
    window1:int
    window2:int

    indicator_class:Type[BaseIndicator] = Field(
        default=SMA2SMACrossStandard,
        exclude=True
    )

class _SMATrendMaintValColumn(BaseConfig):
    base_series:str = Field(alias="base")
    sma:str
    prev_sma:str

class SMATrendMaintValConfig(_SMATrendMaintValColumn):
    window:int

    indicator_class:Type[BaseIndicator] = Field(
        default=SMATrendMaintVal,
        exclude=True
    )

class _SMAAdjustColumn(BaseConfig):
    base_series:str = Field(alias="base")
    adj_series:str = Field(alias="adj")

class SMAAdjustConfig(_SMAAdjustColumn):
    window:int
    indicator_class:Type[BaseIndicator] = Field(
        default=SMAadjust,
        exclude=True
    )

# ---- ema ----
class _EMACalcColumn(BaseConfig):
    base_series:str = Field(alias="base")
     
class EMACalcConfig(_EMACalcColumn):
    window:int
    smoothing:Optional[float]=None

    indicator_class:Type[BaseIndicator] = Field(
        default=EMACalc,
        exclude=True
    )

# ---- macd ----
class _MACDCalcColumn(BaseConfig):
    fast_ema:str
    slow_ema:str
     
class MACDCalcConfig(_MACDCalcColumn):
    signal:int

    indicator_class:Type[BaseIndicator] = Field(
        default=MACDCalc,
        exclude=True
    )

# ---- relation ----
class _CrossTypeColumn(BaseConfig):
    s1:str
    s2:str
    prev_s1:str
    prev_s2:str
    upper_bound:Optional[str]=None
    lower_bound:Optional[str]=None
    upper_standard:Optional[str]=None
    lower_standard:Optional[str]=None

class CrossTypeConfig(_CrossTypeColumn):
    indicator_class:Type[BaseIndicator] = Field(
        default=CrossType,
        exclude=True
    )

class _CrossValColumn(BaseConfig):
    s1:str
    s2:str
    base_series:str = Field(alias="base")
    cross_type:str
    upper_bound:Optional[str]=None
    lower_bound:Optional[str]=None
    upper_standard:Optional[str]=None
    lower_standard:Optional[str]=None

class CrossValConfig(_CrossValColumn):
    indicator_class:Type[BaseIndicator] = Field(
        default=CrossVal,
        exclude=True
    )

class _TrendTypeColumn(BaseConfig):
    upper_bound:str
    lower_bound:str
    prev_base_series:str = Field(alias="prev_base")

class TrendTypeConfig(_TrendTypeColumn):
    thresh:float
    trend_len:int

    indicator_class:Type[BaseIndicator] = Field(
        default=TrendType,
        exclude=True
    )
    
class _TrendValColumn(BaseConfig):
    upper_bound:str
    lower_bound:str
    upper_standard:str
    lower_standard:str
    trend_type:str
    base_series:str = Field(alias="base")

class TrendValConfig(_TrendValColumn):
    indicator_class:Type[BaseIndicator] = Field(
        default=TrendVal,
        exclude=True
    )

class _RelativePositionColumn(BaseConfig):
    s1:str
    s2:str

class RelativePositionConfig(_RelativePositionColumn):
    indicator_class:Type[BaseIndicator] = Field(
        default=RelativePosition,
        exclude=True
    )

class _WindowMaxColumn(BaseConfig):
    base_series:str = Field(alias="base")

class WindowMaxConfig(_WindowMaxColumn):
    window:int

    indicator_class:Type[BaseIndicator] = Field(
        default=WindowMax,
        exclude=True
    )
    
class _WindowMinColumn(BaseConfig):
    base_series:str = Field(alias="base")

class WindowMinConfig(_WindowMinColumn):
    window:int

    indicator_class:Type[BaseIndicator] = Field(
        default=WindowMin,
        exclude=True
    )
    
class _ShiftColumn(BaseConfig):
    base_series:str = Field(alias="base")

class ShiftConfig(_ShiftColumn):
    period:int

    indicator_class:Type[BaseIndicator] = Field(
        default=Shift,
        exclude=True
    )

class IndexConfig(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid"
    )

    sma_calc:Optional[dict[str, SMACalcConfig]] = None
    sma_trend:Optional[dict[str, SMATrendMaintValConfig]] = None
    sma_adjust:Optional[dict[str, SMAAdjustConfig]] = None
    ema_calc:Optional[dict[str, EMACalcConfig]] = None
    macd_calc:Optional[dict[str, MACDCalcConfig]] = None
    sma2sma_cross_standard:Optional[dict[str, SMA2SMACrossStandardConfig]] = None
    cross_type:Optional[dict[str, CrossTypeConfig]] = None
    cross_val:Optional[dict[str, CrossValConfig]] = None
    trend_type:Optional[dict[str, TrendTypeConfig]] = None
    trend_val:Optional[dict[str, TrendValConfig]] = None
    window_max:Optional[dict[str, WindowMaxConfig]] = None
    window_min:Optional[dict[str, WindowMinConfig]] = None
    shift:Optional[dict[str, ShiftConfig]] = None
    relative_pos:Optional[dict[str, RelativePositionConfig]] = None
