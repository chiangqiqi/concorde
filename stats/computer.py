import pandas as pd
import numpy as np

from binance.client import Client as Binance


binance = Binance("C9Qc9I3ge6Nz9oUH3cATNXx1rf0PtWwFyKHtklvXwn7TwDWlwCWAZkvJYlHUV7aO",
                  "MUwvS9Brw30ciofOhQTuU2gTUnuDCGElgocZDLH8FpwMnRDhqqskUeGNahTFgNqJ")

# bnbbtc = binance.get_klines(symbol='BNBBTC', interval='15m')

# btcusdt = binance.get_klines(symbol='BTCUSDT', interval='15m')
# bccusdt = binance.get_klines(symbol='BCCUSDT', interval='15m')

# ethusdt = binance.get_klines(symbol='ETHUSDT', interval='15m')

cols = ['t_open', 'open', 'high', 'low', 'close', 'vol', 't_close', 'assert_vol',
        'n_trades', 'taker_base_vol', 'taker_assert_vol', 'nounce']

def trans_kline2df(data):
    df = pd.DataFrame(data)
    df.columns = cols
    
    df['t_open'] = pd.to_datetime(pd.to_numeric(df['t_open']), unit='ms')
    df['t_close'] = pd.to_datetime(pd.to_numeric(df['t_close']), unit='ms')

    for col in cols:
        if not col.startswith('t'):
            df[col] = pd.to_numeric(df[col])

    df.set_index('t_open', inplace=True)
    return df

def retrieve_kline_df(market, interval):
    data = binance.get_klines(symbol=market, interval=interval)
    return trans_kline2df(data)

# def compare_market(df1, df2):
    # close price relation ship

import seaborn as sns

def compute_market_relation(market1, market2, interval):
    """Compute relation between two market using multi interval ticker
    """
    # intervals = ['1m', '5m', '15m', '30m', '1h', '2h', '4h']

    
    # for interval in intervals:
    df1 = retrieve_kline_df(market1, interval)
    df2 = retrieve_kline_df(market2, interval)
    
    arr = np.array([[df1.close.diff(j).corr(df2.close.diff(i)) for i in range(10)] for j in range(10)])
    
    # sns.heatmap(arr)
    
    # plt.show()
    return arr
