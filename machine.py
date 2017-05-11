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
from exchange.order import OrderState, ORDER_ID_FILLED_IMMEDIATELY
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

	# return order state
	async def waitOrderToBeFilled(self, currencyPair, exchangeName, id, waitOrderFilledSecond):
		queryOrderStateIntervalMs = self.config['arbitrage']['query_order_state_interval_ms']
		if id == ORDER_ID_FILLED_IMMEDIATELY:
			return OrderState.FILLED

		state = OrderState.INITIAL
		end_time = time.time() + waitOrderFilledSecond
		while time.time() < end_time:
			order = await self.exchanges[exchangeName].getOrderAsync(currencyPair, id)
			state = order.state
			if order.state == OrderState.FILLED or order.state == OrderState.CANCELLED:
				break
			await asyncio.sleep(queryOrderStateIntervalMs/1000.)
		return state

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
		# waitSeconds config
		waitSeconds = self.config['arbitrage']['wait_order_filled_second']

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
			logging.info("now wait orders to be filled, wait %s seconds at max.", waitSeconds)
			(buyOrderState, sellOrderState) = await asyncio.gather(
				self.waitOrderToBeFilled(currencyPair, buyExchangeName, buyOrderId, waitSeconds),
				self.waitOrderToBeFilled(currencyPair, sellExchangeName, sellOrderId, waitSeconds))
			logging.info("buyOrderState %s, sellOrderState %s", buyOrderState, sellOrderState)

			buyOrderStateStr = str(buyOrderState)
			if buyOrderState == OrderState.INITIAL:
				buyOrderStateStr = "OPEN"
			sellOrderStateStr = str(sellOrderState)
			if sellOrderState == OrderState.INITIAL:
				sellOrderStateStr = "OPEN"

			if buyOrderState != OrderState.FILLED:
				logging.warn("buy order(%s) is not filled in exchange %s in %s seconds", 
					buyOrderId, buyExchangeName, waitSeconds)
			if buyOrderState != OrderState.FILLED:
				logging.warn("sell order(%s) is not filled in exchange %s in %s seconds", 
					sellOrderId, sellExchangeName, waitSeconds)
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
		
	async def testTransferCoin(self):
		return await self.transferCoin(CurrencyPair.BTS_CNY, "btc38", "yunbi", 10)

	# return True if submit transfer success, else False
	async def transferCoin(self, currencyPair, fromExchange, toExchange, amount):
		currency = currencyPair2Currency(currencyPair)
		logging.info("getting address of exchange %s for currency %s", toExchange, currency)
		address = await self.exchanges[toExchange].getCurrencyAddressAsync(currency = currency)
		exchangeWithdrawMemo = self.config['arbitrage'][currencyPair]['exchange_withdraw_memo']

		memo = 'rk_withdraw'
		if currency == Currency.BTS:
			memo = exchangeWithdrawMemo[toExchange]

		logging.info("calling exchange %s to transfer %d coin to exchange %s, address = %s, memo = %s", 
						fromExchange, amount, toExchange, address, memo)
		try:
			await self.exchanges[fromExchange].withdraw(currency = currency, amount = amount, address = address, memo = memo)
		except Exception as e:
			# TODO: 短信通知，如果提币失败的话
			logging.error("withdraw error: %s", e)
			return False

		return True

	# return True if arbitrage exist and order success else False
	async def checkEntryAndArbitrage(self, 
									currencyPair,
									buyExchangeName,
									askItems, 
									sellExchangeName,
									bidItems):
		currency = currencyPair2Currency(currencyPair)
		#config
		balanceRatio = self.config['arbitrage']['balance_ratio']
		coinTradeMinimum = self.config['arbitrage']['coin_trade_minimum'][currencyPair]
		coinTradeMaximum = self.config['arbitrage']['coin_trade_maximum'][currencyPair]
		allowSlippagePerc = self.config['arbitrage'][currencyPair]['allow_slippage_perc']
		usingWithdraw = self.config['arbitrage'][currencyPair]['using_withdraw']
		withdrawPerc = self.config['arbitrage'][currencyPair]['withdraw_perc']
		withdrawMinimum = self.config['arbitrage'][currencyPair]['withdraw_minimum']
		isExchangeWithdrawAllowed = self.config['arbitrage'][currencyPair]['exchange_withdraw_permission']
		logging.debug("usingWithdraw %s, withdrawPerc %s, withdrawMinimum %s, isExchangeWithdrawAllowed %s", 
			usingWithdraw, withdrawPerc, withdrawMinimum, isExchangeWithdrawAllowed)

		#account info
		buyExchangeCash = self.exchanges[buyExchangeName].accountInfo['balances'][Currency.CNY]
		sellExchangeCash = self.exchanges[sellExchangeName].accountInfo['balances'][Currency.CNY]
		buyExchangeCoinAmount = self.exchanges[buyExchangeName].accountInfo['balances'][currency]
		sellExchangeCoinAmount = self.exchanges[sellExchangeName].accountInfo['balances'][currency]

		#转币如果允许的话
		transferAmount = buyExchangeCoinAmount * withdrawPerc
		# if sellExchangeCoinAmount < coinTradeMinimum and \
		if True and \
		transferAmount >= withdrawMinimum and \
		isExchangeWithdrawAllowed[buyExchangeName]:
			logging.info("transfer %s %s from %s to %s", transferAmount, currency, buyExchangeName, sellExchangeName)
			await self.transferCoin(currencyPair = currencyPair, 
							  fromExchange = buyExchangeName, 
							  toExchange = sellExchangeName, 
							  amount = transferAmount)
			return

		#校验是否有足够的钱或币进行交易
		if await self.notEnoughBalanceToTrade(currencyPair, buyExchangeName, askItems[0].price, sellExchangeName):
			return False
		
		#决定套利收获
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
				if usingWithdraw:
					withdrawCost = self.exchanges[buyExchangeName].calculateWithdrawFee(currency, tradeAmount) * bidPrice
					withdrawCost += self.exchanges[sellExchangeName].calculateWithdrawFee(Currency.CNY, sellValue)

				#计算收益
				alphaFlat = sellValue - buyValue - tradeCost
				if usingWithdraw:
					alphaFlat -= withdrawCost
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
		prev_check_time = None
		interval = self.config['arbitrage']['check_interval_second']
		while True:
			tick = datetime.now()
			if prev_check_time is not None and (tick - prev_check_time).total_seconds() < interval:
				elapse = (tick - prev_check_time).total_seconds()
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
