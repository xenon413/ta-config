from decimal import Decimal, ROUND_HALF_UP
import numpy as np
import pandas as pd

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

