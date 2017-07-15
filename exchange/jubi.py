# -*- coding: utf-8 -*-

from lib.jubi.client import Client as Client
from finance.currency import Currency, CurrencyPair
from finance.order import OrderState, OrderDirection, Order, ORDER_ID_FILLED_IMMEDIATELY
from finance.quotes import Quotes, OrderBookItem
from .exchange import ExchangeBase, Fee
from .exception import *
import logging
import math

JUBITradeFee = {
    CurrencyPair.XRP_CNY: Fee(0.001, Fee.FeeTypes.PERC),
    CurrencyPair.ETC_CNY: Fee(0.001, Fee.FeeTypes.PERC),
    CurrencyPair.DOGE_CNY: Fee(0.001, Fee.FeeTypes.PERC),
        CurrencyPair.BTS_CNY: Fee(0.001, Fee.FeeTypes.PERC),
}

JUBIWithdrawFee = {
    Currency.XRP: Fee(0.01, Fee.FeeTypes.PERC),
    Currency.ETC: Fee(0.01, Fee.FeeTypes.FIX),
    Currency.DOGE: Fee(0.01, Fee.FeeTypes.PERC),
}


class Exchange(ExchangeBase):
    __currency_map = {
        Currency.CNY: "CNY",
        Currency.BTC: "btc",
        Currency.BTS: "bts",
        Currency.LTC: "ltc",
        Currency.ETC: "etc",
        Currency.ETH: "eth",
        Currency.XRP: "xrp",
        Currency.DOGE: "doge",
        Currency.ANS: "ans"
    }
    __currency_pair_map = {
        CurrencyPair.BTC_CNY: "btc",
        CurrencyPair.BTS_CNY: "bts",
        CurrencyPair.LTC_CNY: "ltc",
        CurrencyPair.ETC_CNY: "etc",
        CurrencyPair.ETH_CNY: "eth",
        CurrencyPair.XRP_CNY: "xrp",
        CurrencyPair.DOGE_CNY: "doge",
        CurrencyPair.ANS_CNY: "ans"
    }

    __trade_type_buy = "buy"
    __trade_type_sell = "sell"

    __order_status_open = "open" #待成交
    __order_status_new = "new" #待成交
    __order_status_cancelled = "cancelled"
    __order_status_filled = "closed"

    def __init__(self, config):
        super().__init__(config)
        self.client = Client(config['access_key'], config['secret_key'])


    def _floor(self, num, precision = 4):
        multiplier = math.pow(10.0, precision)
        return math.floor(num * multiplier) / multiplier

    def calculateTradeFee(self, currencyPair, amount, price):
        return JUBITradeFee[currencyPair].calculate_fee(amount * price)

    def calculateWithdrawFee(self, currency, amount):
        return JUBIWithdrawFee[currency].calculate_fee(amount)

    async def getAccountInfo(self):
        resp =  await self.client.post('balances')
        if 'result' in resp and resp['result'] is False:
            raise ApiErrorException(resp['code'], str(resp))
        if 'asset' not in resp:
            raise ApiErrorException(-1, resp)

        resp_balances = resp
        balances = {}
        __inverted_currency_map = {v.lower() + "_balance":k for (k,v) in self.__currency_map.items()}
        for currency_str in resp_balances:
            if currency_str in __inverted_currency_map:
                currency = __inverted_currency_map[currency_str]
                balances.update({currency: float(resp_balances[currency_str])})
        return {"balances": balances}

    async def getQuotes(self, currencyPair, size = 50):
        resp =  await self.client.get('depth', {'coin': self.__currency_pair_map[currencyPair]})
        if 'result' in resp and resp['result'] is False:
            raise ApiErrorException(resp['code'], str(resp))
        bids = list(map(lambda x: OrderBookItem(price = float(x[0]), amount = float(x[1])), resp['bids']))
        asks = list(map(lambda x: OrderBookItem(price = float(x[0]), amount = float(x[1])), resp['asks']))
        quotes = Quotes(bids = bids, asks = asks)
        logging.debug("jubi quotes: %s", quotes)
        return quotes

    async def getCashAsync(self):
        info = await self.getAccountInfo()
        return info['balances'][Currency.CNY]

    async def getCurrencyAmountAsync(self, currency):
        info = await self.getAccountInfo()
        return info['balances'][currency]

    async def getCurrencyAddressAsync(self, currency):
        raise NotImplementedError("jubi do not have getCurrencyAddressAsync api")

    async def tradeAsync(self, currencyPair, amount, price, action):
        """
        action: buy or sell
        """
        logging.debug("jubi buy %s, amount %s, price %s", currencyPair, amount, price)

        #特殊逻辑，每个币种的价格精确度不一样，必须调用方处理
        # this fucing api has strange precision limit
        precision_dict = {CurrencyPair.XRP_CNY: 4, CurrencyPair.DOGE_CNY: 6,
                          CurrencyPair.ETC_CNY: 2, CurrencyPair.BTS_CNY: 6}

        precision = precision_dict[currencyPair] if currencyPair in precision_dict else 6

        floorPrice = self._floor(price, precision)
        logging.debug("jubi buy %s, floorPrice %s", currencyPair, floorPrice)

        resp =  await self.client.post('order', {'coin': self.__currency_pair_map[currencyPair],
                                                 'amount': self._floor(amount, 4),
                                                 'price': floorPrice,
                                                 'type': action})
        
        if 'result' in resp and resp['result'] is False:
            raise ApiErrorException(resp['code'], str(resp))
        return resp


    async def buyAsync(self, currencyPair, amount, price):
        resp =  await self.tradeAsync(currencyPair, amount, price, 'buy')
        return resp['id']

    async def sellAsync(self, currencyPair, amount, price):
        resp =  await self.tradeAsync(currencyPair, amount, price, 'sell')
        return resp['id']

    async def cancelOrderAsync(self, currencyPair, id):
        logging.debug("jubi cancel order id %s, currencyPair %s", id, currencyPair)
        resp =  await self.client.post('cancelOrder', {'coin': self.__currency_pair_map[currencyPair],
                                                       'id': id})
        if 'result' in resp and resp['result'] is False:
            raise ApiErrorException(resp['code'], str(resp))
        return True

    def _json_to_order(self, currencyPair, orderJs):
        id = orderJs['id']
        tradeDate = orderJs['datetime']
        if orderJs['type'] == self.__trade_type_buy:
            buyOrSell = OrderDirection.BUY
        else:
            buyOrSell = OrderDirection.SELL
        price = float(orderJs['price'])
        amount = float(orderJs['amount_original'])
        amountNotFilled = float(orderJs['amount_outstanding'])
        filledPrice = None
        filledAmount = amount - amountNotFilled
        fee = None
        orderJsState = orderJs['status']
        if orderJsState == self.__order_status_open or orderJsState == self.__order_status_new:
            state = OrderState.INITIAL
        elif orderJsState == self.__order_status_filled:
            state = OrderState.FILLED
        elif orderJsState == self.__order_status_cancelled:
            state = OrderState.CANCELLED
        else:
            state = OrderState.PARTIALLY_FILLED

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
        resp =  await self.client.post('trade_view', {'coin': self.__currency_pair_map[currencyPair],
                                                     'id': id})
        # 特殊逻辑，下单后聚币网居然可能查不到订单，暂时返回None吧
        if 'result' in resp and resp['result'] is False and int(resp['code']) == 203:
            return None
            
        if 'result' in resp and resp['result'] is False:
            raise ApiErrorException(resp['code'], str(resp))

        order = self._json_to_order(currencyPair, resp)
        return order

    async def getOpenOrdersAsync(self, currencyPair, params = {}):
        raise NotImplementedError("jubi do not have getOpenOrdersAsync api")
        # new_params = params
        # new_params.update({"coin": self.__currency_pair_map[currencyPair], "type": "all"})
        # resp =  await self.client.post('trade_list', params)

        # if 'result' in resp and resp['result'] is False:
        #   raise ApiErrorException(resp['code'], str(resp))

        # orders = list(map(lambda orderJs: self._json_to_order(currencyPair, orderJs), resp))
        # return orders
