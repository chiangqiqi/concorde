#!/usr/bin/env python
import logging
import configparser
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
    coina = sys.argv[1]
    coinb = sys.argv[2]

    arbitrager = Arbitrager(binance, okex, ratio=0.002, informer=informer)
    while True:
        time.sleep(1)
        try:
            arbitrager.run(coina, coinb)
        except requests.exceptions.ReadTimeout as e:
            logging.warning(e)
        except Exception as e:
            logging.warning(e)
            msg = "[ERROR]:" + str(e)
            informer.send_msg(msg)
            continue

if __name__ == '__main__':
    main()
