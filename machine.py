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
from exchange.order import ORDER_ID_FILLED_IMMEDIATELY
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

	# return order_id if successes, None if order failed
	async def orderWithRetry(self, currencyPair, exchangeName, price, amount, isSell, maxRetryNum):
		logging.debug("orderWithRetry: currencyPair %s, exchangeName %s, price %s, amount %s, isSell %s, maxRetryNum %s",
					currencyPair, exchangeName, price, amount, isSell, maxRetryNum)
		if isSell:
			orderFunc = self.exchanges[exchangeName].sellAsync
		else:
			orderFunc = self.exchanges[exchangeName].buyAsync

		orderSuccess = False
		orderId = None
		for i in range(maxRetryNum):
			try:
				orderId = await orderFunc(currencyPair, price = price, amount = amount)
				orderSuccess = True
				break
			except Exception as e:
				logging.warn("%s order in exchange %s(%f,%f) failed: %s, will try again[%d/%d]",
							'sell' if isSell else 'buy',
							exchangeName, price, amount, e, i+1, maxRetryNum)
		if orderSuccess:
			logging.info("%s order in exchange %s(%f,%f) success", 'sell' if isSell else 'buy', exchangeName, price, amount)
			return orderId
		else:
			logging.warn("%s order in exchange %s(%f,%f) failed, reach maximum retry.",
						'sell' if isSell else 'buy',
						exchangeName, price, amount)
			return None

	# return True if successes, False if failed
	async def cancelOrderWithRetry(self, currencyPair, exchangeName, id, maxRetryNum):
		logging.debug("cancelOrderWithRetry: currencyPair %s, exchangeName %s, id %s, maxRetryNum %s",
					 currencyPair, exchangeName, id, maxRetryNum)
		cancelSuccess = False
		for i in range(maxRetryNum):
			try:
				cancelSuccess = await self.exchanges[exchangeName].cancelOrderAsync(currencyPair = currencyPair, id = id)
				break
			except Exception as e:
				logging.warn("cancel order in exchange %s(order_id: %s) failed: %s, will try again[%d/%d]",
							exchangeName, id, e, i+1, maxRetryNum)
		if not cancelSuccess:
			logging.warn("cancel order in exchange %s(order_id: %s) failed, reach maximum retry.",
						exchangeName, id)
			return False
		return True

	# # return True if both order success
	# async def doArbitrageOrder(self, 
	# 						 currencyPair, 
	# 						 buyExchangeName, 
	# 						 buyPrice, 
	# 						 buyAmount,
	# 						 sellExchangeName,
	# 						 sellPrice,
	# 						 sellAmount):
	# 	logging.info("doArbitrageOrder: [%s] buy price %f, buy amount %f, [%s] sell price %f, sell amount %f",
	# 				buyExchangeName, buyPrice, buyAmount, sellExchangeName, sellPrice, sellAmount)
	# 	(buyOrderId, sellOrderId) = await asyncio.gather(
	# 		self.exchanges[buyExchangeName].buyAsync(currencyPair, price = buyPrice, amount = buyAmount),
	# 		self.exchanges[sellExchangeName].sellAsync(currencyPair, price = sellPrice, amount = sellAmount),
	# 		return_exceptions = True)
	# 	if issubclass(type(buyOrderId), Exception) and issubclass(type(sellOrderId), Exception):
	# 		logging.warn("place buy order to %s fail[%s] and place sell order to %s fail[%s], return to checkEntryAndArbitrage",
	# 				buyExchangeName, buyOrderId, sellExchangeName, sellOrderId)
	# 		return (False, None, None)

	# 	if issubclass(type(buyOrderId), Exception):
	# 		maxOrderRetry = filter(lambda x: x['name'] == buyExchangeName, self.config['exchange']).__next__()['max_order_retry']
	# 		tryTimes = 1
	# 		while issubclass(type(buyOrderId), Exception):
	# 			logging.warn("place buy order to %s fail[%s], will try again[%d/%d]",
	# 					buyExchangeName, buyOrderId, tryTimes, maxOrderRetry)
	# 			tryTimes += 1
	# 			if tryTimes > 3:
	# 				logging.warn("place buy order to %s fail[%s], will try again[%d/%d]",
	# 						buyExchangeName, buyOrderId, tryTimes, maxOrderRetry)
	# 				break
	# 			else:
	# 				buyOrderId = await self.exchanges[buyExchangeName].buyAsync(currencyPair, price = buyPrice, amount = buyAmount)

	# 	if issubclass(type(sellOrderId), Exception):
	# 		maxOrderRetry = filter(lambda x: x['name'] == sellExchangeName, self.config['exchange']).__next__()['max_order_retry']
	# 		tryTimes = 1
	# 		while issubclass(type(sellOrderId), Exception):
	# 			logging.warn("place sell order to %s fail[%s], will try again[%d/%d]",
	# 					sellExchangeName, sellOrderId, tryTimes, maxOrderRetry)
	# 			tryTimes += 1
	# 			if tryTimes > 3:
	# 				logging.warn("place sell order to %s fail[%s], will try again[%d/%d]",
	# 						sellExchangeName, sellOrderId, tryTimes, maxOrderRetry)
	# 				break
	# 			else:
	# 				sellOrderId = await self.exchanges[sellExchangeName].sellAsync(currencyPair, price = sellPrice, amount = sellAmount)

	# 	# just log
	# 	if not issubclass(type(buyOrderId), Exception):
	# 		logging.info("place buy order to %s success, price %f, amount %f, id %s",
	# 				buyExchangeName, buyPrice, buyAmount, buyOrderId)
	# 	if not issubclass(type(sellOrderId), Exception):
	# 		logging.info("place sell order to %s success, price %f, amount %f, id %s",
	# 				sellExchangeName, sellPrice, sellAmount, sellOrderId)
	# 	if not issubclass(type(buyOrderId), Exception) and not issubclass(type(sellOrderId), Exception):
	# 		return (True, buyOrderId, sellOrderId)
	# 	else:
	# 		return (False, None, None)


	async def doTrade(self, 
					  currencyPair, 
					  buyExchangeName, 
					  buyPrice, 
					  buyAmount,
					  sellExchangeName,
					  sellPrice,
					  sellAmount,
					  tradeCost,
					  alphaFlat,
					  alpha):
		logging.info("doTrade: [%s] buy price %f, buy amount %f, [%s] sell price %f, sell amount %f",
					buyExchangeName, buyPrice, buyAmount, sellExchangeName, sellPrice, sellAmount)

		assert(buyAmount == sellAmount)
		# get retry config
		buyMaxOrderRetry = filter(lambda x: x['name'] == buyExchangeName, 
								self.config['exchange']).__next__()['max_order_retry']
		buyMaxCancelOrderRetry = filter(lambda x: x['name'] == buyExchangeName, 
								self.config['exchange']).__next__()['max_cancel_order_retry']
		sellMaxOrderRetry = filter(lambda x: x['name'] == sellExchangeName, 
								self.config['exchange']).__next__()['max_order_retry']
		sellMaxCancelOrderRetry = filter(lambda x: x['name'] == sellExchangeName, 
								self.config['exchange']).__next__()['max_cancel_order_retry']

		# make order
		(buyOrderId, sellOrderId) = await asyncio.gather(
			self.orderWithRetry(currencyPair = currencyPair, exchangeName = buyExchangeName, price = buyPrice, 
								amount = buyAmount, isSell = False, maxRetryNum = buyMaxOrderRetry),
			self.orderWithRetry(currencyPair = currencyPair, exchangeName = sellExchangeName, price = sellPrice, 
								amount = sellAmount, isSell = True, maxRetryNum = sellMaxOrderRetry))

		# 两者下单都失败，记录日志
		if buyOrderId is None and sellOrderId is None:
			logging.warn("place buy order to %s fail and place sell order to %s fail",
						 buyExchangeName, sellExchangeName)
			return

		# 两者下单都成功
		if buyOrderId is not None and sellOrderId is not None:
			logging.info("place order to %s(buyPrice: %s, buyAmount: %s) and %s(sellPrice: %s, sellAmount: %s) success",
						 buyExchangeName, buyPrice, buyAmount, sellExchangeName, sellPrice, sellAmount)
			# TODO: wait order to be fill
			
			#流水日志
			water = {"time": datetime.now(),
					 "buyExchange": buyExchangeName,
					 "sellExchange": sellExchangeName,
					 "buyPrice": buyPrice,
					 "buyAmount": buyAmount,
					 "buyOrderId": buyOrderId,
					 "buyOrderState": "OpenOrFilled",
					 "sellPrice": sellPrice,
					 "sellAmount": sellAmount,
					 "sellOrderId": sellOrderId,
					 "sellOrderState": "OpenOrFilled",
					 "tradeCost": tradeCost,
					 "alphaFlat": alphaFlat,
					 "alpha": alpha}
			waterLogger.info("%s", water)
			return

		# cancel order if exist failed
		if buyOrderId is not None:
			logging.warn("doTrade place order in %s success but failed in %s", buyExchangeName, sellExchangeName)
			if buyOrderId != ORDER_ID_FILLED_IMMEDIATELY:
				cancelSucess = await self.cancelOrderWithRetry(currencyPair, buyExchangeName, buyOrderId, buyMaxCancelOrderRetry)
			#TODO: 报警，有open orders存在
			#流水日志
			water = {"time": datetime.now(),
					 "buyExchange": buyExchangeName,
					 "sellExchange": sellExchangeName,
					 "buyPrice": buyPrice,
					 "buyAmount": buyAmount,
					 "buyOrderId": buyOrderId,
					 "buyOrderState": "PartiallyFilledOrFilledOrCancelled",
					 "sellPrice": sellPrice,
					 "sellAmount": sellAmount,
					 "sellOrderId": sellOrderId,
					 "sellOrderState": "Failed",
					 "tradeCost": tradeCost,
					 "alphaFlat": alphaFlat,
					 "alpha": alpha}
			waterLogger.info("%s", water)
		if sellOrderId is not None:
			logging.warn("doTrade place order in %s success but failed in %s", sellExchangeName, buyExchangeName)
			if buyOrderId != ORDER_ID_FILLED_IMMEDIATELY: 
				cancelSucess = await self.cancelOrderWithRetry(currencyPair, sellExchangeName, sellOrderId, sellMaxCancelOrderRetry)
			#TODO: 报警，有open orders存在
			#流水日志
			water = {"time": datetime.now(),
					 "buyExchange": buyExchangeName,
					 "sellExchange": sellExchangeName,
					 "buyPrice": buyPrice,
					 "buyAmount": buyAmount,
					 "buyOrderId": buyOrderId,
					 "buyOrderState": "Failed",
					 "sellPrice": sellPrice,
					 "sellAmount": sellAmount,
					 "sellOrderId": sellOrderId,
					 "sellOrderState": "PartiallyFilledOrFilledOrCancelled",
					 "tradeCost": tradeCost,
					 "alphaFlat": alphaFlat,
					 "alpha": alpha}
			waterLogger.info("%s", water)

	async def notEnoughBalanceToTrade(self, currencyPair, buyExchangeName, buyPrice, sellExchangeName):
		currency = currencyPair2Currency(currencyPair)
		coinTradeMinimum = self.config['arbitrage']['coin_trade_minimum'][currencyPair]

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
			return True
		
		#校验有没足够的的钱买币
		if buyPrice * coinTradeMinimum > buyExchangeCash:
			logging.warn("%s do not have enough money to buy, only have %f, coin_trade_minimum is %f, min ask price is %f",
						buyExchangeName, buyExchangeCash, coinTradeMinimum, buyPrice)
			return True
		return False
		
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
		allowSlippagePerc = self.config['arbitrage'][currencyPair]['allow_slippage_perc']

		#校验是否有足够的钱或币进行交易
		if await self.notEnoughBalanceToTrade(currencyPair, buyExchangeName, askItems[0].price, sellExchangeName):
			return False
		
		#决定套利收获
		buyExchangeCash = self.exchanges[buyExchangeName].accountInfo['balances'][Currency.CNY]
		sellExchangeCash = self.exchanges[sellExchangeName].accountInfo['balances'][Currency.CNY]
		buyExchangeCoinAmount = self.exchanges[buyExchangeName].accountInfo['balances'][currency]
		sellExchangeCoinAmount = self.exchanges[sellExchangeName].accountInfo['balances'][currency]
		gainTarget = self.determineGainTarget(buyExchangeCoinAmount, sellExchangeCoinAmount)

		#判断是否能够套利
		for bidItem in bidItems:
			bidPrice = bidItem.price
			logging.info("adjust bidPrice, allowSlippagePerc is %.6f, bidPrice %f, adjBidPrice %f",
						allowSlippagePerc, bidPrice, bidPrice * (1.0 - allowSlippagePerc))
			bidPrice = bidPrice * (1.0 - allowSlippagePerc)
			bidAmount = bidItem.amount
			if (bidPrice <= askItems[0].price):
				logging.info("%s[ask %.6f(%.6f)], %s[bid %.6f(%.6f)], no alpha",
							buyExchangeName, askItems[0].price, askItems[0].amount,
							sellExchangeName, bidPrice, bidAmount)
				break
			for askItem in askItems:
				askPrice = askItem.price
				logging.info("adjust askPrice, allowSlippagePerc is %.6f, askPrice %f, adjAskPrice %f",
							allowSlippagePerc, askPrice, askPrice * (1.0 + allowSlippagePerc))
				askPrice = askPrice * (1.0 + allowSlippagePerc)
				askAmount = askItem.amount

				# no alpha
				if (bidPrice <= askPrice):
					logging.info("%s[ask %.6f(%.6f)], %s[bid %.6f(%.6f)] no alpha",
								buyExchangeName, askPrice, askAmount,
								sellExchangeName, bidPrice, bidAmount)
					break

				#如果币数太少，不交易
				if min(bidAmount, askAmount) < coinTradeMinimum:
					logging.info("min(bidAmount[%f], askAmount[%f]) < coinTradeMinimum[%f], no trade",
								bidAmount, askAmount, coinTradeMinimum)
					continue

				#决定卖币数量
				#卖币数量 = min(bidAmount, askAmount, sellExchangeCoinAmount, avaliableBuyAmount, coinTradeMaximum, balanceTransferAmount)
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
					await self.doTrade(currencyPair = currencyPair, 
									buyExchangeName = buyExchangeName,
									buyPrice = askPrice,
									buyAmount = tradeAmount,
									sellExchangeName = sellExchangeName,
									sellPrice = bidPrice,
									sellAmount = tradeAmount,
									tradeCost = tradeCost,
									alphaFlat = alphaFlat,
									alpha = alpha)
					return True
				else:
					logging.info("%s[ask %.6f(%.6f)], %s[bid %.6f(%.6f)](%s->%s)"+
						"buyValue=%.2f, sellValue=%.2f, tradeCost=%.2f, withdrawCost=%.2f, alphaFlat=%.2f, alpha = %f",
						buyExchangeName, askPrice, askAmount, sellExchangeName, bidPrice, bidAmount,
						buyExchangeName, sellExchangeName, buyValue, sellValue, tradeCost, withdrawCost, alphaFlat, alpha)

		return False

	async def arbitrage(self, currencyPair):
		exchangeNames = self.config['arbitrage'][str(currencyPair)]['arbitrage_exchanges']
		logging.info("arbitrage %s, in exchanges %s", currencyPair, exchangeNames)
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
