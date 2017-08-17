# -*- coding: utf-8 -*-
import logging
import json
import aiohttp

from lib.btc38.client import Client as Client
from finance.currency import Currency, CurrencyPair
from finance.order import OrderState, OrderDirection, Order, ORDER_ID_FILLED_IMMEDIATELY
from finance.quotes import Quotes, OrderBookItem
from .exchange import ExchangeBase, Fee
from .exception import *
from .utils import get_order_book_item, _floor

OK_CODE = 1000
class Exchange(ExchangeBase):
    __currency_map = {
        Currency.CNY: "cny",
        Currency.BTC: "btc",
        Currency.LTC: "ltc",
        Currency.BTS: "bts",
        Currency.XRP: "xrp",
        Currency.NXT: "nxt",
        Currency.DOGE: "doge",
    }
    __currency_pair_map = {
        CurrencyPair.BTC_CNY: "btc_cny",
        CurrencyPair.LTC_CNY: "ltc_cny",
        CurrencyPair.BTS_CNY: "bts_cny",
        CurrencyPair.XRP_CNY: "xrp_cny",
        CurrencyPair.NXT_CNY: "nxt_cny",
        CurrencyPair.DOGE_CNY: "doge_cny",
    }
    TradeFee = {
        CurrencyPair.BTS_CNY: Fee(0.001, Fee.FeeTypes.PERC),
        CurrencyPair.XRP_CNY: Fee(0.001, Fee.FeeTypes.PERC),
        CurrencyPair.DOGE_CNY: Fee(0.001, Fee.FeeTypes.PERC),
    }
    default_trade_fee = Fee(0.001, Fee.FeeTypes.PERC)
    WithdrawFee = {
        Currency.CNY: Fee(0.01, Fee.FeeTypes.PERC),
        Currency.BTS: Fee(0.01, Fee.FeeTypes.MIX, mix_fee2 = 1),
        Currency.XRP: Fee(0.01, Fee.FeeTypes.PERC),
        Currency.DOGE: Fee(0.01, Fee.FeeTypes.PERC),
    }
    trade_type_buy = 1
    trade_type_sell = 2

    __order_status_open = 0 #待成交
    __order_status_cancelled = 1
    __order_status_filled = 2
    __order_status_paritially_filled = 3

    def __init__(self, config):
        super().__init__(config)
        self.client = Client(config['access_key'], config['secret_key'], config['user_id'])

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
        bids = list(map(get_order_book_item, resp['bids']))
        asks = list(map(get_order_book_item, resp['asks']))
        quotes = Quotes(bids = bids, asks = asks)
        logging.debug("btc38 quotes: %s", quotes)
        return quotes

    async def getCurrencyAddressAsync(self, currency):
        raise NotImplementedError("btc38 do not have getCurrencyAddressAsync api")

    async def tradeAsync(self, currencyPair, amount, price, action):
        logging.debug("btc38 buy %s, amount %s, price %s", currencyPair, amount, price)
        #特殊逻辑，每个币种的价格精确度不一样，必须调用方处理
        precision_dict = {CurrencyPair.XRP_CNY: 4, CurrencyPair.DOGE_CNY: 5,
                          CurrencyPair.NXT_CNY: 3, CurrencyPair.ETH_CNY: 1,
                          CurrencyPair.ETC_CNY: 2}

        precision = precision_dict[currencyPair] if currencyPair in precision_dict else 6

        floorPrice = _floor(price, precision)

        logging.debug("btc38 buy %s, floorPrice %s", currencyPair, floorPrice)
        (c, mk_type) = self.__currency_pair_map[currencyPair].split("_")
        resp =  await self.client.post('order', {'coinname': c,
                                                 'mk_type': mk_type,
                                                 'amount': _floor(amount,4),
                                                 'price': floorPrice,
                                                 'type': action})
        retAndId = resp.split('|')
        result = retAndId[0]
        id = ORDER_ID_FILLED_IMMEDIATELY
        if len(retAndId) > 1:
            id = retAndId[1]
        if result != "succ":
            raise ApiErrorException('', resp)
        return id

    async def cancelOrderAsync(self, currencyPair, id):
        logging.debug("btc38 cancel order id %s, currencyPair %s", id, currencyPair)
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
        orders = await self.getOpenOrdersAsync(currencyPair)
        if len(orders) <= 0:
            return None
        return filter(lambda x: x.id == id, orders).__next__()
        # raise NotImplementedError("btc38 do not have getOrderAsync api")

    async def getOpenOrdersAsync(self, currencyPair, params = {}):
        (c, mk_type) = self.__currency_pair_map[currencyPair].split("_")
        resp =  await self.client.post('openOrders', {'mk_type': mk_type, 'coinname': c})
        if resp == 'no_order':
            resp = []
        if not isinstance(resp, list):
            raise ApiErrorException(resp)
        orders = list(map(lambda orderJs: self._json_to_order(currencyPair, orderJs), resp))
        return orders

    async def withdraw(self, currency, amount, address, memo, params={}):
        proxyCodeMap = {'SUCCESS': 0, 
                        'LIMIT': 1, #提币限制 
                        'PROCESSING': 2,
                        'FAIL': 3,
                        'SYSTEM_BUSY': 4,
                        'PARAMS_ERROR': 5,
                        'INTERNAL_SERVER_ERROR': 6,
                        'OVER_BALANCE': 7}
        logging.debug("btc38 withdraw currency %s to address %s, amount %s, memo %s",
                      currency, address, amount, memo)
        path = self.config['withdraw_proxy_url']
        rkWithdrawSecretKey = self.config['rk_withdraw_secret_key']

        # 币数化正，btc38仅支持整数提币
        url = "%s?coinname=%s&address=%s&balance=%s&memo=%s&rk_secret_key=%s"%(path, 
                                                                              self.__currency_map[currency].upper(), 
                                                                              address, 
                                                                              int(amount), 
                                                                              memo, 
                                                                              rkWithdrawSecretKey)
        logging.debug("btc38 client get url: %s", url)
        async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout = 20) as resp:
                    resp_text = await resp.text()
                    logging.debug("btc38 resp: %s", resp_text)
                    try:
                        ret = json.loads(resp_text)
                    except Exception as e:
                        raise ApiErrorException('', resp_text)

                    if ret['code'] != proxyCodeMap['SUCCESS'] or ret['code'] != proxyCodeMap['PROCESSING']:
                        raise ApiErrorException(ret['code'], ret['message'])
                    return True
