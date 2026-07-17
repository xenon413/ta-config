from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from abc import ABC, abstractmethod
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
)
from .indicators.base_indicator import BaseIndicator

class BaseConfig(BaseModel, ABC):
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
        
    @abstractmethod
    def column_mapping(self)->dict[str, str]:...

# add alias if perfer other name
# ---- sma ----
class _SMACalcColumn(BaseConfig):
    base_series:str = Field(alias="base")

    def column_mapping(self)->dict[str, str]:
        return self.model_dump(include=set(_SMACalcColumn.model_fields.keys()), exclude_none=True)
    
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

    def column_mapping(self)->dict[str, str]:
        return self.model_dump(include=set(_SMA2SMACrossStandardColumn.model_fields.keys()), exclude_none=True)
    
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

    def column_mapping(self)->dict[str, str]:
        return self.model_dump(include=set(_SMATrendMaintValColumn.model_fields.keys()), exclude_none=True)

class SMATrendMaintValConfig(_SMATrendMaintValColumn):
    window:int

    indicator_class:Type[BaseIndicator] = Field(
        default=SMATrendMaintVal,
        exclude=True
    )

class _SMAAdjustColumn(BaseConfig):
    base_series:str = Field(alias="base")
    adj_series:str = Field(alias="adj")

    def column_mapping(self)->dict[str, str]:
        return self.model_dump(include=set(_SMAAdjustColumn.model_fields.keys()), exclude_none=True)

class SMAAdjustConfig(_SMAAdjustColumn):
    window:int
    indicator_class:Type[BaseIndicator] = Field(
        default=SMAadjust,
        exclude=True
    )

# ---- ema ----
class _EMACalcColumn(BaseConfig):
    base_series:str = Field(alias="base")

    def column_mapping(self)->dict[str, str]:
        return self.model_dump(include=set(_EMACalcColumn.model_fields.keys()), exclude_none=True)
     
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

    def column_mapping(self)->dict[str, str]:
        return self.model_dump(include=set(_MACDCalcColumn.model_fields.keys()), exclude_none=True)
     
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

    def column_mapping(self)->dict[str, str]:
        return self.model_dump(include=set(_CrossTypeColumn.model_fields.keys()), exclude_none=True)

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

    def column_mapping(self)->dict[str, str]:
        return self.model_dump(include=set(_CrossValColumn.model_fields.keys()), exclude_none=True)

class CrossValConfig(_CrossValColumn):
    indicator_class:Type[BaseIndicator] = Field(
        default=CrossVal,
        exclude=True
    )

class _TrendTypeColumn(BaseConfig):
    upper_bound:str
    lower_bound:str
    prev_base_series:str = Field(alias="prev_base")

    def column_mapping(self)->dict[str, str]:
        return self.model_dump(include=set(_TrendTypeColumn.model_fields.keys()), exclude_none=True)

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

    def column_mapping(self)->dict[str, str]:
        return self.model_dump(include=set(_TrendValColumn.model_fields.keys()), exclude_none=True)

class TrendValConfig(_TrendValColumn):
    indicator_class:Type[BaseIndicator] = Field(
        default=TrendVal,
        exclude=True
    )

class _WindowMaxColumn(BaseConfig):
    base_series:str = Field(alias="base")

    def column_mapping(self)->dict[str, str]:
        return self.model_dump(include=set(_WindowMaxColumn.model_fields.keys()), exclude_none=True)

class WindowMaxConfig(_WindowMaxColumn):
    window:int

    indicator_class:Type[BaseIndicator] = Field(
        default=WindowMax,
        exclude=True
    )
    
class _WindowMinColumn(BaseConfig):
    base_series:str = Field(alias="base")

    def column_mapping(self)->dict[str, str]:
        return self.model_dump(include=set(_WindowMinColumn.model_fields.keys()), exclude_none=True)

class WindowMinConfig(_WindowMinColumn):
    window:int

    indicator_class:Type[BaseIndicator] = Field(
        default=WindowMin,
        exclude=True
    )
    
class _ShiftColumn(BaseConfig):
    base_series:str = Field(alias="base")

    def column_mapping(self)->dict[str, str]:
        return self.model_dump(include=set(_ShiftColumn.model_fields.keys()), exclude_none=True)

