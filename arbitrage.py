#!/usr/bin/env python
import logging
import configparser
import argparse
import sys
import time
import requests

from concorde.exchanges import BinanceWrapper,PoloWrapper,HuobiWrapper,OkexWrapper
from concorde.arbitrage import Arbitrager
from sms.telegram import TgMiddleMan


logging.basicConfig(filename='arbitrage.log',format='%(asctime)s %(message)s',level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler())

config = configparser.ConfigParser()
config.read('config.ini')

huobi_conf = config['huobi']
# huobi = HuobiWrapper(huobi_conf['pkey'],huobi_conf['skey'])

binance_conf = config['binance']
binance = BinanceWrapper(binance_conf['pkey'], binance_conf['skey'])

okex = OkexWrapper("", "")

informer = TgMiddleMan(config['middleman']['addr'])

def main():
    # arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('coina', type=str, help='coin a')
    parser.add_argument('coinb', type=str, help='coin b')

    parser.add_argument("--ratio", help="ratio of the arbitrage machine", type=float, default=0.0025)
    parser.add_argument('--use-avg', dest='ma', action='store_true')
    parser.set_defaults(ma=False)
    parser.add_argument("--max-amount", help="weather we got a limitation on the amount (coin b most of the ime)", type=float)

    args = parser.parse_args()

    arbitrager = Arbitrager(
        binance, okex,
        ratio=args.ratio, use_avg=args.ma,
        max_amount = args.max_amount, informer=informer
    )
    configkey = (args.coina + args.coinb).lower()

    if configkey in config:
        arbitrager.set_config(config[configkey])

    while True:
        time.sleep(1)
        try:
            arbitrager.run(args.coina, args.coinb)
        except requests.exceptions.ReadTimeout as e:
            logging.warning(e)
        except Exception as e:
            logging.warning(e)
            msg = "[ERROR]:" + str(e)
            informer.send_msg(msg)
            continue

if __name__ == '__main__':
    main()
