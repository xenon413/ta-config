import pandas as pd
import numpy as np
from math import gcd
import inspect

from .constants import CandleInterval
from .schema import IndexConfig

# using Topological Sort
# TODO: also returns the order, seperate ordering and config
def vector_config(base_df:pd.DataFrame, config:dict|IndexConfig)->pd.DataFrame:
    if isinstance(config, dict):
        config = IndexConfig.model_validate(config)

    if not isinstance(config, IndexConfig):
        raise ValueError()

    # init
    tasks = {}
    dependencies = {}
    task_by_output = {}

    for index, field in config:
        if index == "indicator_class" or index is None or field is None:
            continue

        field:dict[str, IndexConfig]
        for field_name, field_config in field.items():
            tasks[field_name] = field_config
            
            for out_key in field_config.indicator_class.output_keys(field_name):
                task_by_output[out_key] = field_name
                
            deps = field_config.dependent()
            dependencies[field_name] = [d for d in deps if d is not None]

    # sort
    sorted_tasks = []
    visited = set()
    temp_visited = set()

    def visit(node):
        if node in temp_visited:
            raise ValueError(f"Cyclic dependency detected: {node}")
        if node not in visited:
            temp_visited.add(node)
            for dep in dependencies.get(node, []):
                dep_task = task_by_output.get(dep)
                if dep_task:
                    visit(dep_task)
            temp_visited.remove(node)
            visited.add(node)
            sorted_tasks.append(node)

    for node in tasks:
        if node not in visited:
            visit(node)

    # run task
    for field_name in sorted_tasks:
        field_config = tasks[field_name]
        indicator_cls = field_config.indicator_class
        
        sig = inspect.signature(indicator_cls.vector_endpoint)
        params = sig.parameters
        
        kwargs = {}
        config_dict = field_config.model_dump()
        
        for k, v in config_dict.items():
            if k == "indicator_class" or v is None:
                continue
                
            if isinstance(v, str):
                val = base_df[v]
            else:
                val = v
                
            if k == "standard":
                if "upper_standard" in params: kwargs["upper_standard"] = val
                if "lower_standard" in params: kwargs["lower_standard"] = val
            elif k in params:
                kwargs[k] = val
            elif k + "_series" in params:
                kwargs[k + "_series"] = val

        kwargs["name"] = field_name
        
        res = indicator_cls.vector_endpoint(**kwargs)
        names = indicator_cls.output_keys(field_name)
        
        if isinstance(res, pd.Series):
            base_df[names[0]] = res
        elif isinstance(res, pd.DataFrame):
            for col in names:
                if col in res.columns:
                    base_df[col] = res[col]

    return base_df


class StreamHandle:
    def __init__(self,base_df:pd.DataFrame, config:dict|IndexConfig):
        if isinstance(config, dict):
            config = IndexConfig.model_validate(config)

        if not isinstance(config, IndexConfig):
            raise ValueError()
        
        self.config:IndexConfig = config
        self.prev_df:pd.DataFrame = vector_config(base_df, config)

    def update(self, row:dict)->dict:
        cur_df = pd.concat([self.prev_df, pd.DataFrame(row)], ignore_index=True)
        # use cur_df, prev_df, row, to config new row
        new_row = {}
        
        self.prev_df = cur_df
        return new_row

# abandoned
class SignalHandle:

    @staticmethod
    def clean_df( 
            df:pd.DataFrame,
            open_time_name:str="open_time",
            close_time_name:str="close_time",
            open_price_name:str="open_price",
            high_price_name:str="high_price",
            low_price_name:str="low_price",
            close_price_name:str="close_price",
            volume_name:str="volume",
            
        ):
        column_map = {
            open_time_name:"open_time",
            close_time_name:"close_time",
            open_price_name:"open_price",
            high_price_name:"high_price",
            low_price_name:"low_price",
            close_price_name:"close_price",
            volume_name:"volume"
        }
        df = df[column_map.keys()].copy()
        df = df.rename(columns=column_map)
        df.set_index("open_time")
        return df

    # exclude this and move to core project not here
    @staticmethod
    def merge(
            base_df:pd.DataFrame, base_interval:CandleInterval|str, 
            sub_df:pd.DataFrame, sub_interval:CandleInterval|str
        )->pd.DataFrame:

        # convert str to CandleInterval
        base_interval = base_interval if isinstance(base_interval, CandleInterval) else CandleInterval(base_interval)
        sub_interval = sub_interval if isinstance(sub_interval, CandleInterval) else CandleInterval(sub_interval)

        # get min max of both
        global_min = min(base_df.index.min(), sub_df.index.min())
        global_max = max(base_df.index.max(), sub_df.index.max())

        # generate base df that the base is the gcd of two df
        comm_interval = gcd(base_interval.ms, sub_interval.ms)
        val = np.arange(global_min, global_max+comm_interval, comm_interval)
        comm_df = pd.DataFrame(index=val)
        comm_df.index.name = base_df.index.name

        # merge and fill
        comm_df = pd.merge(comm_df, base_df, left_index=True, right_index=True, how="left")
        if base_interval-comm_interval:
            comm_df[base_df.columns] = comm_df[base_df.columns].ffill(limit=base_interval-comm_interval)

        comm_df = pd.merge(comm_df, sub_df, left_index=True, right_index=True, how="left")
        if sub_interval-comm_interval:
            comm_df[sub_df.columns] = comm_df[sub_df.columns].ffill(limit=sub_interval-comm_interval)

    # config one dataframe at a time (one interval at a time)
    # if ther's dependence between df, config it after merge
    @staticmethod
    def config_signal(
            clean_df:pd.DataFrame,
            config:dict
        ):
        pass