class ShiftConfig(_ShiftColumn):
    period:int

    indicator_class:Type[BaseIndicator] = Field(
        default=Shift,
        exclude=True
    )

class IndexConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

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
    
    @cached_property
    def config_order(self)->list[tuple[str, BaseConfig]]:
        # init
        tasks:dict[str, BaseConfig] = {} # field_name -> field
        dependencies:dict[str, list[str]] = {} # field_name -> deps_name
        task_by_output:dict[str, str] = {} # generate_name -> field_name

        for _, field in self:
            if field is None:
                continue
            field:dict[str, BaseConfig]
            for field_name, field_config in field.items():
                
                # flatten
                tasks[field_name] = field_config

                dependencies[field_name] = [d for d in field_config.column_mapping().values() if d is not None]
                
                for out_key in field_config.indicator_class.output_keys(field_name):
                    task_by_output[out_key] = field_name

        # sort
        sorted_task = []
        visited = set()
        temp_visited = set() # in one chain, prevent looping

        def visit(node:str):
            if node in temp_visited:
                raise ValueError(f"Cyclic dependency detected: {node}")
            if node not in visited:
                temp_visited.add(node)
                for dep in dependencies.get(node, []):
                    # get task from dependent if task exist
                    # if not exist view as the leaf
                    # handles the dependents on original df
                    dep_task = task_by_output.get(dep)
                    if dep_task:
                        visit(dep_task)
                temp_visited.remove(node)
                visited.add(node)
                sorted_task.append((node, tasks[node]))

        for node in tasks:
            if node not in visited:
                visit(node)

        return sorted_task

    def vector_config(self, df:pd.DataFrame)->pd.DataFrame:
        df = df.copy()
        for field_name, field_config in self.config_order:
            field_name:str
            field_config:BaseConfig

            kwargs = field_config.model_dump(exclude_none=True)
            indicator_cls = field_config.indicator_class
            
            # get columns
            col_val:dict[str, pd.Series] = {
                arg_name:df[col_name] for arg_name, col_name in field_config.column_mapping().items()
            }
            kwargs.update(col_val)
            kwargs |= {"name":field_name}
            df = pd.concat([df, indicator_cls.vector_endpoint(**kwargs)], axis=1)

        return df
    
    def stream_update(self, df:pd.DataFrame, row:dict)->pd.DataFrame:
        cur_df = df.copy()
        prev_df = cur_df.iloc[:-1]
        cur_row = row.copy()

        for field_name, field_config in self.config_order:
            field_name:str
            field_config:BaseConfig

            kwargs = field_config.model_dump(exclude_none=True)
            indicator_cls = field_config.indicator_class
            
            # get columns
            col_val:dict[str, pd.Series] = {
                arg_name:prev_df[col_name] for arg_name, col_name in field_config.column_mapping().items()
            }
            kwargs.update(col_val)
            kwargs |= {"name":field_name, "prev_df":prev_df, "cur_row":cur_row}
            res = indicator_cls.stream_handler(**kwargs)
            cur_row.update(res)

            col_pos = [prev_df.columns.get_loc(col) for col in res]
            cur_df.iloc[-1, col_pos] = list(res.values())
        
        return cur_df

    def stream_rotate(self, df:pd.DataFrame, row:dict)->pd.DataFrame:
        prev_df = df.copy()
        cur_df = df.copy()
        cur_df.loc[len(df)] = None

        cur_row = row.copy()
        for field_name, field_config in self.config_order:
            field_name:str
            field_config:BaseConfig

            kwargs = field_config.model_dump(exclude_none=True)
            indicator_cls = field_config.indicator_class
            
            # get columns
            col_val:dict[str, pd.Series] = {
                arg_name:prev_df[col_name] for arg_name, col_name in field_config.column_mapping().items()
            }
            kwargs.update(col_val)
            kwargs |= {"name":field_name, "prev_df":prev_df, "cur_row":cur_row}
            res = indicator_cls.stream_handler(**kwargs)
            cur_row.update(res)

            col_pos = [cur_df.columns.get_loc(col) for col in res]
            cur_df.iloc[-1, col_pos] = list(res.values())
        
        return cur_df
