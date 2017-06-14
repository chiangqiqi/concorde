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

from finance.currency import Currency, CurrencyPair
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
config = yaml.load(open(os.path.join("", 'config.yaml'), encoding='utf8'))

async def test_sms():
	smsClient = AliSms(config['sms'])
	result = await smsClient.sendOpenOrderSms("bter", "123", 10, 1.2)
	print(result)

machine = ArbitrageMachine(config)
loop = asyncio.get_event_loop()
loop.run_until_complete(machine.run(CurrencyPair.BTS_CNY))
# loop.run_until_complete(machine.run(CurrencyPair.ETC_CNY))
# loop.run_until_complete(machine.run(CurrencyPair.XRP_CNY))
# loop.run_until_complete(machine.run(CurrencyPair.DOGE_CNY))
# loop.run_until_complete(machine.sendOpenOrderWarnSms("bter", "123", 10, 1.2))
# loop.run_until_complete(test_sms())
# loop.run_until_complete(machine.testTransferCoin())
# loop.run_until_complete(post_bter())
# # loop.run_until_complete(post_chbtc())


	 
class Fee():
	def enum(**enums):
		return type('Enum', (), enums)
	FeeTypes = enum(PERC = 1, FIX = 2, MIX = 3)
	def __init__(self, fee, fee_type):
		self.fee = fee
		self.fee_type = fee_type
	def calculate_fee(self, num):
		if (self.fee_type == self.FeeTypes.PERC):
			return num * self.fee
		else:
			return self.fee

data_path = "./result/result_sim0.85_bars100_ev0.000040_loss_line1.000000_2016_12.csv"
# data_path = "./result/sim0.90_bars30_ev0.000040_loss_line1.000000_2016_02.csv"
# data_path = "./result/action_sim0.85_bars100_ev0.000040_loss_line1.000000_2016_12.csv"

# trade_fees = {"bter": 0.002, "btc38": 0.001}
trade_fees = {"zec": {"bter": Fee(0.001, Fee.FeeTypes.PERC),
					  "yunbi": Fee(0.001, Fee.FeeTypes.PERC)},
			  "etc": {"bter": Fee(0.001, Fee.FeeTypes.PERC),
					  "yunbi": Fee(0.001, Fee.FeeTypes.PERC),
					  "chbtc": Fee(0.0005, Fee.FeeTypes.PERC)},
			  "nxt": {"bter": Fee(0.002, Fee.FeeTypes.PERC),
					  "btc38": Fee(0.001, Fee.FeeTypes.PERC)},
			  "bts": {"bter": Fee(0.002, Fee.FeeTypes.PERC),
					  "yunbi": Fee(0.001, Fee.FeeTypes.PERC),
					  "btc38": Fee(0.001, Fee.FeeTypes.PERC)}}
# withdraw_fees = {"bter": 0.01, "btc38": 0.01}
withdraw_fees = {"zec": {"bter": Fee(0.0006, Fee.FeeTypes.FIX),
					    "yunbi": Fee(0.0002, Fee.FeeTypes.FIX)},
			    "etc": {"bter": Fee(0.01, Fee.FeeTypes.FIX),
					    "yunbi": Fee(0.01, Fee.FeeTypes.FIX),
					    "chbtc": Fee(0.01, Fee.FeeTypes.FIX)},
			    "nxt": {"bter": Fee(0.003, Fee.FeeTypes.PERC),
					    "btc38": Fee(0.01, Fee.FeeTypes.PERC)},
			    "bts": {"bter": Fee(0.01, Fee.FeeTypes.PERC),
					    "yunbi": Fee(10, Fee.FeeTypes.FIX),
					    "btc38": Fee(0.01, Fee.FeeTypes.PERC)}}
