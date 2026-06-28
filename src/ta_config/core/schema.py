from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from abc import ABC, abstractmethod
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

    indicator_map:dict = Field(default_factory=dict, exclude=True)

    @abstractmethod
    def dependent(self)->tuple[str]:
        """returns the required field name to exist before executing"""
        pass

    @abstractmethod
    def generate(self)->tuple[str, ...]:
        """returns the field name that returns after executing"""
        pass

# ---- sma ----
class SMACalcConfig(MyBaseModel):
    base:str
    window:int

    indicator_map:dict[str, BaseIndicator] = Field(
        default_factory=lambda: {SMACalc.name:SMACalc},
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

    indicator_map:dict[str, BaseIndicator] = Field(
        default_factory=lambda: {SMA2SMACrossStandard.name:SMA2SMACrossStandard},
        exclude=True
    )

    def dependent(self)->tuple[str, str, str]:
        return self.base, self.sma1, self.sma2

class SMATrendMaintValConfig(MyBaseModel):
    base:str
    sma:str
    prev_sma:Optional[str]=None
    window:int

    indicator_map:dict[str, BaseIndicator] = Field(
        default_factory=lambda: {SMATrendMaintVal.name:SMATrendMaintVal},
        exclude=True
    )

    def dependent(self)->list[str]:
        res = [self.base]
        if self.prev_sma is not None:
            res.append(self.prev_sma)
        return res

class SMAAdjustConfig(MyBaseModel):
    base:str
    adj:str
    window:int

    indicator_map:dict[str, BaseIndicator] = Field(
        default_factory=lambda: {SMAadjust.name:SMAadjust},
        exclude=True
    )

    def dependent(self)->list[str]:
        return [self.base, self.adj]

# ---- ema ----
class EMACalcConfig(MyBaseModel):
    base:str
    window:int
    smoothing:float

    indicator_map:dict[str, BaseIndicator] = Field(
        default_factory=lambda: {EMACalc.name:EMACalc},
        exclude=True
    )

    def dependent(self)->list[str]:
        return [self.base]

# ---- macd ----
class MACDCalcConfig(MyBaseModel):
    fast_ema:str
    slow_ema:str
    signal:int

    indicator_map:dict[str, BaseIndicator] = Field(
        default_factory=lambda: {MACDCalc.name:MACDCalc},
        exclude=True
    )

    def dependent(self)->list[str]:
        return [self.fast_ema, self.slow_ema]

# ---- relation ----
class CrossTypeConfig(MyBaseModel):
    s1:str
    s2:str
    prev_s1:Optional[str]
    prev_s2:Optional[str]
    upper_bound:Optional[str]
    lower_bound:Optional[str]
    upper_standard:Optional[str]
    lower_standard:Optional[str]

    indicator_map:dict[str, BaseIndicator] = Field(
        default_factory=lambda: {CrossType.name:CrossType},
        exclude=True
    )

    def dependent(self)->list[str]:
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

        return res
    
class CrossValConfig(MyBaseModel):
    s1:str
    s2:str
    base:str
    cross_type:str
    upper_bound:Optional[str]
    lower_bound:Optional[str]
    standard:Optional[str]

    indicator_map:dict[str, BaseIndicator] = Field(
        default_factory=lambda: {CrossVal.name:CrossVal},
        exclude=True
    )

    def dependent(self)->list[str]:
        res = [self.s1, self.s2, self.base, self.cross_type]
        if self.upper_bound is not None:
            res.append(self.upper_bound)

        if self.lower_bound is not None:
            res.append(self.lower_bound)

        if self.standard is not None:
            res.append(self.standard)

        return res

class TrendTypeConfig(MyBaseModel):
    upper_bound:str
    lower_bound:str
    thresh:float
    trend_len:int
    base:Optional[str]
    prev_base:Optional[str]

    indicator_map:dict[str, BaseIndicator] = Field(
        default_factory=lambda: {TrendType.name:TrendType},
        exclude=True
    )

    def dependent(self)->list[str]:
        res = [self.upper_bound, self.lower_bound]
        if self.base is not None:
            res.append(self.base)

        if self.prev_base is not None:
            res.append(self.prev_base)

        return res
    
class WindowMaxConfig(MyBaseModel):
    base:str
    window:int

    indicator_map:dict[str, BaseIndicator] = Field(
        default_factory=lambda: {WindowMax.name:WindowMax},
        exclude=True
    )

    def dependent(self)->list[str]:
        return [self.base]
    
class WindowMinConfig(MyBaseModel):
    base:str
    window:int

    indicator_map:dict[str, BaseIndicator] = Field(
        default_factory=lambda: {WindowMin.name:WindowMin},
        exclude=True
    )

    def dependent(self)->list[str]:
        return [self.base]
    
class ShiftConfig(MyBaseModel):
    base:str
    period:int

    indicator_map:dict[str, BaseIndicator] = Field(
        default_factory=lambda: {Shift.name:Shift},
        exclude=True
    )

    def dependent(self)->list[str]:
        return [self.base]

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
    window_max:Optional[dict[str, WindowMaxConfig]] = None
    window_min:Optional[dict[str, WindowMinConfig]] = None
    shift:Optional[dict[str, Shift]] = None
    