import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from dateutil import tz

JST = tz.gettz('Asia/Tokyo')
UTC = tz.gettz('utc') 


def nans(length:int):
    out = [np.nan for _ in range(length)]
    return out

def time_utc(year: int, month: int, day: int, hour: int, minute: int):
    t = datetime(year, month, day, hour, minute)
    return t.replace(tzinfo=UTC)    


class DataBuffer:
    def __init__(self, arrays: dict, time_column: str):
        self.arrays = arrays
        self.time_column = time_column
        self.keys = list(self.arrays.keys())
        self.size = len(arrays[self.keys[0]])
        
    def time_array(self):
        return self.arrays[self.time_column]
        
    def time_last(self):
        time = self.time_array()
        return time[-1]
        
    def add_empty(self, keys: [str]):
        for key in keys:
            self.arrays[key] = nans(self.size)
        self.keys = list(self.arrays.keys())
        
    def shift(self, length=1):
        for key, array in self.arrays.items():
            new_array = array[length:] + nans(length)
            self.arrays[key] = new_array
            
    def slice_dic(self, data: dict, begin: int, end: int):
        dic = {}
        for key, array in data.items():
            dic[key] = array[begin: end + 1]
        return dic, (end - begin + 1)
            
    def split_data(self, data: dict):
        t_last = self.time_last()
        time = data[self.time_column]
        n = len(time)
        index = None
        for i, t in enumerate(time):
            if t > t_last:
                index = i
                break
        if index is None:
            return (data, None, 0)
        
        replace_data, length = self.slice_dic(data, 0, index - 1)
        new_data, new_length = self.slice_dic(data, index, n - 1)                 
        return (replace_data, new_data, new_length)
        
    def update(self, data: dict):
        length = None
        for key, value in data.items():
            if length is None:
                length = len(value)
            else:
                if length != len(value):
                    raise Exception('Dimension error')
        replace_data, new_data, new_length = self.split_data(data)
        self.replace(replace_data)
        if new_length > 0:
            self.add_data(new_data, new_length)
            return new_length
        else:
            return 0
                
    
    def replace(self, data: dict):
        time = self.time_array()
        t_list = data[self.time_column]
        for i, t in enumerate(t_list):
            for j, t0 in enumerate(time):
                if t == t0:
                    for key, array in data.items():
                        self.arrays[key][j] = array[i]
                    break
                
                
    def add_data(self, data: dict, length: int):
        for key in self.keys:
            if key in data.keys():
                new_array =  self.arrays[key][length:] + data[key]                
            else:
                new_array = self.arrays[key][length:] + nans(length)
            self.arrays[key] = new_array

    def get_data(self, key: str):
        return self.arrays[key]
    
    def data_last(self, key: str, length: int):
        array = self.arrays[key]
        return array[-length:]

    def update_data(self, key, data):
        length = len(data)
        array = self.arrays[key]
        begin = self.size - length
        for i, d in enumerate(data):
            array[begin + i] = d 
            
    
def test():
    def print_array(dic):
        print('time', dic['time'])
        print('open', dic['open'])
        print('close', dic['close'])
        print('ma3', dic['ma3'])
        print('ma5', dic['ma5'])
        print()
        
    from technical import moving_average
    
    t0 = time_utc(2024, 1, 1, 8, 0)
    utc = [t0 + timedelta(minutes=i) for i in range(10)]
    dic = {
            'time': utc,    
            'open': [10, 20, 30, 40, 50, -20, 70, 80, 90, 100],
            'close': [1, 2, 3, -7, 5, -1, 7, 8, 9, 9.9]
          }
    buffer = DataBuffer(dic, 'time')

    buffer.add_empty(['ma3', 'ma5'])    
    print('#1')
    print_array(buffer.arrays)
    
    op = buffer.arrays['open']
    data2 = moving_average(op, 3)
    buffer.update_data('ma3', data2)
    data3 = moving_average(op, 5)
    buffer.update_data('ma5', data3)
    print('#2')
    print_array(buffer.arrays)
 
    utc2 = [utc[-2] + timedelta(minutes=i) for i in range(1, 5) ]
    dic2 = {
                'time': utc2,
                'open': [-100, -200, -300, -400],
                'close': [-22, -33, -44, -55]
            }
    n = buffer.update(dic2)
    
    op = buffer.data_last('open', 6)
    data2 = moving_average(op, 3)
    buffer.update_data('ma3', data2[-3:])
    
    op = buffer.data_last('open', 8)
    data3 = moving_average(op, 5)
    buffer.update_data('ma5', data3[-3:])
    print('#3')
    print_array(buffer.arrays)
    
    
if __name__ == '__main__':
    test()
    
    
    