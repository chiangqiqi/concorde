#!/usr/bin/env python


pkey = '***'
skey = '***'

from coinex.client import Client

client = Client(pkey, skey)


account =  client.get_account()

top_price = lambda l: float(l[0][0])

def mmake(market, ratio=0.001, amt=0.1):
    depth = client.depth(market)['data']
    asks,bids = depth['asks'], depth['bids']
    top_bid,top_ask = top_price(bids),top_price(asks)
    
    mid = (top_ask + top_bid)/2
    if top_ask/top_bid > 1.002:
        ask_price = mid * (1+ratio)
        bid_price = mid * (1-ratio)
        
        import pdb; pdb.set_trace()
        # place 2 orders
        client.trade(market, ask_price, amt, 'sell')
        client.trade(market, bid_price, amt, 'buy')
    
mmake('ltcbtc')