gain_target = 0.001
urls = {"bts": {"bter": "http://data.bter.com/api2/1/orderBook/bts_cny",
				"btc38": 'http://api.btc38.com/v1/depth.php?c=bts&mk_type=cny',
				"yunbi": 'https://yunbi.com//api/v2/depth.json?market=btscny&limit=10'},
		"dash": {"bter": "http://data.bter.com/api2/1/orderBook/dash_cny",
				"btc38": 'http://api.btc38.com/v1/depth.php?c=dash&mk_type=cny'},
		"doge": {"bter": "http://data.bter.com/api2/1/orderBook/doge_cny",
				"btc38": 'http://api.btc38.com/v1/depth.php?c=doge&mk_type=cny'},
		"eth": {"bter": "http://data.bter.com/api2/1/orderBook/eth_cny",
				"yunbi": 'https://yunbi.com//api/v2/depth.json?market=ethcny&limit=10'},
		"etc": {"bter": "http://data.bter.com/api2/1/orderBook/etc_cny",
				"yunbi": 'https://yunbi.com//api/v2/depth.json?market=etccny&limit=10',
				"chbtc": 'http://api.chbtc.com/data/v1/depth?currency=etc_cny&size=10'},
		"nxt": {"bter": "http://data.bter.com/api2/1/orderBook/nxt_cny",
				"btc38": 'http://api.btc38.com/v1/depth.php?c=nxt&mk_type=cny'},
		"zec": {"bter": "http://data.bter.com/api2/1/orderBook/zec_cny",
				"yunbi": 'https://yunbi.com//api/v2/depth.json?market=zeccny&limit=10'}
		}
interval = 3


def get_bter_quote(url): #"http://data.bter.com/api2/1/orderBook/bts_cny"
	r = requests.get(url, timeout=10)
	result = r.json()
	tmp = sorted(result["bids"], key = lambda x: float(x[0]), reverse=True)
	bids = list(map(lambda x: {'price':float(x[0]), 'quantity':float(x[1])}, tmp))
	tmp = sorted(result["asks"], key = lambda x: float(x[0]))
	asks = list(map(lambda x: {'price':float(x[0]), 'quantity':float(x[1])}, tmp))
	quotes = {"bids": bids, "asks": asks}
	return quotes

def get_btc38_quote(url): #'http://api.btc38.com/v1/depth.php?c=bts&mk_type=cny'
	r = requests.get(url, timeout=10)
	result = r.json()
	tmp = sorted(result["bids"], key = lambda x: float(x[0]), reverse=True)
	bids = list(map(lambda x: {'price':float(x[0]), 'quantity':float(x[1])}, tmp))
	tmp = sorted(result["asks"], key = lambda x: float(x[0]))
	asks = list(map(lambda x: {'price':float(x[0]), 'quantity':float(x[1])}, tmp))
	quotes = {"bids": bids, "asks": asks}
	return quotes

