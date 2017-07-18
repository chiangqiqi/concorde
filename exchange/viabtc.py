# -*- coding: utf-8 -*-

from lib.viabtc.client import Client as Client
from finance.currency import Currency, CurrencyPair
from finance.order import OrderState, OrderDirection, Order, ORDER_ID_FILLED_IMMEDIATELY
from finance.quotes import Quotes, OrderBookItem
from .exchange import ExchangeBase, Fee
from .exception import *
import logging

TradeFee = {
        CurrencyPair.ETC_CNY: Fee(0.001, Fee.FeeTypes.PERC),
        CurrencyPair.ETH_CNY: Fee(0.001, Fee.FeeTypes.PERC),
        CurrencyPair.BTS_CNY: Fee(0.001, Fee.FeeTypes.PERC),
}

WithdrawFee = {
    Currency.ETC: Fee(0.01, Fee.FeeTypes.FIX),
}

import json

OK_CODE = 0
class Exchange(ExchangeBase):
    __currency_map = {
        Currency.CNY: "CNY",
        Currency.BTC: "BTC",
        Currency.LTC: "LTC",
        Currency.ETC: "ETC",
        Currency.ETH: "ETH",
    }
    __currency_pair_map = {
        CurrencyPair.BTC_CNY: "BTCCNY",
        CurrencyPair.LTC_CNY: "LTCCNY",
        CurrencyPair.ETC_CNY: "ETCCNY",
        CurrencyPair.ETH_CNY: "ETHCNY",
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
        return TradeFee[currencyPair].calculate_fee(amount * price)

    def calculateWithdrawFee(self, currency, amount):
        return WithdrawFee[currency].calculate_fee(amount)

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

        format_item = lambda x: OrderBookItem(price = float(x[0]), amount = float(x[1]))

        data = resp['data']
        bids = [format_item(r) for r in data['bids']]
        asks = [format_item(r) for r in data['asks']]

        quotes = Quotes(bids = bids, asks = asks)
        logging.debug("quotes: %s", quotes)
        return quotes


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

    async def buyAsync(self, currencyPair, amount, price):
        return await self.tradeAsync(currencyPair, amount, price, 'buy')
    
    async def sellAsync(self, currencyPair, amount, price):
        return await self.tradeAsync(currencyPair, amount, price, 'sell')

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
        params = {'currency': self.__currency_pair_map[currencyPair], 'id': id}
        resp =  await self.client.post('getOrder', params)
        
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
