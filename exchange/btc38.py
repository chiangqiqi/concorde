# -*- coding: utf-8 -*-

from lib.btc38.client import Client as Client
from .currency import Currency, CurrencyPair
from .order import OrderState, OrderDirection, Order, ORDER_ID_FILLED_IMMEDIATELY
from .exchange import ExchangeBase, Fee
from .quotes import Quotes, OrderBookItem
from .exception import *
import logging

BTC38TradeFee = {
	CurrencyPair.BTS_CNY: Fee(0.001, Fee.FeeTypes.PERC),
}

BTC38WithdrawFee = {
	Currency.BTS: Fee(0.01, Fee.FeeTypes.MIX, mix_fee2 = 1),
}


OK_CODE = 1000
class Exchange(ExchangeBase):
	__currency_map = {
		Currency.CNY: "cny",
		Currency.BTC: "btc",
		Currency.LTC: "ltc",
		Currency.BTS: "bts",
	}
	__currency_pair_map = {
		CurrencyPair.BTC_CNY: "btc_cny",
		CurrencyPair.LTC_CNY: "ltc_cny",
		CurrencyPair.BTS_CNY: "bts_cny",
	}

	__trade_type_buy = 1
	__trade_type_sell = 2

	__order_status_open = 0 #待成交
	__order_status_cancelled = 1
	__order_status_filled = 2
	__order_status_paritially_filled = 3

	def __init__(self, config):
		super().__init__(config)
		self.client = Client(config['access_key'], config['secret_key'], config['user_id'])

	def calculateTradeFee(self, currencyPair, amount, price):
		return BTC38TradeFee[currencyPair].calculate_fee(amount * price)

	def calculateWithdrawFee(self, currency, amount):
		return BTC38WithdrawFee[currency].calculate_fee(amount)

	async def getAccountInfo(self):
		resp =  await self.client.post('balances')
		if 'cny_balance' not in resp:
			raise ApiErrorException("", resp)
		resp_balances = resp
		balances = {}
		for (currency, currency_str) in self.__currency_map.items():
			if currency_str + "_balance" in resp_balances:
				balances.update({currency: float(resp_balances[currency_str + "_balance"])})
		return {"balances": balances}

	async def getQuotes(self, currencyPair, size = 50):
		(c, mk_type) = self.__currency_pair_map[currencyPair].split("_")
		resp =  await self.client.get('depth', {'c': c, 'mk_type': mk_type})
		if 'bids' not in resp:
			raise ApiErrorException("", resp)
		bids = list(map(lambda x: OrderBookItem(price = float(x[0]), amount = float(x[1])), resp['bids']))
		asks = list(map(lambda x: OrderBookItem(price = float(x[0]), amount = float(x[1])), resp['asks']))
		quotes = Quotes(bids = bids, asks = asks)
		logging.debug("btc38 quotes: %s", quotes)
		return quotes

	async def getCashAsync(self):
		info = await self.getAccountInfo()
		return info['balances'][Currency.CNY]

	async def getCurrencyAmountAsync(self, currency):
		info = await self.getAccountInfo()
		return info['balances'][currency]

	async def getCurrencyAddressAsync(self, currency):
		raise NotImplementedError("btc38 do not have getCurrencyAddressAsync api")

	async def buyAsync(self, currencyPair, amount, price):
		logging.debug("btc38 buy %s, amount %s, price %s", currencyPair, amount, price)
		(c, mk_type) = self.__currency_pair_map[currencyPair].split("_")
		resp =  await self.client.post('order', {'coinname': c,
												'mk_type': mk_type,
										   		'amount': amount,
										   		'price': price,
										   		'type': self.__trade_type_buy})
		retAndId = resp.split('|')
		result = retAndId[0]
		id = ORDER_ID_FILLED_IMMEDIATELY
		if len(retAndId) > 1:
			id = retAndId[1]
		if result != "succ":
			raise ApiErrorException('', resp)
		return id

	async def sellAsync(self, currencyPair, amount, price):
		logging.debug("btc38 sell %s, amount %s, price %s", currencyPair, amount, price)
		(c, mk_type) = self.__currency_pair_map[currencyPair].split("_")
		resp =  await self.client.post('order', {'coinname': c,
												'mk_type': mk_type,
										   		'amount': amount,
										   		'price': price,
										   		'type': self.__trade_type_sell})
		retAndId = resp.split('|')
		result = retAndId[0]
		id = ORDER_ID_FILLED_IMMEDIATELY
		if len(retAndId) > 1:
			id = retAndId[1]
		if result != "succ":
			raise ApiErrorException('', resp)
		return id

	async def cancelOrderAsync(self, currencyPair, id):
		logging.debug("btc38 cancel order id %d, currencyPair %s", id, currencyPair)
		(c, mk_type) = self.__currency_pair_map[currencyPair].split("_")
		resp =  await self.client.post('cancelOrder', {'mk_type': mk_type,
													   'order_id': id})
		if resp != "succ":
			raise ApiErrorException('', resp)
		return True

	def _json_to_order(self, currencyPair, orderJs):
		id = orderJs['id']
		tradeDate = orderJs['time']
		if int(orderJs['type']) == self.__trade_type_buy:
			buyOrSell = OrderDirection.BUY
		else:
			buyOrSell = OrderDirection.SELL
		price = float(orderJs['price'])
		amount = float(orderJs['amount'])
		filledPrice = None
		filledAmount = None
		fee = None
		state = OrderState.INITIAL

		return Order(currencyPair = currencyPair,
					 id = id,
					 buyOrSell  = buyOrSell,
					 price = price,
					 amount = amount,
					 filledPrice = filledPrice,
					 filledAmount = filledAmount,
					 fee = fee,
					 state = state,
					 tradeDate = tradeDate)


	async def getOrderAsync(self, currencyPair, id):
		raise NotImplementedError("btc38 do not have getOrderAsync api")

	async def getOpenOrdersAsync(self, currencyPair, params = {}):
		(c, mk_type) = self.__currency_pair_map[currencyPair].split("_")
		resp =  await self.client.post('openOrders', {'mk_type': mk_type, 'coinname': c})
		if resp == 'no_order':
			resp = []
		if not isinstance(resp, list):
			raise ApiErrorException(resp)
		orders = list(map(lambda orderJs: self._json_to_order(currencyPair, orderJs), resp))
		return orders
