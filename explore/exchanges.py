from binance.client import Client as Binance
from poloniex import Poloniex
from huobi.client import Huobi

import logging

class PoloWrapper:
    """a simple polo wrapper
    """
    def __init__(self, pkey, skey):
        """
        :param: pkey: public key
        :param: skey: secret key
        """
        self.client = Poloniex(pkey, skey)

    def trade(self, currency_pair, price, amount, trade_side):
        """trade_type: buy or sell

        polo client api is buy(self, currencyPair, rate, amount, orderType=False)
        """
        if trade_side == "Buy":
            self.client.buy(currency_pair, price, amount)
        elif trade_side == "Sell":
            self.client.sell(currency_pair, price, amount)

    def balance(self, currency=None):
        if not currency:
            return self.client.returnBalances()

        return self.client.returnBalances()[currency]

    def depth(self, currency_pair):
        return self.client.returnOrderBook(currency_pair)

from binance.enums import SIDE_BUY,SIDE_SELL,ORDER_TYPE_LIMIT,TIME_IN_FORCE_IOC,TIME_IN_FORCE_GTC

class BinanceWrapper:
    """Simple binance api wrapper
    """
    def __init__(self, pkey, skey):
        """
        :param: pkey: public key
        :param: skey: secret key
        """
        self.client = Binance(pkey, skey)

    def trade(self, currency_pair, price, amount, trade_side):
        """trade_side: buy or sell

        polo client api is buy(self, currencyPair, rate, amount, orderType=False)
        """
        if trade_side == "Buy":
            ttype = SIDE_BUY
        elif trade_side == "Sell":
            ttype = SIDE_SELL

        order = self.client.create_order(
            symbol=currency_pair,
            side=ttype,
            type=ORDER_TYPE_LIMIT,
            quantity=amount,
            price=price,
            timeInForce=TIME_IN_FORCE_GTC)

        logging.info("place a {} order in binance {} {} {}".format(trade_side, currency_pair, price, amount))


    def balance(self, currency=None):
        account_info = self.client.get_account()
        balances = account_info["balances"]


        balances_dict = dict([(rec['asset'], rec['free']) for rec in balances])

        if not currency:
            return balances_dict

        return balances_dict[currency]

    def depth(self, currency_pair):
        return self.client.get_order_book(symbol=currency_pair)


class HuobiWrapper:
    def __init__(self,pkey, skkey):
        "docstring"
        self.client = Huobi(pkey, skey)

    def trade(self, currency_pair, price, amount, trade_side):
        """trade_side: buy or sell

        polo client api is buy(self, currencyPair, rate, amount, orderType=False)
        """
        if trade_side == "Buy":
            ttype = 'buy-limit'
        elif trade_side == "Sell":
            ttype = 'sell-limit'

        order = self.client.send_order(amount, "", currency_pair,ttype,price)
        logging.info("place a {} order in binance {} {} {}".format(trade_side, currency_pair, price, amount))

    def balance(self, currency_pair):
        return dict([(rec['currency'],float(rec['balance']))
                     for rec in  balance['data']['list'] if rec['type'] == 'trade'])

    def depth(self, currency_pair):
        return self.client.get_depth(currency_pair)['tick']
