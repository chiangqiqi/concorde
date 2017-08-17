from .test_exchanges import ExchangeTester
from .test_common import name2exchange
from finance.currency import Currency, CurrencyPair


exchanges = ['jubi']
def test_exchanges_order():
    for ex in exchanges:
        exchange = name2exchange(ex)
        tester = ExchangeTester(exchange)
        tester.test_sell(CurrencyPair.XRP_CNY, amount=0.1, price=200)
