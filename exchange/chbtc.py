# -*- coding: utf-8 -*-

from lib.chbtc.client import Client as Client
from finance.currency import Currency, CurrencyPair
from finance.order import OrderState, OrderDirection, Order, ORDER_ID_FILLED_IMMEDIATELY
from finance.quotes import Quotes, OrderBookItem
from .exchange import ExchangeBase, Fee
from .exception import *
import logging

CHBTCTradeFee = {
	CurrencyPair.ETC_CNY: Fee(0.0005, Fee.FeeTypes.PERC),
        CurrencyPair.BTS_CNY: Fee(0.001, Fee.FeeTypes.PERC),
}

CHBTCWithdrawFee = {
	Currency.ETC: Fee(0.01, Fee.FeeTypes.FIX),
}


OK_CODE = 1000
class Exchange(ExchangeBase):
	__currency_map = {
		Currency.CNY: "CNY",
		Currency.BTC: "btc",
		Currency.LTC: "ltc",
		Currency.ETC: "etc",
		Currency.ETH: "eth",
        Currency.BTS: "BTS"
	}
	__currency_pair_map = {
		CurrencyPair.BTC_CNY: "btc_cny",
		CurrencyPair.LTC_CNY: "ltc_cny",
		CurrencyPair.ETC_CNY: "etc_cny",
		CurrencyPair.ETH_CNY: "eth_cny",
        CurrencyPair.BTS_CNY: "bts_cny"
	}

	__trade_type_buy = 1
	__trade_type_sell = 0

	__order_status_open = 0 #待成交
	__order_status_cancelled = 1
	__order_status_filled = 2
	__order_status_paritially_filled = 3

	def __init__(self, config):
		super().__init__(config)
		self.client = Client(config['access_key'], config['secret_key'])

	def calculateTradeFee(self, currencyPair, amount, price):
		return CHBTCTradeFee[currencyPair].calculate_fee(amount * price)

	def calculateWithdrawFee(self, currency, amount):
		return CHBTCWithdrawFee[currency].calculate_fee(amount)

	async def getAccountInfo(self):
		resp =  await self.client.get('getAccountInfo')
		if 'code' in resp and resp['code'] != OK_CODE:
			raise ApiErrorException(resp['code'], resp['message'])
		resp_balances = resp['result']['balance']
		balances = {}
		__inverted_currency_map = {v.upper():k for (k,v) in self.__currency_map.items()}
		for currency_str in resp_balances:
			if currency_str in __inverted_currency_map:
				currency = __inverted_currency_map[currency_str]
				balances.update({currency: float(resp_balances[currency_str]['amount'])})
		return {"balances": balances}

	async def getQuotes(self, currencyPair, size = 50):
		resp =  await self.client.get('depth', {'currency': self.__currency_pair_map[currencyPair], 'size': size})
		if 'code' in resp and resp['code'] != OK_CODE:
			raise ApiErrorException(resp['code'], resp['message'])
		bids = list(map(lambda x: OrderBookItem(price = float(x[0]), amount = float(x[1])), resp['bids']))
		asks = list(map(lambda x: OrderBookItem(price = float(x[0]), amount = float(x[1])), resp['asks']))
		quotes = Quotes(bids = bids, asks = asks)
		logging.debug("chbtc quotes: %s", quotes)
		return quotes

	async def getCashAsync(self):
		resp =  await self.client.get('getAccountInfo')
		if 'code' in resp and resp['code'] != OK_CODE:
			raise ApiErrorException(resp['code'], resp['message'])
		return round(float(resp['result']['balance']['CNY']['amount']), 2)

	async def getCurrencyAmountAsync(self, currency):
		resp =  await self.client.get('getAccountInfo')
		if 'code' in resp and resp['code'] != OK_CODE:
			raise ApiErrorException(resp['code'], resp['message'])
		cur = self.__currency_map[currency].upper()
		if cur not in resp['result']['balance']:
			raise CurrencyNotExistException(currency)
		return float(resp['result']['balance'][cur]['amount'])

	async def getCurrencyAddressAsync(self, currency):
		cur = self.__currency_map[currency]
		resp = await self.client.get('getUserAddress', {'currency': cur})
		if 'code' in resp and resp['code'] != OK_CODE:
			raise ApiErrorException(resp['code'], resp['message'])
		return resp['message']['datas']['key']

	async def buyAsync(self, currencyPair, amount, price):
		logging.debug("chbtc buy %s, amount %s, price %s", currencyPair, amount, price)
		resp =  await self.client.get('order', {'currency': self.__currency_pair_map[currencyPair],
										   'amount': amount,
										   'price': price,
										   'tradeType': self.__trade_type_buy})
		if 'code' in resp and resp['code'] != OK_CODE:
			raise ApiErrorException(resp['code'], resp['message'])
		return resp['id']

	async def sellAsync(self, currencyPair, amount, price):
		logging.debug("chbtc sell %s, amount %s, price %s", currencyPair, amount, price)
		resp =  await self.client.get('order', {'currency': self.__currency_pair_map[currencyPair],
										   'amount': amount,
										   'price': price,
										   'tradeType': self.__trade_type_sell})
		if 'code' in resp and resp['code'] != OK_CODE:
			raise ApiErrorException(resp['code'], resp['message'])
		return resp['id']

	async def cancelOrderAsync(self, currencyPair, id):
		logging.debug("chbtc cancel order id %s, currencyPair %s", id, currencyPair)
		resp =  await self.client.get('cancelOrder', {'currency': self.__currency_pair_map[currencyPair],
											  'id': id})
		if 'code' in resp and resp['code'] != OK_CODE:
			raise ApiErrorException(resp['code'], resp['message'])
		return True

	def _json_to_order(self, currencyPair, orderJs):
		id = orderJs['id']
		tradeDate = int(orderJs['trade_date'])
		if int(orderJs['type']) == self.__trade_type_buy:
			buyOrSell = OrderDirection.BUY
		else:
			buyOrSell = OrderDirection.SELL
		price = float(orderJs['price'])
		amount = float(orderJs['total_amount'])
		filledPrice = float(orderJs['trade_price'])
		filledAmount = float(orderJs['trade_amount'])
		fee = float(orderJs['fees'])
		orderJsState = int(orderJs['status'])
		if orderJsState == self.__order_status_open:
			state = OrderState.INITIAL
		elif orderJsState == self.__order_status_filled:
			state = OrderState.FILLED
		elif orderJsState == self.__order_status_paritially_filled:
			state = OrderState.PARTIALLY_FILLED
		else:
			state = OrderState.CANCELLED

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
		resp =  await self.client.get('getOrder', {'currency': self.__currency_pair_map[currencyPair],
											  'id': id})
		if 'code' in resp and resp['code'] != OK_CODE:
			raise ApiErrorException(resp['code'], resp['message'])

		order = self._json_to_order(currencyPair, resp)
		return order

	async def getOpenOrdersAsync(self, currencyPair, params = {}):
		new_params = params
		new_params.update({"currency": self.__currency_pair_map[currencyPair]})
		resp =  await self.client.get('getUnfinishedOrdersIgnoreTradeType', params)
		if 'code' in resp and resp['code'] != OK_CODE:
			raise ApiErrorException(resp['code'], resp['message'])
		orders = list(map(lambda orderJs: self._json_to_order(currencyPair, orderJs), resp))
		return orders
