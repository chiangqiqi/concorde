import logging
import pandas as pd

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

huobi = HuobiWrapper("","")

def check_price_for_arbi(coinA, coinB, threshold=0.0001, ratio=0.0015):
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

    logging.info("binance price is {}, {}".format(b_ask, b_bid))
    logging.info("huobi price is {}, {}".format(p_ask, p_bid))

    # 最小交易量
    # a 平台 bid 价格超过b 平台 ask 的价格时候才有套利机会
    if price_diff(ratio, b_bid, p_ask):
        logging.info("huobi ask price  {} is lower than binance bid price {}".format(p_ask, b_bid))
        # b 网执行卖单， p 网执行卖单
        b_sell_price,p_buy_price,amt = amount_and_price(format_ticker(huobi_price['asks']),
                                                        format_ticker(bina_price['bids']), ratio)

        b_eth_amt = float(binance.balance(coinA))
        amt = min(amt, b_eth_amt)
        # limit precision
        amt = round(amt * 0.999, 4)
        if amt> threshold:
            binance.trade(bina_str, b_sell_price, amt, "Sell")
        else:
            logging.info("not enogh usdt {} to trade".format(b_eth_amt))

    if price_diff(ratio, p_bid, b_ask):
        logging.info("binance ask price  {} is lower than huobi bid price {}".format(b_ask, p_bid))
        p_sell_price,b_buy_price,amt = amount_and_price(format_ticker(bina_price['asks']),
                                                        format_ticker(huobi_price['bids']), ratio)

        b_usdt_amt = float(binance.balance(coinB))
        
        # cut by a little margin to avoid lot error
        amt = min(amt, b_usdt_amt/b_buy_price)

        amt = round(amt * 0.999, 4)
        
        if amt> threshold:
            binance.trade(bina_str, b_buy_price, amt, "Buy")
        else:
            logging.info("not enogh usdt {} to trade".format(b_usdt_amt))

import time
import sys

def main():
    coina = sys.argv[1]
    coinb = sys.argv[2]


    while True:
        # try:
        check_price_for_arbi(coina, coinb)
        time.sleep(0.5)
        # except Exception as e:
            # logging.warning(e)
            # continue

if __name__ == '__main__':
    main()
