
import MetaTrader5 as mt5
import pandas as pd
from dateutil import tz
from datetime import datetime, timedelta


JST = tz.gettz('Asia/Tokyo')
UTC = tz.gettz('utc')  
        
def now():
    t = datetime.now(tz=UTC)
    return t

# numpy timestamp -> pydatetime naive
def nptimestamp2pydatetime(npdatetime):
    timestamp = (npdatetime - np.datetime64('1970-01-01T00:00:00Z')) / np.timedelta64(1, 's')
    dt = datetime.utcfromtimestamp(timestamp)
    return dt

def slice(df, ibegin, iend):
    new_df = df.iloc[ibegin: iend + 1, :]
    return new_df

def df2dic(df: pd.DataFrame):
    dic = {}
    for column in df.columns:
        dic[column] = df[column].to_numpy()
    return dic

def time_str_2_datetime(df, time_column, format='%Y-%m-%d %H:%M:%S'):
    time = df[time_column].to_numpy()
    new_time = [datetime.strptime(t, format) for t in time]
    df[time_column] = new_time
        
class Mt5Api:
    def __init__(self, symbol):
        self.symbol = symbol
        self.ticket = None
        
    @staticmethod
    def connect():
        if mt5.initialize():
            print('Connected to MT5 Version', mt5.version())
        else:
            print('initialize() failed, error code = ', mt5.last_error())

    def get_rates(self, timeframe: str, length: int):
        #print(self.symbol, timeframe)
        rates = mt5.copy_rates_from_pos(self.symbol,  timeframe, 0, length)
        if rates is None:
            raise Exception('get_rates error')
        return self.parse_rates(rates)

    def parse_rates(self, rates):
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
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
