# -*- coding: utf-8 -*-

from lib.yunbi.client import Client as YunbiClient, get_api_path
from .currency import Currency, CurrencyPair
from .order import OrderState, OrderDirection, Order
from .exchange import ExchangeBase, Fee
from .quotes import Quotes, OrderBookItem
from .exception import *
import logging

YunbiTradeFee = {
	CurrencyPair.ETC_CNY: Fee(0.001, Fee.FeeTypes.PERC),
	CurrencyPair.ZEC_CNY: Fee(0.001, Fee.FeeTypes.PERC),
	CurrencyPair.BTS_CNY: Fee(0.001, Fee.FeeTypes.PERC),
}

YunbiWithdrawFee = {
	Currency.ETC: Fee(0.01, Fee.FeeTypes.FIX),
	Currency.ZEC: Fee(0.0002, Fee.FeeTypes.FIX),
	Currency.BTS: Fee(10, Fee.FeeTypes.FIX),
}

class Exchange(ExchangeBase):
	__currency_map = {
		Currency.CNY: "cny",
		Currency.BTC: "btc",
		Currency.LTC: "ltc",
		Currency.ETC: "etc",
		Currency.ETH: "eth",
		Currency.ZEC: "zec",
		Currency.BTS: "bts",
	}
	__currency_pair_map = {
		CurrencyPair.BTC_CNY: "btccny",
		CurrencyPair.LTC_CNY: "ltccny",
		CurrencyPair.ETC_CNY: "etccny",
		CurrencyPair.ETH_CNY: "ethcny",
		CurrencyPair.ZEC_CNY: "zeccny",
		CurrencyPair.BTS_CNY: "btscny",
	}

	__trade_type_buy = "buy"
	__trade_type_sell = "sell"

	def __init__(self, config):
		super().__init__(config)
		self.client = YunbiClient(config['access_key'], config['secret_key'])

	def calculateTradeFee(self, currencyPair, amount, price):
		return YunbiTradeFee[currencyPair].calculate_fee(amount * price)

	def calculateWithdrawFee(self, currency, amount):
		return YunbiWithdrawFee[currency].calculate_fee(amount)

	async def getAccountInfo(self):
		resp =  await self.client.get(get_api_path('members'))
		if 'error' in resp:
			raise ApiErrorException(resp['error']['code'], resp['error']['message'])
		resp_balances = resp['accounts']
		balances = {}
		__inverted_currency_map = {v:k for (k,v) in self.__currency_map.items()}
		for item in resp_balances:
			if item['currency'] in __inverted_currency_map:
				currency = __inverted_currency_map[item['currency']]
				balances.update({currency: float(item['balance'])})
		return {"balances": balances}

	async def getQuotes(self, currencyPair):
		resp =  await self.client.get(get_api_path('depth'), {'market': self.__currency_pair_map[currencyPair]})
		if 'error' in resp:
			raise ApiErrorException(resp['error']['code'], resp['error']['message'])

		bids = list(map(lambda x: OrderBookItem(price = float(x[0]), amount = float(x[1])), resp['bids']))
		asks = list(map(lambda x: OrderBookItem(price = float(x[0]), amount = float(x[1])), resp['asks']))
		quotes = Quotes(bids = bids, asks = asks)
		logging.debug("yunbi quotes: %s", quotes)
		return quotes

	async def getCashAsync(self):
		info = await self.getAccountInfo()
		return info['balances'][Currency.CNY]

	async def getCurrencyAmountAsync(self, currency):
		info = await self.getAccountInfo()
		return info['balances'][currency]

	async def getCurrencyAddressAsync(self, currency):
		cur = self.__currency_map[currency]
		resp = await self.client.get(get_api_path('deposite_address'), {'currency': cur})
		if 'error' in resp:
			raise ApiErrorException(resp['error']['code'], resp['error']['message'])
		return resp['address']

	async def buyAsync(self, currencyPair, amount, price):

# #sell 10 dogecoins at price 0.01
# params = {'market': 'dogcny', 'side': 'sell', 'volume': 10, 'price': 0.01}
# res = client.post(get_api_path('orders'), params)
# print res

# #buy 10 dogecoins at price 0.001
# params = {'market': 'dogcny', 'side': 'buy', 'volume': 10, 'price': 0.001}
# res = client.post(get_api_path('orders'), params)

		logging.debug("yunbi buy %s, amount %s, price %s", currencyPair, amount, price)
		resp =  await self.client.post(get_api_path('orders'), {'market': self.__currency_pair_map[currencyPair],
																'volume': amount,
														   		'side': self.__trade_type_buy,
																'price': price})
		if 'error' in resp:
			(code, error_msg) = resp['error'].split(':')
			raise ApiErrorException(code, error_msg)

		return resp['orderNumber']

	async def sellAsync(self, currencyPair, amount, price):
		logging.debug("yunbi sell %s, amount %s, price %s", currencyPair, amount, price)
		resp =  await self.client.post(get_api_path('orders'), {'market': self.__currency_pair_map[currencyPair],
																'volume': amount,
														   		'side': self.__trade_type_sell,
																'price': price})
		if 'error' in resp:
			(code, error_msg) = resp['error'].split(':')
			raise ApiErrorException(code, error_msg)

		return resp['orderNumber']

	async def cancelOrderAsync(self, currencyPair, id):
		logging.debug("yunbi cancel order id %d, currencyPair %s", id, currencyPair)
		resp =  await self.client.post(get_api_path('cancelOrder'), {'currencyPair': self.__currency_pair_map[currencyPair],
										  'orderNumber': id})
		if str(resp['result']).lower() != 'true':
			raise ApiErrorException(resp['code'], resp['message'])
		return True

	def _json_to_order(self, currencyPair, orderJs):
		id = orderJs['orderNumber']
		tradeDate = int(orderJs['timestamp'])
		if orderJs['type'].lower() == 'buy':
			buyOrSell = OrderDirection.BUY
		else:
			buyOrSell = OrderDirection.SELL
		price = float(orderJs['initialRate'])
		amount = float(orderJs['initialAmount'])
		filledPrice = float(orderJs['filledRate'])
		filledAmount = float(orderJs['filledAmount'])
		if 'feeValue' in orderJs:
			fee = float(orderJs['feeValue'])
		else:
			fee = None
		if filledAmount == amount:
			state = OrderState.FILLED
		elif filledAmount > 0.0 and filledAmount < amount:
			state = OrderState.PARTIALLY_FILLED
		else:
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
		resp =  await self.client.post(get_api_path('getOrder'), {'currencyPair': self.__currency_pair_map[currencyPair],
											  'orderNumber': id})
		if str(resp['result']).lower() != 'true':
			raise ApiErrorException(resp['code'], resp['message'])

		order = self._json_to_order(currencyPair, resp['order'])
		return order

	async def getOpenOrdersAsync(self, currencyPair, params = {}):
		resp =  await self.client.post(get_api_path('openOrders'), {'currencyPair': self.__currency_pair_map[currencyPair]})
		if str(resp['result']).lower() != 'true':
			raise ApiErrorException(resp['code'], resp['message'])
		orders = list(map(lambda orderJs: self._json_to_order(currencyPair, orderJs), resp['orders']))
		return orders