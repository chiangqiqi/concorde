#coding=utf-8
#加载必要的库
# import numpy as np
# import pandas as pd
from __future__ import print_function
from datetime import datetime
import time
import math
import json, requests
import sys, traceback
# from exchange.bter import Exchange as BterExchange
# from exchange.chbtc import Exchange as CHBTCExchange
from exchange.currency import Currency, CurrencyPair, currencyPair2Currency
import importlib
import asyncio
import logging
import logging.config

waterLogger = logging.getLogger("water")

class ArbitrageMachine(object):
	def __init__(self, config):
		self.config = config
		self.exchanges = {}
		exchanges = self.config['arbitrage']['exchanges']
		logging.info("initilizing %d exchange: %s", len(exchanges), exchanges)
		for exch in exchanges:
			exchConfig = list(filter(lambda x: x['name'] == exch, config['exchange']))[0]
			logging.info("initilizing exchange %s, config: %s", exch, exchConfig)
			e = importlib.import_module("exchange.%s"%exch).Exchange(exchConfig)
			self.exchanges.update({exch: e})

	# async def checkEntry(buyExchangeName, )
	
	def determineGainTarget(self, buyExchangeCoinAmount, sellExchangeCoinAmount):
		balanceRatio = self.config['arbitrage']['balance_ratio']
		if buyExchangeCoinAmount / sellExchangeCoinAmount < balanceRatio:
			return self.config['arbitrage']['balance_target_gain']
		else:
			return self.config['arbitrage']['arbitrage_target_gain']

	def _floor(self, num, precision = 3):
		multiplier = math.pow(10.0, precision)
		return math.floor(num * multiplier) / multiplier

	# return True if both order success
	async def doArbitrageOrder(self, 
							 currencyPair, 
							 buyExchangeName, 
							 buyPrice, 
							 buyAmount,
							 sellExchangeName,
							 sellPrice,
							 sellAmount):
		logging.info("doArbitrageOrder: [%s] buy price %f, buy amount %f, [%s] sell price %f, sell amount %f",
					buyExchangeName, buyPrice, buyAmount, sellExchangeName, sellPrice, sellAmount)
		(buyOrderId, sellOrderId) = await asyncio.gather(
			self.exchanges[buyExchangeName].buyAsync(currencyPair, price = buyPrice, amount = buyAmount),
			self.exchanges[sellExchangeName].sellAsync(currencyPair, price = sellPrice, amount = sellAmount),
			return_exceptions = True)
		if issubclass(type(buyOrderId), Exception) and issubclass(type(sellOrderId), Exception):
			logging.warn("place buy order to %s fail[%s] and place sell order to %s fail[%s], return to checkEntryAndArbitrage",
					buyExchangeName, buyOrderId, sellExchangeName, sellOrderId)
			return (False, None, None)

		if issubclass(type(buyOrderId), Exception):
			maxOrderRetry = filter(lambda x: x['name'] == buyExchangeName, self.config['exchange']).__next__()['max_order_retry']
			tryTimes = 1
			while issubclass(type(buyOrderId), Exception):
				logging.warn("place buy order to %s fail[%s], will try again[%d/%d]",
						buyExchangeName, buyOrderId, tryTimes, maxOrderRetry)
				tryTimes += 1
				if tryTimes > 3:
					logging.warn("place buy order to %s fail[%s], will try again[%d/%d]",
							buyExchangeName, buyOrderId, tryTimes, maxOrderRetry)
					break
				else:
					buyOrderId = await self.exchanges[buyExchangeName].buyAsync(currencyPair, price = buyPrice, amount = buyAmount)

		if issubclass(type(sellOrderId), Exception):
			maxOrderRetry = filter(lambda x: x['name'] == sellExchangeName, self.config['exchange']).__next__()['max_order_retry']
			tryTimes = 1
			while issubclass(type(sellOrderId), Exception):
				logging.warn("place sell order to %s fail[%s], will try again[%d/%d]",
						sellExchangeName, sellOrderId, tryTimes, maxOrderRetry)
				tryTimes += 1
				if tryTimes > 3:
					logging.warn("place sell order to %s fail[%s], will try again[%d/%d]",
							sellExchangeName, sellOrderId, tryTimes, maxOrderRetry)
					break
				else:
					sellOrderId = await self.exchanges[sellExchangeName].sellAsync(currencyPair, price = sellPrice, amount = sellAmount)

		# just log
		if not issubclass(type(buyOrderId), Exception):
			logging.info("place buy order to %s success, price %f, amount %f, id %s",
					buyExchangeName, buyPrice, buyAmount, buyOrderId)
		if not issubclass(type(sellOrderId), Exception):
			logging.info("place sell order to %s success, price %f, amount %f, id %s",
					sellExchangeName, sellPrice, sellAmount, sellOrderId)
		if not issubclass(type(buyOrderId), Exception) and not issubclass(type(sellOrderId), Exception):
			return (True, buyOrderId, sellOrderId)
		else:
			return (False, None, None)

	# return True if arbitrage exist and order success else False
	async def checkEntryAndArbitrage(self, 
									currencyPair,
									buyExchangeName,
									askItems, 
									sellExchangeName,
									bidItems):
		currency = currencyPair2Currency(currencyPair)
		balanceRatio = self.config['arbitrage']['balance_ratio']
		coinTradeMinimum = self.config['arbitrage']['coin_trade_minimum'][currencyPair]
		coinTradeMaximum = self.config['arbitrage']['coin_trade_maximum'][currencyPair]

		#获取余额
		buyExchangeCash = self.exchanges[buyExchangeName].accountInfo['balances'][Currency.CNY]
		sellExchangeCash = self.exchanges[sellExchangeName].accountInfo['balances'][Currency.CNY]
		buyExchangeCoinAmount = self.exchanges[buyExchangeName].accountInfo['balances'][currency]
		sellExchangeCoinAmount = self.exchanges[sellExchangeName].accountInfo['balances'][currency]
		# ((buyExchangeCash, buyExchangeCoinAmount),  (sellExchangeCash, sellExchangeCoinAmount)) = \
		# 	await asyncio.gather(self.exchanges[buyExchangeName].getMultipleCurrencyAmountAsync(Currency.CNY, currency),
		# 						 self.exchanges[sellExchangeName].getMultipleCurrencyAmountAsync(Currency.CNY, currency))
		logging.debug("[%s]buyExchangeCash %f, buyExchangeCoinAmount %f", buyExchangeName, buyExchangeCash, buyExchangeCoinAmount)
		logging.debug("[%s]sellExchangeCash %f, sellExchangeCoinAmount %f", sellExchangeName, sellExchangeCash, sellExchangeCoinAmount)
		
		#校验有没足够的币卖
		if sellExchangeCoinAmount < coinTradeMinimum:
			logging.warn("%s do not have enough coin to sell, only have %f, coin_trade_minimum is %f",
						sellExchangeName, sellExchangeCoinAmount, coinTradeMinimum)
			return False
		
		#校验有没足够的的钱买币
		if askItems[0].price * coinTradeMinimum > buyExchangeCash:
			logging.warn("%s do not have enough money to buy, only have %f, coin_trade_minimum is %f, min ask price is %f",
						buyExchangeName, buyExchangeCash, coinTradeMinimum, askItems[0].price)
			return False
		
		#决定套利收获
		gainTarget = self.determineGainTarget(buyExchangeCoinAmount, sellExchangeCoinAmount)

		#判断是否能够套利
		for bidItem in bidItems:
			bidPrice = bidItem.price
			bidAmount = bidItem.amount
			if (bidPrice <= askItems[0].price):
				logging.info("%s[ask %.6f(%.6f)], %s[bid %.6f(%.6f)], no alpha",
							buyExchangeName, askItems[0].price, askItems[0].amount,
							sellExchangeName, bidPrice, bidAmount)
				break
			for askItem in askItems:
				askPrice = askItem.price
				askAmount = askItem.amount

				# no alpha
				if (bidPrice <= askPrice):
					logging.info("%s[ask %.6f(%.6f)], %s[bid %.6f(%.6f)] no alpha",
								buyExchangeName, askPrice, askAmount,
								sellExchangeName, bidPrice, bidAmount)
					break

				#决定卖币数量
				#卖币数量 = min(bidAmount, askAmount, sellExchangeCoinAmount, avaliableBuyAmount, balanceTransferAmount)
				avaliableBuyAmount = self._floor(buyExchangeCash / askPrice)
				tradeAmount = min(bidAmount, askAmount)
				tradeAmount = min(tradeAmount, coinTradeMaximum)
				tradeAmount = min(tradeAmount, sellExchangeCoinAmount)
				tradeAmount = min(tradeAmount, avaliableBuyAmount)
				if buyExchangeCoinAmount / sellExchangeCoinAmount < balanceRatio:
					balanceTransferAmount =  sellExchangeCoinAmount - (buyExchangeCoinAmount + sellExchangeCoinAmount) / 2.0
					logging.info("transfer coin[%s->%s], num = %f", 
								sellExchangeCoinAmount, 
								buyExchangeCoinAmount,
								balanceTransferAmount)
					tradeAmount = min(tradeAmount, self._floor(balanceTransferAmount))
				logging.info("tradeAmount = %f, ", tradeAmount)

				#计算各种费用
				buyValue = askPrice * tradeAmount
				sellValue = bidPrice * tradeAmount
				tradeCost = self.exchanges[buyExchangeName].calculateTradeFee(currencyPair, tradeAmount, askPrice) + \
							 self.exchanges[sellExchangeName].calculateTradeFee(currencyPair, tradeAmount, bidPrice)
				withdrawCost = self.exchanges[buyExchangeName].calculateWithdrawFee(currency, tradeAmount) * bidPrice

				#计算收益
				# alphaFlat = sellValue - buyValue - withdrawCost - tradeCost
				alphaFlat = sellValue - buyValue - tradeCost
				alpha = (alphaFlat) / buyValue
				if alpha >= (gainTarget): #发现套利机会
					logging.info("%s[ask %.6f(%.6f)], %s[bid %.6f(%.6f)](%s->%s)arbitrage!!!!"+
						"buyValue=%.2f, sellValue=%.2f, tradeCost=%.2f, withdrawCost=%.2f, alphaFlat=%.2f, alpha = %f",
						buyExchangeName, askPrice, askAmount, sellExchangeName, bidPrice, bidAmount,
						buyExchangeName, sellExchangeName, buyValue, sellValue, tradeCost, withdrawCost, alphaFlat, alpha)
					(orderSuccess, buyOrderId, sellOrderId) = await self.doArbitrageOrder(currencyPair = currencyPair, 
																						buyExchangeName = buyExchangeName,
																						buyPrice = askPrice,
																						buyAmount = tradeAmount,
																						sellExchangeName = sellExchangeName,
																						sellPrice = bidPrice,
																						sellAmount = tradeAmount)
					#流水日志
					water = {"time": datetime.now(),
							 "buyExchange": buyExchangeName,
							 "sellExchange": sellExchangeName,
							 "amount": tradeAmount,
							 "buyPrice": askPrice,
							 "sellPrice": bidPrice,
							 "buyOrderId": buyOrderId,
							 "sellOrderId": sellOrderId,
							 "tradeCost": tradeCost,
							 "alphaFlat": alphaFlat,
							 "alpha": alpha}
					waterLogger.info("%s", water)
					return True
				else:
					logging.info("%s[ask %.6f(%.6f)], %s[bid %.6f(%.6f)](%s->%s)"+
						"buyValue=%.2f, sellValue=%.2f, tradeCost=%.2f, withdrawCost=%.2f, alphaFlat=%.2f, alpha = %f",
						buyExchangeName, askPrice, askAmount, sellExchangeName, bidPrice, bidAmount,
						buyExchangeName, sellExchangeName, buyValue, sellValue, tradeCost, withdrawCost, alphaFlat, alpha)

		return False

	async def arbitrage(self, currencyPair):
		exchangeNames = list(self.exchanges.keys())
		i = 0
		for i in range(len(exchangeNames)):
			exchangeAName = exchangeNames[i]
			j = i + 1
			while j < len(exchangeNames):
				exchangeBName = exchangeNames[j]

				#先update账户信息
				await asyncio.gather(self.exchanges[exchangeAName].updateAccountInfo(),
									 self.exchanges[exchangeBName].updateAccountInfo())

				(exchangeAQoutes, exchangeBQoutes) = await asyncio.gather(self.exchanges[exchangeAName].getQuotes(currencyPair),
																		  self.exchanges[exchangeBName].getQuotes(currencyPair))
				# logging.debug("%s->%s", exchangeAName, exchangeAQoutes)
				# logging.debug("%s->%s", exchangeBName, exchangeBQoutes)
				isArbitrage = await self.checkEntryAndArbitrage(currencyPair = currencyPair, 
											buyExchangeName = exchangeAName,
											askItems = exchangeAQoutes.getAsks(),
											sellExchangeName = exchangeBName,
											bidItems = exchangeBQoutes.getBids())
				if not isArbitrage:
					await self.checkEntryAndArbitrage(currencyPair = currencyPair,
												buyExchangeName = exchangeBName,
												askItems = exchangeBQoutes.getAsks(),
												sellExchangeName = exchangeAName,
												bidItems = exchangeAQoutes.getBids())
				j += 1

	async def run(self, currencyPair):
		prev_check_time = datetime.now()
		interval = self.config['arbitrage']['check_interval_second']
		while True:
			tick = datetime.now()
			elapse = (tick - prev_check_time).total_seconds()
			if (elapse < interval):
				time.sleep(interval - elapse)
			else:
				try:
					#arbitrage
					await self.arbitrage(currencyPair)
				except asyncio.TimeoutError as e:
					logging.error("http timeout, %s", e)
				except Exception as e:
					logging.error("%s",e)
					ex_type, ex, tb = sys.exc_info()
					traceback.print_tb(tb)

				prev_check_time = datetime.now()
