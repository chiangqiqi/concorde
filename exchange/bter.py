# -*- coding: utf-8 -*-
import logging

from lib.bter.client import Client as BterClient, get_api_path
from finance.currency import Currency, CurrencyPair
from finance.order import OrderState, OrderDirection, Order, ORDER_ID_FILLED_IMMEDIATELY
from finance.quotes import Quotes, OrderBookItem
from .exchange import ExchangeBase, Fee
from .exception import *
from .utils import get_order_book_item, _floor

class Exchange(ExchangeBase):
    __currency_map = {
        Currency.CNY: "CNY",
        Currency.BTC: "BTC",
        Currency.LTC: "LTC",
        Currency.ETC: "ETC",
        Currency.ETH: "ETH",
        Currency.EOS: "EOS",
        Currency.ZEC: "ZEC",
        Currency.BTS: "BTS",
        Currency.XRP: "XRP",
        Currency.NXT: "NXT",
        Currency.QTUM: "QTUM"
    }
    __currency_pair_map = {
        CurrencyPair.BTC_CNY: "btc_cny",
        CurrencyPair.LTC_CNY: "ltc_cny",
        CurrencyPair.ETC_CNY: "etc_cny",
        CurrencyPair.ETH_CNY: "eth_cny",
        CurrencyPair.EOS_CNY: "eos_cny",
        CurrencyPair.ZEC_CNY: "zec_cny",
        CurrencyPair.BTS_CNY: "bts_cny",
        CurrencyPair.XRP_CNY: "xrp_cny",
        CurrencyPair.NXT_CNY: "nxt_cny",
        CurrencyPair.QTUM_CNY: "qtum_cny"
    }
    TradeFee = {
        CurrencyPair.ETC_CNY: Fee(0.001, Fee.FeeTypes.PERC),
        CurrencyPair.ZEC_CNY: Fee(0.001, Fee.FeeTypes.PERC),
        CurrencyPair.BTS_CNY: Fee(0.0012, Fee.FeeTypes.PERC),
        CurrencyPair.XRP_CNY: Fee(0.0012, Fee.FeeTypes.PERC),
    }
    WithdrawFee = {
            Currency.ETC: Fee(0.01, Fee.FeeTypes.FIX),
            Currency.ZEC: Fee(0.0006, Fee.FeeTypes.FIX),
            Currency.BTS: Fee(0.01, Fee.FeeTypes.MIX, mix_fee2 = 1),
    }
    default_trade_fee = Fee(0.0012, Fee.FeeTypes.PERC)
    trade_type_buy = "buy"
    trade_type_sell = "sell"

    def __init__(self, config):
        super().__init__(config)
        self.client = BterClient(config['access_key'], config['secret_key'])

    async def getAccountInfo(self):
        resp =  await self.client.post(get_api_path('balances'))
        if str(resp['result']).lower() != 'true':
            raise ApiErrorException(resp['code'], resp['message'])
        resp_balances = resp['available']
        balances = {}
        __inverted_currency_map = {v:k for (k,v) in self.__currency_map.items()}
        for currency_str in resp_balances:
            if currency_str in __inverted_currency_map:
                currency = __inverted_currency_map[currency_str]
                balances.update({currency: float(resp_balances[currency_str])})
        return {"balances": balances}


    async def getQuotes(self, currencyPair):
        resp =  await self.client.get(get_api_path('depth')%self.__currency_pair_map[currencyPair])
        if str(resp['result']).lower() != 'true':
            raise ApiErrorException(resp['code'], resp['message'])

        bids = list(map(get_order_book_item, resp['bids']))
        asks = list(map(get_order_book_item, resp['asks']))
        quotes = Quotes(bids = bids, asks = asks)
        logging.debug("bter quotes: %s", quotes)
        return quotes

    async def getCurrencyAddressAsync(self, currency):
        cur = self.__currency_map[currency]
        resp = await self.client.post(get_api_path('deposite_address'), {'currency': cur})
        if str(resp['result']).lower() != 'true':
            raise ApiErrorException(resp['code'], resp['message'])
        return resp['addr']

    async def tradeAsync(self, currencyPair, amount, price, action):
        logging.debug("bter buy %s, amount %s, price %s", currencyPair, amount, price)
        path = get_api_path(action)
        resp = await self.client.post(path,
                                      {'currencyPair': self.__currency_pair_map[currencyPair],
                                       'amount': amount,
                                       'rate': price})
        if str(resp['result']).lower() != 'true':
            raise ApiErrorException(resp['code'], resp['message'])
        return resp['orderNumber']

    async def cancelOrderAsync(self, currencyPair, id):
        logging.debug("bter cancel order id %s, currencyPair %s", id, currencyPair)
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
