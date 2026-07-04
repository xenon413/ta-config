from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from abc import ABC, abstractmethod
from typing import Type

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
)
from .indicators.base_indicator import BaseIndicator

class MyBaseModel(BaseModel, ABC):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True
    )

    indicator_class:Type[BaseIndicator] = Field(
        default=BaseIndicator,
        exclude=True
    )

    @abstractmethod
    def dependent(self)->tuple[str]:
        """returns the required field name to exist before executing"""
        pass

    # @abstractmethod
    # def generate(self)->tuple[str, ...]:
    #     """returns the field name that returns after executing"""
    #     pass

# ---- sma ----
class SMACalcConfig(MyBaseModel):
    base:str
    window:int

    indicator_class:Type[BaseIndicator] = Field(
        default=SMACalc,
        exclude=True
    )

    def dependent(self)->tuple[str]:
        return self.base,

class SMA2SMACrossStandardConfig(MyBaseModel):
    base:str
    sma1:str
    window1:int
    sma2:str
    window2:int

    indicator_class:Type[BaseIndicator] = Field(
        default=SMA2SMACrossStandard,
        exclude=True
    )

    def dependent(self)->tuple[str, str, str]:
        return self.base, self.sma1, self.sma2

class SMATrendMaintValConfig(MyBaseModel):
    base:str
    sma:str
    prev_sma:str
    window:int

    indicator_class:Type[BaseIndicator] = Field(
        default=SMATrendMaintVal,
        exclude=True
    )

    def dependent(self)->tuple[str, str, str]:
        return self.base, self.sma, self.prev_sma

class SMAAdjustConfig(MyBaseModel):
    base:str
    adj:str
    window:int

    indicator_class:Type[BaseIndicator] = Field(
        default=SMAadjust,
        exclude=True
    )

    def dependent(self)->tuple[str,str]:
        return self.base, self.adj

# ---- ema ----
class EMACalcConfig(MyBaseModel):
    base:str
    window:int
    smoothing:Optional[float]=None

    indicator_class:Type[BaseIndicator] = Field(
        default=EMACalc,
        exclude=True
    )

    def dependent(self)->tuple[str]:
        return self.base,

# ---- macd ----
class MACDCalcConfig(MyBaseModel):
    fast_ema:str
    slow_ema:str
    signal:int

    indicator_class:Type[BaseIndicator] = Field(
        default=MACDCalc,
        exclude=True
    )

    def dependent(self)->tuple[str,str]:
        return self.fast_ema, self.slow_ema

# ---- relation ----
class CrossTypeConfig(MyBaseModel):
    s1:str
    s2:str
    prev_s1:str
    prev_s2:str
    upper_bound:Optional[str]=None
    lower_bound:Optional[str]=None
    upper_standard:Optional[str]=None
    lower_standard:Optional[str]=None

    indicator_class:Type[BaseIndicator] = Field(
        default=CrossType,
        exclude=True
    )

    def dependent(self)->tuple[str, ...]:
        res = [self.s1, self.s2]
        if self.prev_s1 is not None:
            res.append(self.prev_s1)

        if self.prev_s2 is not None:
            res.append(self.prev_s2)

        if self.upper_bound is not None:
            res.append(self.upper_bound)

        if self.lower_bound is not None:
            res.append(self.lower_bound)

        if self.upper_standard is not None:
            res.append(self.upper_standard)

        if self.lower_standard is not None:
            res.append(self.lower_standard)

        return tuple(res)
    
class CrossValConfig(MyBaseModel):
    s1:str
    s2:str
    base:str
    cross_type:str
    upper_bound:Optional[str]=None
    lower_bound:Optional[str]=None
    upper_standard:Optional[str]=None
    lower_standard:Optional[str]=None

    indicator_class:Type[BaseIndicator] = Field(
        default=CrossVal,
        exclude=True
    )

    def dependent(self)->tuple[str, ...]:
        res = [self.s1, self.s2, self.base, self.cross_type]
        if self.upper_bound is not None:
            res.append(self.upper_bound)

        if self.lower_bound is not None:
            res.append(self.lower_bound)

        if self.upper_standard is not None:
            res.append(self.upper_standard)

        if self.lower_standard is not None:
            res.append(self.lower_standard)

        return tuple(res)

class TrendTypeConfig(MyBaseModel):
    upper_bound:str
    lower_bound:str
    thresh:float
    trend_len:int
    prev_base:str

    indicator_class:Type[BaseIndicator] = Field(
        default=TrendType,
        exclude=True
    )

    def dependent(self)->tuple[str, str, str]:
        return self.upper_bound, self.lower_bound, self.prev_base
    
class TrendValConfig(MyBaseModel):
    upper_bound:str
    lower_bound:str
    upper_standard:str
    lower_standard:str
    trend_type:str
    base:str

    indicator_class:Type[BaseIndicator] = Field(
        default=TrendVal,
        exclude=True
    )

    def dependent(self)->tuple[str, ...]:
        return self.upper_bound, self.lower_bound, self.upper_standard, self.lower_standard, self.trend_type, self.base
    
class WindowMaxConfig(MyBaseModel):
    base:str
    window:int

    indicator_class:Type[BaseIndicator] = Field(
        default=WindowMax,
        exclude=True
    )

    def dependent(self)->tuple[str]:
        return self.base,
    
class WindowMinConfig(MyBaseModel):
    base:str
    window:int

    indicator_class:Type[BaseIndicator] = Field(
        default=WindowMin,
        exclude=True
    )

    def dependent(self)->tuple[str]:
        return self.base,
    
class ShiftConfig(MyBaseModel):
    base:str
    period:int

    indicator_class:Type[BaseIndicator] = Field(
        default=Shift,
        exclude=True
    )

    def dependent(self)->tuple[str]:
        return self.base,

class IndexConfig(MyBaseModel):
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
    
    def dependent(self)->tuple[str, ...]:...

