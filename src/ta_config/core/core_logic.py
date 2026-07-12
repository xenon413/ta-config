import pandas as pd
import numpy as np
from math import gcd

from .constants import CandleInterval
from .schema import IndexConfig

class StreamHandle:
    def __init__(self,base_df:pd.DataFrame, config:dict|IndexConfig):
        if isinstance(config, dict):
            config = IndexConfig.model_validate(config)

        if not isinstance(config, IndexConfig):
            raise ValueError()
        
        self.config:IndexConfig = config
        self.prev_df:pd.DataFrame = config.config(base_df)

    def update(self, row:dict)->dict:
        # update the dataframe
        cur_df = pd.concat([self.prev_df, pd.DataFrame(row)], ignore_index=True)
        cur_df = cur_df.iloc[1:].reset_index(drop=True)
        # use cur_df, prev_df, row, to config new row
        new_row = {}
        
        # update prev data
        self.prev_df = cur_df
        return new_row
