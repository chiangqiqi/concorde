#!/usr/bin/env python


import logging
from datetime import datetime
import time

from coinex.client import Client

pkey = '5316330BEF5F43D3B656D9760F95202C'
skey = '02C9A322D79E466FAFACB47D400C2301E50A0F70D94BE826'

from pymongo import MongoClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mc = MongoClient()
order_tab = mc['coinex']['orders']
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
    
    return d


def mmake(market, ratio=0.001, amt=0.2):
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
        order_tab.insert(resp)
        placed_orders.append(Order('sell', ask_price, amt))

        resp = client.trade(market, bid_price, amt, 'buy')
        print("placing sell order")
        print(resp)
        placed_orders.append(Order('buy', bid_price, amt))
        order_tab.insert(resp)

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
        client.trade(market, top_ask * (1-0.0005), 0.2, 'sell')
    elif top_bid * balance[coina] < 1/3 * balance[coinb]:
        client.trade(market, top_bid * (1+0.0005), 0.2, 'buy')
    
        
def check_order_filled():
    account = client.get_account()
    # check if there is no
    data = account['data']
    logging.debug(data)
    for coin, balance in data.items():
        if float(balance['frozen']) > 0:
            logging.info('coin {} has frozen value {}'.format(coin, balance['frozen']))
            return False
      
    return True

def cancel_old_orders(market):
    orders = client.get_orders(market)['data']['data']

    now_ts = int(time.time())

    def delete_old_order(order):
        create_time = order['create_time']
        # cancel order that was older than 30 minutes
        if now_ts - create_time > 300:
            resp = client.delete_order(order['id'], market)
            logging.info("delete order {}".format(resp))

    #  如果两个方向的订单都没有成交, 两个方向的订单都取消
    if len(orders) >= 2:
        for order in orders:
            delete_old_order(order)
    elif len(orders) == 1:
        # replace current order with a order
        order = orders[0]

        if now_ts - order['create_time'] < 300:
            return
        
        depth = client.depth(market)['data']
        asks,bids = depth['asks'], depth['bids']
        top_bid,top_ask = top_price(bids),top_price(asks)
      
        delta = (top_ask-top_bid) * 0.1
        if order['type'] == 'sell':
            client.trade(market, top_ask - delta, 0.2, 'sell')
        elif order['type'] == 'buy':
            client.trade(market, top_bid + delta, 0.2, 'buy')
       
        resp = client.delete_order(order['id'], market)
        logging.info("delete order {}".format(resp))
                
            
# mmake('ltcbtc')
if __name__ == '__main__':
    market = 'LTCBTC'
    while 1:
        try:
            # order is not all filled
            if not check_order_filled():
                logging.info("got unfilled order")
                # try to cancel old unfilled order
                cancel_old_orders(market)
            else:
                #account_balance('LTC', 'BTC')
        
                mmake('LTCBTC')
        except Exception as e:
            logging.warning(e)
            
        time.sleep(5)
