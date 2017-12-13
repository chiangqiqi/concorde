"""Profit regression
"""

import pandas as pd
from binance.client import Client as Binance

import pandas as pd

client = Binance("C9Qc9I3ge6Nz9oUH3cATNXx1rf0PtWwFyKHtklvXwn7TwDWlwCWAZkvJYlHUV7aO",
        "MUwvS9Brw30ciofOhQTuU2gTUnuDCGElgocZDLH8FpwMnRDhqqskUeGNahTFgNqJ")


import sys
def main():
    s = sys.argv[1]
    res = client.get_my_trades(symbol=s)

    df = pd.DataFrame(res)

    df.price  = df.price.map(float)
    df.qty  = df.qty.map(float)
    df['pq'] = df.price * df.qty


    print("average price:")
    res = df.groupby('isBuyer').pq.sum()/df.groupby('isBuyer').qty.sum()
    print(res)
    
    print("amount:")
    res = df.groupby('isBuyer').qty.sum()
    print(res)

    df.commission = df.commission.map(float)
    res = df.commission.sum()
    print(res)

if __name__ == '__main__':
    main()
