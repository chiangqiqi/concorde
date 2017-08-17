import yaml
import unittest
import asyncio
import importlib

from finance.currency import Currency, CurrencyPair
from .test_common import name2exchange,async_test

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
    def test_sell(self, cp, amount=0.1, price=3000):
        res = yield from self.exchange.sellAsync(cp, amount, price)
        assert res > 0

    @async_test
    def test_sell_and_check_status(self, cp=CurrencyPair.ETH_CNY):
        # res just returns the order id
        cp = CurrencyPair.ETH_CNY
        orderid = yield from self.exchange.sellAsync(cp, 0.1, 3000)

        order = yield from self.exchange.getOrderAsync(cp, orderid)
        assert order.buyOrSell == 'sell'

    @async_test
    def test_buy_and_check_status(self, cp=CurrencyPair.ETH_CNY):
        # res just returns the order id
        orderid = yield from self.exchange.buyAsync(cp, 1000.0343401, 0.0512345002)

        order = yield from self.exchange.getOrderAsync(cp, orderid)
        assert order.buyOrSell == 'buy'

    @async_test
    def _get_order(self):
        res = yield from self.exchange.getOrderAsync(CurrencyPair.ETH_CNY, 6498328)

        assert res.amount == 0.1

    def test_get(self):
        res = self.exchange.calculateTradeFee(CurrencyPair.ETH_CNY, 10000, 1)
        assert res == 10

        self._get_cash()
        self._get_currency_amout()

    def test_ordering(self):
        self.test_sell()

exchanges = ['yunbi', 'viabtc', 'chbtc']
def test_exchanges_get():
    for ex in exchanges:
        exchange = name2exchange(ex)
        tester = ExchangeTester(exchange)
        tester.test_get()

exchanges = ['yunbi']
def test_exchanges_order():
    for ex in exchanges:
        exchange = name2exchange(ex)
        tester = ExchangeTester(exchange)
        tester.test_sell_and_check_status()


class JubiPrecisonTest(unittest.TestCase):
    def setUp(self):
        exchange = name2exchange('jubi')
        self.tester = ExchangeTester(exchange)
        
    def test_jubi_bts(self):
        """
        test if bts order is well placed
        """
        self.tester.test_buy_and_check_status(CurrencyPair.BTS_CNY)
        self.tester.test_buy_and_check_status(CurrencyPair.XRP_CNY)


if __name__ == '__main__':
    unittest.main()
