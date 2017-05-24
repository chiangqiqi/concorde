#coding=utf-8
#加载必要的库
# import numpy as np
# import pandas as pd
from __future__ import print_function
from datetime import datetime
import time
import json, requests
import time
import sys, traceback


class Fee():
	def enum(**enums):
		return type('Enum', (), enums)
	FeeTypes = enum(PERC = 1, FIX = 2)
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
			  "eth": {"bter": Fee(0.001, Fee.FeeTypes.PERC),
					  "yunbi": Fee(0.001, Fee.FeeTypes.PERC),
					  "chbtc": Fee(0.0005, Fee.FeeTypes.PERC)},
			  "zec": {"bter": Fee(0.001, Fee.FeeTypes.PERC),
					  "yunbi": Fee(0.001, Fee.FeeTypes.PERC)},
			  "doge": {"bter": Fee(0.002, Fee.FeeTypes.PERC),
					  "btc38": Fee(0.001, Fee.FeeTypes.PERC),
					  "jubi": Fee(0.001, Fee.FeeTypes.PERC)},
			  "xpm": {"bter": Fee(0.002, Fee.FeeTypes.PERC),
					  "jubi": Fee(0.001, Fee.FeeTypes.PERC)},
			  "nxt": {"bter": Fee(0.002, Fee.FeeTypes.PERC),
					  "btc38": Fee(0.001, Fee.FeeTypes.PERC)},
			  "xrp": {"jubi": Fee(0.001, Fee.FeeTypes.PERC),
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
			    "eth": {"bter": Fee(0.01, Fee.FeeTypes.FIX),
					    "yunbi": Fee(0.01, Fee.FeeTypes.FIX),
					    "chbtc": Fee(0.01, Fee.FeeTypes.FIX)},
			    "zec": {"bter": Fee(0.0002, Fee.FeeTypes.FIX),
					    "yunbi": Fee(0.0006, Fee.FeeTypes.FIX)},
			    "xpm": {"bter": Fee(0.01, Fee.FeeTypes.FIX),
					    "jubi": Fee(0.01, Fee.FeeTypes.FIX)},
			    "nxt": {"bter": Fee(0.003, Fee.FeeTypes.PERC),
					    "btc38": Fee(0.01, Fee.FeeTypes.PERC)},
			    "doge": {"jubi": Fee(0.001, Fee.FeeTypes.PERC), #不要withdraw
					    "btc38": Fee(0.001, Fee.FeeTypes.PERC)}, #不要withdraw
			    "xrp": {"jubi": Fee(0.001, Fee.FeeTypes.PERC), #不要withdraw
					    "btc38": Fee(0.001, Fee.FeeTypes.PERC)}, #不要withdraw
			    "bts": {"bter": Fee(0.01, Fee.FeeTypes.PERC),
					    "yunbi": Fee(10, Fee.FeeTypes.FIX),
					    "btc38": Fee(0.01, Fee.FeeTypes.PERC)}}
gain_target = 0.001
urls = {"bts": {"bter": "http://data.bter.com/api2/1/orderBook/bts_cny",
				"btc38": 'http://api.btc38.com/v1/depth.php?c=bts&mk_type=cny',
				"yunbi": 'https://yunbi.com//api/v2/depth.json?market=btscny&limit=10'},
		"dash": {"bter": "http://data.bter.com/api2/1/orderBook/dash_cny",
				"btc38": 'http://api.btc38.com/v1/depth.php?c=dash&mk_type=cny'},
		"etc": {"bter": "http://data.bter.com/api2/1/orderBook/etc_cny",
				"yunbi": 'https://yunbi.com//api/v2/depth.json?market=etccny&limit=10',
				"chbtc": 'http://api.chbtc.com/data/v1/depth?currency=etc_cny&size=10'},
		"eth": {"bter": "http://data.bter.com/api2/1/orderBook/eth_cny",
				"yunbi": 'https://yunbi.com//api/v2/depth.json?market=ethcny&limit=10',
				"chbtc": 'http://api.chbtc.com/data/v1/depth?currency=eth_cny&size=10'},
		"nxt": {"bter": "http://data.bter.com/api2/1/orderBook/nxt_cny",
				"btc38": 'http://api.btc38.com/v1/depth.php?c=nxt&mk_type=cny'},
		"doge": {"jubi": "http://www.jubi.com/api/v1/depth?coin=doge",
				"btc38": 'http://api.btc38.com/v1/depth.php?c=doge&mk_type=cny'},
		"xrp": {"jubi": "http://www.jubi.com/api/v1/depth?coin=xrp",
				"btc38": 'http://api.btc38.com/v1/depth.php?c=xrp&mk_type=cny'},
		"xpm": {"jubi": "http://www.jubi.com/api/v1/depth?coin=xpm",
				"bter": "http://data.bter.com/api2/1/orderBook/xpm_cny"},
		"zec": {"bter": "http://data.bter.com/api2/1/orderBook/zec_cny",
				"yunbi": 'https://yunbi.com//api/v2/depth.json?market=zeccny&limit=10'}
		}
interval = 3

# def get_yunbi_quote(url): #'https://yunbi.com//api/v2/depth.json?market=btscny&limit=10'
# 	r = requests.get(url, timeout=30)
# 	result = r.json()
# 	tmp = sorted(result["bids"], key = lambda x: float(x[0]), reverse=True)
# 	bids = list(map(lambda x: {'price':float(x[0]), 'quantity':float(x[1])}, tmp))
# 	tmp = sorted(result["asks"], key = lambda x: float(x[0]))
# 	asks = list(map(lambda x: {'price':float(x[0]), 'quantity':float(x[1])}, tmp))
# 	quotes = {"bids": bids, "asks": asks}
# 	return quotes

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
	exchange_a = "jubi"
	# exchange_a = "yunbi"
	# exchange_b = "yunbi"
	exchange_b = "btc38"
	# exchange_b = "chbtc"
	# exchange_b = "jubi"
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
		print("[%s] %s(bid %.6f, ask %.6f), %s(bid %.6f, ask %.6f) "%(datetime.now(),exchange_a,
			bter_quote["bids"][bter_i]["price"],
			bter_quote["asks"][bter_j]["price"],
			exchange_b,
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

			# alpha_flat = sell_amount - buy_amount - withdraw_cost - trade_cost
			alpha_flat = sell_amount - buy_amount - trade_cost
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
				check_entry("doge")
			except Exception as e:
				print("error: %s"%(e))
				ex_type, ex, tb = sys.exc_info()
				traceback.print_tb(tb)

run()
# post_yunbi()
# post_bter()
# post_chbtc()

