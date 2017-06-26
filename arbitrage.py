#coding=utf-8
#加载必要的库
# import numpy as np
# import pandas as pd
from __future__ import print_function
from datetime import datetime
import time
import json, requests
import time
import importlib
import asyncio
import logging
import logging.config
import yaml
import os
import aiohttp
import sys

from finance.currency import Currency, CurrencyPair, getCurrencyPairByName
from lib.yunbi.client import Client, get_api_path
from lib.bter.client import Client as BterClient
from lib.chbtc.client import Client as ChbtcClient
from exchange.bter import Exchange as BterExchange
from exchange.chbtc import Exchange as CHBTCExchange
from exchange.btc38 import Exchange as Btc38Exchange
from exchange.yunbi import Exchange as YunbiExchange
from exchange.jubi import Exchange as JubiExchange
from machine import ArbitrageMachine
from sms.ali_sms import AliSms

async def error(flag):
    if flag:
        raise ValueError("value error")
    else:
        return 1

async def test(url="http://www.baidu.com"):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout = 10) as resp:
            resp_text = await resp.text()
            print(resp.headers['Set-Cookie'])


logging.config.fileConfig("./logging.config")

def main():
    config = yaml.load(open(os.path.join("", 'config.yaml'), encoding='utf8'))
    machine = ArbitrageMachine(config)
    loop = asyncio.get_event_loop()

    if len(sys.argv) <= 2:
        print('input coin')


    d = {'zec': CurrencyPair.ZEC_CNY, 'xrp': CurrencyPair.XRP_CNY, 'BTS': CurrencyPair.BTS_CNY, 'ETC': CurrencyPair.ETC_CNY}

    cp = getCurrencyPairByName(d[sys.argv[1]])
    loop.run_until_complete(machine.run(cp))

if __name__ == '__main__':
    main()
     
