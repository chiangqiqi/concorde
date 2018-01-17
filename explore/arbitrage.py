import logging
import pandas as pd
from collections import deque
import math

from exchanges import BinanceWrapper,PoloWrapper,HuobiWrapper

logging.basicConfig(filename='arbitrage_huobi.log',format='%(asctime)s %(message)s',level=logging.INFO)

"""
polo.returnTicker
"""

# wrapper for client code
top_price = lambda l: float(l[0][0])
price_diff = lambda r,x,y: (x-y)/x> r


parsedepth = lambda x: float(x)

    
from itertools import takewhile
import functools

def amount_and_price(bask, abid, ratio):
    """return buy price and sell price for two exchange depth array, and the amount
    bid is smaller than 

    corr: bprice and a price may got a 
    """
    topbid,topask = top_price(abid),top_price(bask)
    
    condi = functools.partial(price_diff, ratio)
    ask_chi = list(takewhile(lambda x: condi(topbid, x[0]), bask))
    bid_chi = list(takewhile(lambda x: condi(x[0], topask), abid))

    price_bid, price_ask = bid_chi[-1][0], ask_chi[-1][0]
    sum_amt = lambda l: sum([x[1] for x in l])

    amt = min(sum_amt(ask_chi), sum_amt(bid_chi))

    return price_bid, price_ask, amt


format_ticker = lambda l: [(float(x[0]), float(x[1])) for x in l]

binance = BinanceWrapper("C9Qc9I3ge6Nz9oUH3cATNXx1rf0PtWwFyKHtklvXwn7TwDWlwCWAZkvJYlHUV7aO",
                         "MUwvS9Brw30ciofOhQTuU2gTUnuDCGElgocZDLH8FpwMnRDhqqskUeGNahTFgNqJ")

import configparser

config = configparser.ConfigParser()
config.read('config.ini')

huobi_conf = config['huobi']
huobi = HuobiWrapper(huobi_conf['pkey'],huobi_conf['skey'])

def price_deform(price,r):
    return [(float(rec[0])*r, float(rec[1])) for rec in price]

def precision_floor(f, presicion=2):
    base = math.pow(10, presicion)
    return math.floor(f * base) / base


def check_price_for_arbi(coinA, coinB, threshold=0.0001, ratio=0.0025):
    """keep in mind  ask price is higher than 
    coinB: 基准货币，比如 btc, usdt
    coinA: 交易货币
    """
    bina_str = "{}{}".format(coinA, coinB)
    huobi_str = "{}{}".format(coinA, coinB).lower()

    huobi_price = huobi.depth(huobi_str)
    bina_price_before = binance.depth(bina_str)

    p_ask, b_ask = top_price(huobi_price['asks']), top_price(bina_price_before['asks'])
    p_bid, b_bid = top_price(huobi_price['bids']), top_price(bina_price_before['bids'])
   
    q.append((p_ask, b_ask, p_bid, b_bid))
    arr = np.array(q)
    avg_price(arr)

    huobi_div_bina = avg_price(arr)
    logging.info("ratio is {}".format(huobi_div_bina))

   
    # deform the other platform price
    bina_price = {}
    bina_price['asks'] = price_deform(bina_price_before['asks'], 1/huobi_div_bina)
    bina_price['bids'] = price_deform(bina_price_before['bids'], 1/huobi_div_bina)

    # 买一价和卖一价, bid is higher than asks
    p_ask, b_ask = top_price(huobi_price['asks']), top_price(bina_price['asks'])
    p_bid, b_bid = top_price(huobi_price['bids']), top_price(bina_price['bids'])

    logging.info("binance price is {}, {}".format(b_ask, b_bid))
    logging.info("huobi price is {}, {}".format(p_ask, p_bid))


    if len(q) < 100:
        logging.info("ticker length is {}".format(len(q)))
        return
 
    # 最小交易量
    # a 平台 bid 价格超过b 平台 ask 的价格时候才有套利机会
    if price_diff(ratio, b_bid, p_ask):
        logging.info("huobi ask price  {} is lower than binance bid price {}".format(p_ask, b_bid))
        # b 网执行卖单， p 网执行买单
        b_sell_price,p_buy_price,amt = amount_and_price(format_ticker(huobi_price['asks']),
                                                        format_ticker(bina_price['bids']), ratio)

        # b_eth_amt = float(binance.balance(coinA))
        p_usdt_amt = float(huobi.balance(coinB))

        amt = min(amt, p_usdt_amt/p_buy_price)
        # limit precision
        amt = precision_floor(amt, 4)

        if amt> threshold:
            # binance.trade(bina_str, b_sell_price, amt, "Sell")
            huobi.trade(huobi_str, p_buy_price, amt, "Buy")
        else:
            logging.info("not enogh usdt {} to trade".format(p_usdt_amt))

    if price_diff(ratio, p_bid, b_ask):
        logging.info("binance ask price  {} is lower than huobi bid price {}".format(b_ask, p_bid))
        p_sell_price,b_buy_price,amt = amount_and_price(format_ticker(bina_price['asks']),
                                                        format_ticker(huobi_price['bids']), ratio)

        # b_usdt_amt = float(binance.balance(coinB))
        p_eth_amt = float(huobi.balance(coinA))
        
        # cut by a little margin to avoid lot error
        # amt = min(amt, b_usdt_amt/b_buy_price)

        amt = precision_floor(p_eth_amt, 4)

        if amt> threshold:
            # print("buy")
            # binance.trade(bina_str, b_buy_price, amt, "Buy")
            huobi.trade(huobi_str, p_sell_price, amt, "Sell")
        else:
            logging.info("not enogh {} {} to trade".format(coinA ,p_eth_amt))

import time
import sys
import numpy as np

q = deque(maxlen=3600)

def avg_price(arr):
    """average price of usdt between two platform
    """
    avg =  np.mean(arr, axis=0)

    ask_ratio, bid_ratio  = avg[1]/avg[0], avg[3]/avg[2]

    print("avg ratio between two platform is {}, {}".format(ask_ratio, bid_ratio))

    return (ask_ratio+ bid_ratio)/2


def check_price_stats(coinA, coinB, threshold=0.0001, ratio=0.0015):
    """keep in mind  ask price is higher than 
    coinB: 基准货币，比如 btc, usdt
    coinA: 交易货币
    """
    bina_str = "{}{}".format(coinA, coinB)
    huobi_str = "{}{}".format(coinA, coinB).lower()

    huobi_price = huobi.depth(huobi_str)
    bina_price = binance.depth(bina_str)

    # 买一价和卖一价, bid is higher than asks
    p_ask, b_ask = top_price(huobi_price['asks']), top_price(bina_price['asks'])
    p_bid, b_bid = top_price(huobi_price['bids']), top_price(bina_price['bids'])

    q.append((p_ask, b_ask, p_bid, b_bid))

    arr = np.array(q)

    avg_price(arr)

def main():
    coina = sys.argv[1]
    coinb = sys.argv[2]

    if coina == "ETH":
        thres = 0.001
    elif coina == "BTC":
        thres = 0.0001

    while True:
        time.sleep(1)
        try:
            check_price_for_arbi(coina, coinb, threshold=thres)
        except Exception as e:
            logging.warning(e)
            continue

if __name__ == '__main__':
    main()
