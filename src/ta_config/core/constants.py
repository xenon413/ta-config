from enum import StrEnum

from .indicators import SMACalc

class CandleInterval(StrEnum):
    MIN_1="1m"
    MIN_3="3m"
    MIN_5="5m"
    MIN_15="15m"
    MIN_30="30m"
    HOUR_1="1h"
    HOUR_2="2h"
    HOUR_4="4h"
    HOUR_6="6h"
    HOUR_8="8h"
    HOUR_12="12h"
    DAY_1="1d"
    DAY_3="3d"
    WEEK_1="1w"

    @property
    def seconds(self)->int:
        '''Get the interval in seconds'''
        mapping={
            "1m": 60,"3m": 180,"5m": 300,"15m": 900,"30m": 1800,
            "1h": 3600,"2h": 7200,"4h": 14400,"6h": 21600,"8h": 28800,
            "12h": 43200,"1d": 86400,"3d": 259200,"1w": 604800
        }
        return mapping.get(self, 0)
    
    @property
    def ms(self)->int:
        return self.seconds*1000
    
