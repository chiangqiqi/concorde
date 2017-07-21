import yaml
import pytest
import unittest
import asyncio
import importlib

from exchange.viabtc import Exchange as ViaBTC
from finance.currency import Currency, CurrencyPair


def async_test(f):
    """
    a simple wrapper for coroutine which should live in a event loop
    """
    def wrapper(*args, **kwargs):
        coro = asyncio.coroutine(f)
        future = coro(*args, **kwargs)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(future)
    return wrapper

class ExchangeTester:
    def __init__(self, _exchange):
        """
        test the functions of an exchange
        """
        self.exchange = _exchange

    @async_test
    def _get_cash(self):
        res = yield from self.exchange.getCashAsync()
        assert res > 0

    @async_test
    def _get_account_info(self):
        res = yield from self.exchange.getAccountInfo()
        assert res['balances']['ETH'] >= 0

    @async_test
    def _get_currency_amout(self):
        res = yield from self.exchange.getCurrencyAmountAsync(Currency.ETH)
        assert res >= 0

    @async_test
    def _get_depth(self):
        res = yield from self.exchange.getQuotes(CurrencyPair.ETH_CNY)
        assert res.asks[0].price >= 0

    @async_test
    def test_sell(self):
        res = yield from self.exchange.sellAsync(CurrencyPair.ETH_CNY, 0.1, 2000)
        assert res > 0

    @async_test
    def test_sell_and_check_status(self):
        # res just returns the order id
        cp = CurrencyPair.ETH_CNY
        orderid = yield from self.exchange.sellAsync(cp, 0.1, 2000)

        order = yield from self.exchange.getOrderAsync(cp, orderid)
        assert order.buyOrSell == 'sell'

    @async_test
    def _get_order(self):
        res = yield from self.exchange.getOrderAsync(CurrencyPair.ETH_CNY, 6498328)

        assert res.amount == 0.1

    def test_get(self):
        self._get_cash()
        self._get_currency_amout()

    def test_ordering(self):
        self.test_sell()

config = yaml.load(open('config.yaml', encoding='utf8'))

def name2exchange(name):
    exch_config = list(filter(lambda x: x['name'] == name, config['exchange']))[0]
    e = importlib.import_module("exchange.%s"%name).Exchange(exch_config)
    return e


exchanges = ['yunbi', 'viabtc', 'chbtc']
def __test_exchanges_get():
    for ex in exchanges:
        exchange = name2exchange(ex)
        tester = ExchangeTester(exchange)
        tester.test_get()

exchanges = ['chbtc']
def test_exchanges_order():
    for ex in exchanges:
        exchange = name2exchange(ex)
        tester = ExchangeTester(exchange)
        tester.test_sell_and_check_status()

if __name__ == '__main__':
    unittest.main()
