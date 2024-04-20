import os
import sys
sys.path.append('../Libraries/trade')

import MetaTrader5 as mt5
import pandas as pd
from dateutil import tz
from datetime import datetime, timedelta, timezone
from time_utils import TimeUtils
JST = tz.gettz('Asia/Tokyo')
UTC = tz.gettz('utc')  
        
def server_time(begin_month, begin_sunday, end_month, end_sunday, delta_hour_from_gmt_in_summer):
    now = datetime.now(JST)
    dt, tz = TimeUtils.delta_hour_from_gmt(now, begin_month, begin_sunday, end_month, end_sunday, delta_hour_from_gmt_in_summer)
    #delta_hour_from_gmt  = dt
    #server_timezone = tz
    #print('SeverTime GMT+', dt, tz)
    return dt, tz  
  
def adjust_summer_time(time: datetime):
    dt, tz = server_time(3, 2, 11, 1, 3.0)
    return time - dt

def adjust(dic, column='time'):
    utc = dic[column]
    time = []
    jst = []
    for ts in utc:
        t0 = pd.to_datetime(ts)
        t0 = t.replace(tzinfo=UTC)
        t = adjust_summer_time(t0)
        time.append(t)
        tj = t.astimezone(JST)
        jst.append(tj)  
    dic[column] = time
    dic['jst'] = jst
            
class Mt5Api:
    def __init__(self):
        self.connect()
        
    def connect():
        if mt5.initialize():
            print('Connected to MT5 Version', mt5.version())
        else:
            print('initialize() failed, error code = ', mt5.last_error())

    def get_rates(self, symbol: str, timeframe: str, length: int):
        #print(symbol, timeframe)
        rates = mt5.copy_rates_from_pos(symbol,  timeframe, 0, length)
        if rates is None:
            raise Exception('get_rates error')
        return self.parse_rates(rates)

    def parse_rates(self, rates):
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        adjust(df, 'time')
        
        return df
        


def test1():
    symbol = 'NIKKEI'
    mt5trade = Mt5Api(symbol)
    mt5trade.connect()
    ret, result = mt5trade.entry(Signal.SHORT, 0.1, stoploss=300.0)
    result.description()
    mt5trade.close_order_result(result, result.volume)
    pass


if __name__ == '__main__':
    test1()
