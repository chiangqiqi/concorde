# from poloniex import 
from binance.client import Client as Binance

# import binance.
from poloniex import Poloniex

import logging

# Binance :
# API Key:
# C9Qc9I3ge6Nz9oUH3cATNXx1rf0PtWwFyKHtklvXwn7TwDWlwCWAZkvJYlHUV7aO
# Secret:
# MUwvS9Brw30ciofOhQTuU2gTUnuDCGElgocZDLH8FpwMnRDhqqskUeGNahTFgNqJ

# poloniex

# API Key
# DJWOINQK-6RANSEOQ-S0K6E1RH-OLRSHH0K
# Secret
# c267c3fcf439bdca2673a0ff1420a407970f8b85bbe44cbea64801a6b213047c3021178b20fd47a55d599f120368f557d48eb1bcc8e1bfa59d0d32e9c7140bbe

"""
polo.returnTicker
"""

# wrapper for client code
top_price = lambda l: float(l[0][0])
price_diff = lambda r,x,y: (x-y)/x> r

from enum import *

class ArbitrageEx:
    """abstract class for client
    """
    def __init__(self, args):
        "docstring"
        pass

import pandas as pd

parsedepth = lambda x: float(x)

class PoloWrapper:
    """a simple polo wrapper
    """
    def __init__(self, pkey, skey):
        """
        :param: pkey: public key
        :param: skey: secret key
        """
        self.client = Poloniex(pkey, skey)
        
    def trade(self, currency_pair, price, amount, trade_side):
        """trade_type: buy or sell

        polo client api is buy(self, currencyPair, rate, amount, orderType=False)
        """
        if trade_side == "Buy":
            self.client.buy(currency_pair, price, amount)
        elif trade_side == "Sell":
            self.client.sell(currency_pair, price, amount)

    def balance(self, currency=None):
        if not currency:
            return self.client.returnBalances()

        return self.client.returnBalances()[currency]

    def depth(self, currency_pair):
        return self.client.returnOrderBook(currency_pair)

from binance.enums import SIDE_BUY,SIDE_SELL,ORDER_TYPE_LIMIT,TIME_IN_FORCE_IOC,TIME_IN_FORCE_GTC

class BinanceWrapper:
    """Simple binance api wrapper
    """
    def __init__(self, pkey, skey):
        """
        :param: pkey: public key
        :param: skey: secret key
        """
        self.client = Binance(pkey, skey)
        
    def trade(self, currency_pair, price, amount, trade_side):
        """trade_side: buy or sell

        polo client api is buy(self, currencyPair, rate, amount, orderType=False)
        """
        if trade_side == "Buy":
            ttype = SIDE_BUY
        elif trade_side == "Sell":
            ttype = SIDE_SELL
        
        order = self.client.create_order(
            symbol=currency_pair,
            side=ttype,
            type=ORDER_TYPE_LIMIT,
            quantity=amount,
            price=price,
            timeInForce=TIME_IN_FORCE_GTC)

        print("place a sell order in binance {} {} {}".format(currency_pair, price, amount))


    def balance(self, currency=None):
        account_info = self.client.get_account()
        balances = account_info["balances"]


        balances_dict = dict([(rec['asset'], rec['free']) for rec in balances])

        if not currency:
            return balances_dict

        return balances_dict[currency]

    def depth(self, currency_pair):
        return self.client.get_order_book(symbol=currency_pair)

    
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

polo = PoloWrapper("DJWOINQK-6RANSEOQ-S0K6E1RH-OLRSHH0K",
                   "c267c3fcf439bdca2673a0ff1420a407970f8b85bbe44cbea64801a6b213047c3021178b20fd47a55d599f120368f557d48eb1bcc8e1bfa59d0d32e9c7140bbe")

binance = BinanceWrapper("C9Qc9I3ge6Nz9oUH3cATNXx1rf0PtWwFyKHtklvXwn7TwDWlwCWAZkvJYlHUV7aO",
                         "MUwvS9Brw30ciofOhQTuU2gTUnuDCGElgocZDLH8FpwMnRDhqqskUeGNahTFgNqJ")


def check_price_for_arbi(coinA, coinB, threshold=0.0001, ratio=0.0015):
    """keep in mind  ask price is higher than 
    coinB: 基准货币，比如 btc, usdt
    coinA: 交易货币
    """
    bina_str = "{}{}".format(coinA, coinB)
    polo_str = "{}_{}".format(coinB, coinA)

    polo_price = polo.depth(polo_str)
    bina_price = binance.depth(bina_str)

    # 买一价和卖一价, bid is higher than asks
    p_ask, b_ask = top_price(polo_price['asks']), top_price(bina_price['asks'])
    p_bid, b_bid = top_price(polo_price['bids']), top_price(bina_price['bids'])

    print("binance price is {}, {}".format(b_ask, b_bid))
    print("poloniex price is {}, {}".format(p_ask, p_bid))

    # 最小交易量
    # a 平台 bid 价格超过b 平台 ask 的价格时候才有套利机会
    if price_diff(ratio, b_bid, p_ask):
        print("poloniex ask price  {} is lower than binance bid price {}".format(p_ask, b_bid))
        # b 网执行卖单， p 网执行卖单
        b_sell_price,p_buy_price,amt = amount_and_price(format_ticker(polo_price['asks']),
                                                        format_ticker(bina_price['bids']), ratio)

        b_eth_amt = float(binance.balance(coinA))
        amt = min(amt, b_eth_amt)
        # limit precision
        amt = round(amt, 3)
        if amt> threshold:
            binance.trade(bina_str, b_sell_price, amt, "Sell")
        else:
            print("not enogh usdt {} to trade".format(b_eth_amt))

    if price_diff(ratio, p_bid, b_ask):
        print("binance ask price  {} is lower than poloniex bid price {}".format(b_ask, p_bid))
        p_sell_price,b_buy_price,amt = amount_and_price(format_ticker(bina_price['asks']),
                                                        format_ticker(polo_price['bids']), ratio)

        b_usdt_amt = float(binance.balance(coinB))
        
        # cut by a little margin to avoid lot error
        amt = min(amt, b_usdt_amt/b_buy_price * 0.9)

        amt = round(amt, 3)
        
        if amt> threshold:
            binance.trade(bina_str, b_buy_price, amt, "Buy")
        else:
            print("not enogh usdt {} to trade".format(b_usdt_amt))

import time
import sys

def main():
    coina = sys.argv[1]
    coinb = sys.argv[2]
    while True:
        try:
            check_price_for_arbi(coina, coinb)
            time.sleep(0.5)
        except Exception as e:
            print(e)
            continue

if __name__ == '__main__':
    main()
