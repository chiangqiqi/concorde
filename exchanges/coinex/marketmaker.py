#!/usr/bin/env python

from coinex.client import Client

pkey = '5316330BEF5F43D3B656D9760F95202C'
skey = '02C9A322D79E466FAFACB47D400C2301E50A0F70D94BE826'

from pymongo import MongoClient

mc = MongoClient()
orders = mc['coinex']['orders']
client = Client(pkey, skey)


# account =  client.get_account()

top_price = lambda l: float(l[0][0])

from collections import namedtuple

placed_orders = []

Order = namedtuple("Order", ['type', 'price', 'amount'])


def refresh_balance():
    resp = client.get_account()
    d = {}
    data = resp['data']
    
    for coin in data:
        d[coin] = float(data[coin]['available'])
    
    balance = d
    return d


def mmake(market, ratio=0.001, amt=0.1):
    depth = client.depth(market)['data']
    asks,bids = depth['asks'], depth['bids']
    top_bid,top_ask = top_price(bids),top_price(asks)
    
    mid = (top_ask + top_bid)/2
    
    balance = refresh_balance()
   
    if top_ask/top_bid < 1.002:
        print("no price gap")
    else:
        ask_price = mid * (1+ratio)
        bid_price = mid * (1-ratio)
        
        # check if we have enogh balance
        if balance['BTC'] < amt * ask_price:
            print("no enogh btc {}".format(balance))
            return 

       
        # import pdb; pdb.set_trace()
        # place 2 orders
        resp = client.trade(market, ask_price, amt, 'sell')
        print("placing sell order")
        print(resp)
        orders.insert(resp)
        placed_orders.append(Order('sell', ask_price, amt))

        resp = client.trade(market, bid_price, amt, 'buy')
        print("placing sell order")
        print(resp)
        placed_orders.append(Order('buy', bid_price, amt))
        orders.insert(resp)
        
def account_balance(coina, coinb):
    if coina == 'BTC':
        market = coinb+coina
    else:
        market = coina+coinb
   
    balance = refresh_balance()
    
    depth = client.depth(market)['data']
    asks,bids = depth['asks'], depth['bids']
    top_bid,top_ask = top_price(bids),top_price(asks)
    
    # coinb is btc too much ltc, too little btc
    if balance[coinb] < 1/3 * top_bid * balance[coina]:
        client.trade(market, top_ask * (1-0.0005), 0.1, 'sell')
    elif top_bid * balance[coina] < 1/3 * balance[coinb]:
        client.trade(market, top_bid * (1+0.0005), 0.1, 'buy')
    
        
import time
# mmake('ltcbtc')
if __name__ == '__main__':
    while 1:
        account_balance('LTC', 'BTC')
        mmake('ltcbtc')
        time.sleep(1)
