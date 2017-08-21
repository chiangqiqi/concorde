# -*- coding: utf-8 -*-

import logging
import json

from lib.viabtc.client import Client as Client
from finance.currency import Currency, CurrencyPair
from finance.order import OrderState, OrderDirection, Order, ORDER_ID_FILLED_IMMEDIATELY
from finance.quotes import Quotes, OrderBookItem
from .exchange import ExchangeBase, Fee
from .exception import *
from .utils import get_order_book_item 

OK_CODE = 0
class Exchange(ExchangeBase):
    __currency_map = {
        Currency.CNY: "CNY",
        Currency.BTC: "BTC",
        Currency.LTC: "LTC",
        Currency.ETC: "ETC",
        Currency.ZEC: "ZEC",
        Currency.ETH: "ETH",
    }
    __currency_pair_map = {
        CurrencyPair.BTC_CNY: "BTCCNY",
        CurrencyPair.LTC_CNY: "LTCCNY",
        CurrencyPair.ETC_CNY: "ETCCNY",
        CurrencyPair.ETH_CNY: "ETHCNY",
        CurrencyPair.ZEC_CNY: "ZECCNY",
    }
    TradeFee = {
        CurrencyPair.ETC_CNY: Fee(0.001, Fee.FeeTypes.PERC),
        CurrencyPair.ETH_CNY: Fee(0.001, Fee.FeeTypes.PERC),
        CurrencyPair.BTS_CNY: Fee(0.001, Fee.FeeTypes.PERC),
        CurrencyPair.ZEC_CNY: Fee(0.001, Fee.FeeTypes.PERC),
    }
    WithdrawFee = {
        Currency.ETC: Fee(0.01, Fee.FeeTypes.FIX),
    }
    trade_type_buy = "buy"
    trade_type_sell = "sell"
    
    default_trade_fee = Fee(0.001, Fee.FeeTypes.PERC)

    def __init__(self, config):
        super().__init__(config)
        self.client = Client(config['access_key'], config['secret_key'])

    async def getAccountInfo(self):
        resp =  await self.client.get('balances')
        resp_balances = resp['data']

        balances = {}
        __inverted_currency_map = {v.upper():k for (k,v) in self.__currency_map.items()}
        for currency_str in resp_balances:
            if currency_str in __inverted_currency_map:
                currency = __inverted_currency_map[currency_str]
                balances[currency_str] = float(resp_balances[currency_str]['available'])

        return {"balances": balances}

    async def getQuotes(self, currencyPair, size = 50):
        params = {'market': self.__currency_pair_map[currencyPair],
                  'merge':0, 'limit': size}
        resp = await self.client.get('depth', params)

        if 'code' in resp and resp['code'] != OK_CODE:
            raise ApiErrorException(resp['code'], resp['message'])

        data = resp['data']
        bids = [get_order_book_item(r) for r in data['bids']]
        asks = [get_order_book_item(r) for r in data['asks']]

        quotes = Quotes(bids = bids, asks = asks)
        return quotes


    async def getCurrencyAmountAsync(self, currency):
        resp =  await self.getAccountInfo()
        balance = resp['balances']

        cur = self.__currency_map[currency].upper()
        if cur not in balance:
            raise CurrencyNotExistException(currency)
        return float(balance[cur])

    async def getCurrencyAddressAsync(self, currency):
        cur = self.__currency_map[currency]
        resp = await self.client.get('getUserAddress', {'currency': cur})
        if 'code' in resp and resp['code'] != OK_CODE:
            raise ApiErrorException(resp['code'], resp['message'])
        return resp['message']['datas']['key']

    async def tradeAsync(self, currencyPair, amount, price, action):
        """
        action: buy or sell
        """
        logging.debug("chbtc buy %s, amount %s, price %s", currencyPair, amount, price)
        params = {'market': self.__currency_pair_map[currencyPair],
                  'amount': amount,
                  'price': price,
                  'type': action,
                  'source_id': 'abc'
        }
        resp =  await self.client.post('order', params)

        if 'code' in resp and resp['code'] != OK_CODE:
            raise ApiErrorException(resp['code'], resp['message'])

        return resp['data']['id']

    async def cancelOrderAsync(self, currencyPair, id):
        raise NotImplementedError('not implemented')

    def _json_to_order(self, currencyPair, orderJs):
        id = orderJs['id']
        tradeDate = int(orderJs['create_time'])

        if orderJs['type'] == 'buy':
            buyOrSell = OrderDirection.BUY
        else:
            buyOrSell = OrderDirection.SELL

        price = float(orderJs['price'])
        amount = float(orderJs['amount'])
        filledPrice = float(orderJs['avg_price'])
        filledAmount = float(orderJs['deal_amount'])
        fee = float(orderJs['deal_fee'])
        orderJsState = orderJs['status']

        if orderJsState == 'not_deal':
            state = OrderState.INITIAL
        elif orderJsState == 'done':
            state = OrderState.FILLED
        elif orderJsState == 'part_deal':
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
        params = {'market': self.__currency_pair_map[currencyPair], 'id': id}
        resp =  await self.client.get('getOrder', params)

        if 'code' in resp and resp['code'] != OK_CODE:
            raise ApiErrorException(resp['code'], resp['message'])

        order = self._json_to_order(currencyPair, resp['data'])
        return order

    async def getOpenOrdersAsync(self, currencyPair, params = {}):
        raise NotImplementedError('not implemented')
