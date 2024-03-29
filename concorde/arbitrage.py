import logging
import pandas as pd
from collections import deque
import time
import sys
import numpy as np
import math

from itertools import takewhile
import functools

# wrapper for client code
top_price = lambda l: float(l[0][0])
price_diff = lambda r,x,y: (x-y)/x> r

parsedepth = lambda x: float(x)

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


def price_deform(price,r):
    return [(float(rec[0])*r, float(rec[1])) for rec in price]

def precision_floor(f, presicion=2):
    base = math.pow(10, presicion)
    return math.floor(f * base) / base


class Arbitrager:
    def __init__(self, exchangeA, exchangeB,
                 ratio=0.0025, precision=3, informer=None, use_avg=False, 
                 max_amount=None, max_amount_a=None):
        """
        precision: Binance sometimes got a LOT error if the amount is with a presicion higher
        """
        self.exchangeA = exchangeA
        self.exchangeB = exchangeB
        # self._coinA = coinA
        # self._coinB = coinB
        self.threshold=0.0001
        self.ratio = ratio
        self.use_avg = use_avg
        self.amt_precision = precision
        self.informer = informer
        # max buy in amount
        self.max_amount = max_amount
        # 2 hour MA
        self.q = deque(maxlen=7200)

    def set_config(self, config):
        """
        """
        self.threshold = float(config['threshold'])
        self.amt_precision = int(config['precision'])

    def run(self, coinA, coinB):
        """keep in mind  ask price is higher than
        coinB: 基准货币，比如 btc, usdt
        coinA: 交易货币
        """
        bina_str = "{}{}".format(coinA, coinB)
        # huobi_str = "{}{}".format(coinA, coinB).lower()
        huobi_str = "{}_{}".format(coinA, coinB).lower()

        huobi_price = self.exchangeB.depth(huobi_str)
        bina_price = self.exchangeA.depth(bina_str)

        p_ask, b_ask = top_price(huobi_price['asks']), top_price(bina_price['asks'])
        p_bid, b_bid = top_price(huobi_price['bids']), top_price(bina_price['bids'])

        if self.use_avg:
            self.q.append((p_ask, b_ask, p_bid, b_bid))
            arr = np.array(self.q)
            avg_price(arr)

            huobi_div_bina = avg_price(arr)
            logging.info("ratio is {}".format(huobi_div_bina))

            # deform the other platform price
            huobi_price = {}
            huobi_price['asks'] = price_deform(bina_price['asks'], huobi_div_bina)
            huobi_price['bids'] = price_deform(bina_price['bids'], huobi_div_bina)

            # 买一价和卖一价, bid is higher than asks
            p_ask, b_ask = top_price(huobi_price['asks']), top_price(bina_price['asks'])
            p_bid, b_bid = top_price(huobi_price['bids']), top_price(bina_price['bids'])

            if len(self.q) < 100:
                logging.info("ticker length is {}".format(len(self.q)))
                return

        logging.info("binance price is {}, {}".format(b_ask, b_bid))
        logging.info("huobi price is {}, {}".format(p_ask, p_bid))

        # 最小交易量
        # a 平台 bid 价格超过b 平台 ask 的价格时候才有套利机会
        if price_diff(self.ratio, b_bid, p_ask):
            logging.info("huobi ask price  {} is lower than binance bid price {}".format(p_ask, b_bid))
            # b 网执行卖单， p 网执行买单
            b_sell_price,p_buy_price,amt = amount_and_price(format_ticker(huobi_price['asks']),
                                                            format_ticker(bina_price['bids']), self.ratio)

            b_eth_amt = float(self.exchangeA.balance(coinA))
            b_usdt_amt = float(self.exchangeA.balance(coinB))
            # p_usdt_amt = float(self.exchangeA.balance(coinB))

            amt = b_eth_amt
            # amt = min(amt, p_usdt_amt/p_buy_price)
            # limit precision

            if self.max_amount is not None:
                amt = min(amt, (self.max_amount - b_usdt_amt)/b_sell_price)

            amt = precision_floor(amt, self.amt_precision)

            if amt> self.threshold:
                self.exchangeA.trade(bina_str, b_sell_price, amt, "Sell")
                if self.informer:
                    msg = "place a {} sell order with amount {} at price {}.".format(bina_str, amt, b_sell_price)
                    self.informer.send_msg(msg)
                # self.exchangeA.trade(huobi_str, p_buy_price, amt, "Buy")
            else:
                logging.info("not enogh {} {} to trade".format(coinA ,b_eth_amt))
                # logging.info("not enogh usdt {} to trade".format(p_usdt_amt))

        if price_diff(self.ratio, p_bid, b_ask):
            logging.info("binance ask price  {} is lower than huobi bid price {}".format(b_ask, p_bid))
            p_sell_price,b_buy_price,amt = amount_and_price(format_ticker(bina_price['asks']),
                                                            format_ticker(huobi_price['bids']), self.ratio)

            b_usdt_amt = float(self.exchangeA.balance(coinB))
            b_eth_amt = float(self.exchangeA.balance(coinA))
            # p_eth_amt = float(self.exchangeA.balance(coinA))

            # cut by a little margin to avoid lot error
            amt = min(amt, b_usdt_amt/b_buy_price)
            if self.max_amount_a is not None:
                amt = min(amt, self.max_amount_a - b_eth_amount)


            amt = precision_floor(amt, self.amt_precision)

            if amt> self.threshold:
                # print("buy")
                self.exchangeA.trade(bina_str, b_buy_price, amt, "Buy")
                if self.informer:
                    msg = "place a {} buy order with amount {} at price {}.".format(bina_str, amt, b_buy_price)
                    self.informer.send_msg(msg)
                # self.exchangeA.trade(huobi_str, p_sell_price, amt, "Sell")
            else:
                logging.info("not enogh usdt {} to trade".format(b_usdt_amt))
                # logging.info("not enogh {} {} to trade".format(coinA ,p_eth_amt))


def avg_price(arr):
    """average price of usdt between two platform
    """
    avg =  np.mean(arr, axis=0)
    ask_ratio, bid_ratio  = avg[1]/avg[0], avg[3]/avg[2]
    print("avg ratio between two platform is {}, {}".format(ask_ratio, bid_ratio))
    return (ask_ratio+ bid_ratio)/2
