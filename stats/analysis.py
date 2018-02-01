"""Profit regression
"""
import sqlite3

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


from datetime import datetime
conn = sqlite3.connect('trades.db')
get_value = lambda rec: (rec['id'], rec['orderId'], rec['commission'], rec['commissionAsset'], rec['isBuyer'], rec['isMaker'],
                         float(rec['price']), float(rec['qty']),
                         datetime.fromtimestamp(rec['time']/1000))

def create_table():
    """
     {'commission': '0.08285806',
    'commissionAsset': 'BNB',
    'id': 1925591,
    'isBestMatch': True,
    'isBuyer': True,
    'isMaker': False,
    'orderId': 9815671,
    'price': '15773.07000000',
    'qty': '0.03080900',
    'time': 1513228880628} 
    """

    c.execute('''CREATE TABLE btcusdt
    (id long,orderId long, commission real, commissionAsset text, isBuyer boolean, isMaker boolean, price real, qty real, time date)''')

def save_trades_tosql(s):
    res = client.get_my_trades(symbol=s)

    c = conn.cursor()
    for rec in res:
        print(rec)
        c.execute("insert or ignore into {} values (?,?,?,?,?,?,?,?,?)".format(s), get_value(rec))

    conn.commit()
    
# select sum(qty*price)/sum(qty) as avg_price from btcusdt where time> '2017-12-13 13:00:00' group by isBuyer
# select sum(qty*price)/sum(qty), sum(qty),count(1) as avg_price from btcusdt where time> '2017-12-14 11:00:00' group by isBuyer

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'check':
        main()
    elif cmd == "sync_orders":
        save_trades_tosql("BTCUSDT")