def check_entry(id):
	exchange_a = "bter"
	# exchange_b = "yunbi"
	exchange_b = "btc38"
	# exchange_b = "chbtc"
	id_urls = urls[id]
	bter_url = id_urls[exchange_a]
	btc38_url = id_urls[exchange_b]
	bter_quote = get_bter_quote(bter_url)
	btc38_quote = get_btc38_quote(btc38_url)
	stop_flag = False
	bter_i = 0 #bid
	bter_j = 0 #ask
	btc38_i = 0 #bid
	btc38_j = 0 #ask
	while not stop_flag:
		trade_cost = 0.0
		withdraw_cost = 0.0
		print("[%s] bter(bid %.6f, ask %.6f), btc(bid %.6f, ask %.6f) "%(datetime.now(),
			bter_quote["bids"][bter_i]["price"],
			bter_quote["asks"][bter_j]["price"],
			btc38_quote["bids"][btc38_i]["price"],
			btc38_quote["asks"][btc38_j]["price"]), end='', flush=True)
		if (bter_quote["bids"][bter_i]["price"] > btc38_quote["asks"][btc38_j]["price"]):
			bid_price = bter_quote["bids"][bter_i]["price"]
			ask_price = btc38_quote["asks"][btc38_j]["price"]
			buy_quantity = btc38_quote["asks"][btc38_j]["quantity"]
			sell_quantity = bter_quote["bids"][bter_i]["quantity"]
			trade_quantity = min(buy_quantity, sell_quantity)
			buy_amount = ask_price * trade_quantity
			sell_amount = bid_price * trade_quantity
			trade_cost += trade_fees[id][exchange_b].calculate_fee(buy_amount) + trade_fees[id][exchange_a].calculate_fee(sell_amount)
			withdraw_cost += withdraw_fees[id][exchange_b].calculate_fee(trade_quantity) * bid_price

			alpha_flat = sell_amount - buy_amount - withdraw_cost - trade_cost
			alpha = (alpha_flat) / buy_amount
			if alpha >= (gain_target):
				print("(%s->%s)arbitrage!!!!buy_amount=%.2f, sell_amount=%.2f, trade_cost=%.2f, withdraw_cost=%.2f, alpha_flat=%.2f, alpha = %f"%(
					exchange_b, exchange_a, buy_amount, sell_amount, trade_cost, withdraw_cost, alpha_flat, alpha), flush=True)
				stop_flag = True
			else:
				print("(%s->%s)buy_amount=%.2f, sell_amount=%.2f, trade_cost=%.2f, withdraw_cost=%.2f, alpha_flat=%.2f, alpha = %f"%(
					exchange_b, exchange_a, buy_amount, sell_amount, trade_cost, withdraw_cost, alpha_flat, alpha), flush=True)
				if buy_quantity < sell_quantity:
					btc38_j += 1
				elif sell_quantity < buy_quantity:
					bter_i += 1
				else:
					btc38_j += 1
					bter_i += 1
		elif (bter_quote["asks"][bter_j]["price"] < btc38_quote["bids"][btc38_i]["price"]):
			bid_price = btc38_quote["bids"][btc38_i]["price"]
			ask_price = bter_quote["asks"][bter_j]["price"]
			buy_quantity = bter_quote["asks"][bter_j]["quantity"]
			sell_quantity = btc38_quote["bids"][btc38_i]["quantity"]
			trade_quantity = min(buy_quantity, sell_quantity)
			buy_amount = ask_price * trade_quantity
			sell_amount = bid_price * trade_quantity
			trade_cost += trade_fees[id][exchange_b].calculate_fee(sell_amount) + trade_fees[id][exchange_a].calculate_fee(buy_amount)
			withdraw_cost += withdraw_fees[id][exchange_b].calculate_fee(trade_quantity) * bid_price

			alpha_flat = sell_amount - buy_amount - withdraw_cost - trade_cost
			alpha = (alpha_flat) / buy_amount
			if alpha >= (gain_target):
				print("(%s->%s)arbitrage!!!!buy_amount=%.2f, sell_amount=%.2f, trade_cost=%.2f, withdraw_cost=%.2f, alpha_flat=%.2f, alpha = %f"%(
					exchange_a, exchange_b, buy_amount, sell_amount, trade_cost, withdraw_cost, alpha_flat, alpha), flush=True)
				stop_flag = True
			else:
				print("(%s->%s)buy_amount=%.2f, sell_amount=%.2f, trade_cost=%.2f, withdraw_cost=%.2f, alpha_flat=%.2f, alpha = %f"%(
					exchange_a, exchange_b, buy_amount, sell_amount, trade_cost, withdraw_cost, alpha_flat, alpha), flush=True)
				if buy_quantity < sell_quantity:
					bter_j += 1
				elif sell_quantity < buy_quantity:
					btc38_i += 1
				else:
					btc38_i += 1
					bter_j += 1
		else:
			print("no alpha", flush = True)
			stop_flag = True

def run():
	prev_check_time = datetime.now()
	while True:
		tick = datetime.now()
		elapse = (tick - prev_check_time).total_seconds()
		if (elapse < interval):
			time.sleep(interval - elapse)
		else:
			prev_check_time = datetime.now()
			try:
				check_entry("bts")
			except Exception as e:
				print("error: %s"%(e))

# # run()
# post_yunbi()
# # post_bter()
# loop = asyncio.get_event_loop()
# loop.run_until_complete(post_bter())
# loop.run_until_complete(post_chbtc())
# loop.run_until_complete(post_btc38())
# loop.run_until_complete(post_yunbi())
# loop.run_until_complete(post_jubi())
# # post_chbtc()

