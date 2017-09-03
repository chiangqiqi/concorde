#coding=utf-8
#加载必要的库
# import numpy as np
# import pandas as pd
from __future__ import print_function
import asyncio
import logging
import logging.config
import yaml
import os
import sys

from finance.currency import CurrencyPair
from machine import ArbitrageMachine

logging.config.fileConfig("./logging.config")

def main():
    config = yaml.load(open(os.path.join("", 'config.yaml'), encoding='utf8'))
    machine = ArbitrageMachine(config)
    loop = asyncio.get_event_loop()

    d = {'XRP': CurrencyPair.XRP_CNY, 'BTS': CurrencyPair.BTS_CNY,
         'ETC': CurrencyPair.ETC_CNY, 'ETH': CurrencyPair.ETH_CNY,
         'ANS': CurrencyPair.ANS_CNY, 'ZEC': CurrencyPair.ZEC_CNY,
         'NXT': CurrencyPair.NXT_CNY,
         'QTUM': CurrencyPair.QTUM_CNY,
         'BCC': CurrencyPair.BCC_CNY,
         'EOS': CurrencyPair.EOS_CNY,
    }

    coin = sys.argv[1]
    # cp = getCurrencyPairByName(d[sys.argv[1]])
    loop.run_until_complete(machine.run(d[coin]))

if __name__ == '__main__':
    main()
