import pandas as pd
from .schema import IndexConfig, BaseConfig

class Config:
    @staticmethod
    def config_order(index_config: IndexConfig) -> list[tuple[str, BaseConfig]]:
        # init
        tasks: dict[str, BaseConfig] = {} # field_name -> field
        dependencies: dict[str, list[str]] = {} # field_name -> deps_name
        task_by_output: dict[str, str] = {} # generate_name -> field_name

        for _, field in index_config:
            if field is None:
                continue
            field: dict[str, BaseConfig]
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

        def visit(node: str):
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

    @classmethod
    def vector_config(cls, index_config: IndexConfig, df: pd.DataFrame, include_orign: bool = True) -> pd.DataFrame:
        results = [df] if include_orign else []
        available_cols = {col: df[col] for col in df.columns}
        
        for field_name, field_config in cls.config_order(index_config):
            field_name: str
            field_config: BaseConfig

            kwargs = field_config.model_dump(exclude_none=True)
            indicator_cls = field_config.indicator_class
            
            # get columns
            col_val: dict[str, pd.Series] = {
                arg_name: available_cols[col_name] for arg_name, col_name in field_config.column_mapping().items()
            }
            kwargs.update(col_val)
            kwargs |= {"name": field_name}
            
            new_cols = indicator_cls.vector_endpoint(**kwargs)
            results.append(new_cols)
            
            for col in new_cols.columns:
                available_cols[col] = new_cols[col]

        if not results:
            return pd.DataFrame(index=df.index)
        return pd.concat(results, axis=1)
    
    @classmethod
    def stream_update(cls, index_config: IndexConfig, df: pd.DataFrame, row: dict) -> pd.DataFrame:
        cur_df = df.copy()
        prev_df = cur_df.iloc[:-1]
        cur_row = row.copy()

        for field_name, field_config in cls.config_order(index_config):
            field_name: str
            field_config: BaseConfig

            kwargs = field_config.model_dump(exclude_none=True)
            indicator_cls = field_config.indicator_class
            
            # get columns
            col_val: dict[str, pd.Series] = {
                arg_name: prev_df[col_name] for arg_name, col_name in field_config.column_mapping().items()
            }
            kwargs.update(col_val)
            kwargs |= {"name": field_name, "prev_df": prev_df, "cur_row": cur_row}
            res = indicator_cls.stream_handler(**kwargs)
            cur_row.update(res)

            col_pos = [prev_df.columns.get_loc(col) for col in res]
            cur_df.iloc[-1, col_pos] = list(res.values())
        
        return cur_df

    @classmethod
    def stream_rotate(cls, index_config: IndexConfig, df: pd.DataFrame, row: dict) -> pd.DataFrame:
        prev_df = df.copy()
        cur_df = df.copy()
        cur_df.loc[len(df)] = None

        cur_row = row.copy()
        for field_name, field_config in cls.config_order(index_config):
            field_name: str
            field_config: BaseConfig

            kwargs = field_config.model_dump(exclude_none=True)
            indicator_cls = field_config.indicator_class
            
            # get columns
            col_val: dict[str, pd.Series] = {
                arg_name: prev_df[col_name] for arg_name, col_name in field_config.column_mapping().items()
            }
            kwargs.update(col_val)
            kwargs |= {"name": field_name, "prev_df": prev_df, "cur_row": cur_row}
            res = indicator_cls.stream_handler(**kwargs)
            cur_row.update(res)

            col_pos = [cur_df.columns.get_loc(col) for col in res]
            cur_df.iloc[-1, col_pos] = list(res.values())
        
        return cur_df
