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


polo = Poloniex("DJWOINQK-6RANSEOQ-S0K6E1RH-OLRSHH0K",
                "c267c3fcf439bdca2673a0ff1420a407970f8b85bbe44cbea64801a6b213047c3021178b20fd47a55d599f120368f557d48eb1bcc8e1bfa59d0d32e9c7140bbe")

binance = Binance("C9Qc9I3ge6Nz9oUH3cATNXx1rf0PtWwFyKHtklvXwn7TwDWlwCWAZkvJYlHUV7aO",
"MUwvS9Brw30ciofOhQTuU2gTUnuDCGElgocZDLH8FpwMnRDhqqskUeGNahTFgNqJ")

"""
polo.returnTicker
"""

# wrapper for client code
top_price = lambda l: float(l[0][0])
price_diff = lambda r,x,y: (x-y)/x> r

def check_price_for_arbi():
    polo_price = polo.returnOrderBook("USDT_ETH")
    bina_price = binance.get_order_book(symbol="ETHUSDT")

    # 买一价和卖一价, bid is higher than asks
    p_ask, p_bid = top_price(polo_price['asks']), top_price(bina_price['asks'])
    b_ask, b_bid = top_price(polo_price['bids']), top_price(bina_price['bids'])

    ratio = 0.002

    print("binance price is {}, {}".format(b_ask, b_bid))
    print("poloniex price is {}, {}".format(p_ask, p_bid))
    if price_diff(0.002, p_ask, b_bid):
        print("poloniex ask price  {} is higher than binance bid price {}".format(p_ask, b_bid))

    if price_diff(0.002, b_ask, p_bid):
        print("binance ask price  {} is higher than poloniex bid price {}".format(b_ask, p_bid))



while True:
    check_price_for_arbi()
# binance.get_all_tickers
