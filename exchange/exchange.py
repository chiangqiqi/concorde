# -*- coding: utf-8 -*-

from six import with_metaclass
import abc
import asyncio

class Fee():
    def enum(**enums):
        return type('Enum', (), enums)
    FeeTypes = enum(PERC = 1, FIX = 2, MIX = 3)
    def __init__(self, fee, fee_type, mix_fee2 = 0.0):
        self.fee = fee
        self.mix_fee2 = mix_fee2
        self.fee_type = fee_type

    def calculate_fee(self, num):
        if (self.fee_type == self.FeeTypes.PERC):
            return num * self.fee
        elif (self.fee_type == self.FeeTypes.FIX):
            return self.fee
        else:
            return num * self.fee + self.mix_fee2

class ExchangeBase(with_metaclass(abc.ABCMeta)):
    '''
    Abstract class of exchange.
    Class properties:
    '''
    def __init__(self, config):
        self.config = config
        self.accountInfo = {}
    ##
    #param:
    #amount - 交易数量
    #price - 交易单价
    #return: cny, amount * price * tradeRate，单位CNY
    def calculateTradeFee(self, currencyPair, amount, price):
        fee = self.default_trade_fee
        if currencyPair in self.TradeFee:
            fee = self.TradeFee[currencyPair]
        return fee.calculate_fee(amount * price)

    #param:
    #amount - 提现数量
    #return: 手续费数量，单位个
    def calculateWithdrawFee(self, currency, amount):
        return self.WithdrawFee[currency].calculate_fee(amount)


    @abc.abstractmethod
    async def getAccountInfo(self):
        pass

    async def updateAccountInfo(self):
        self.accountInfo = await self.getAccountInfo()

    @abc.abstractmethod
    async def getQuotes(self, currencyPair):
        pass

    async def getCashAsync(self):
        """
        most time, get cash async should be just inside the balance
        """
        resp =  await self.getAccountInfo()
        return round(float(resp['balances']['CNY']), 2)

    async def getCurrencyAmountAsync(self, currency):
        info = await self.getAccountInfo()
        return info['balances'][currency]


    @abc.abstractmethod
    async def getCurrencyAddressAsync(self, currency):
        pass
    
    async def buyAsync(self, currencyPair, amount, price):
        resp =  await self.tradeAsync(currencyPair, amount, price, self.trade_type_buy)
        return resp

    async def sellAsync(self, currencyPair, amount, price):
        resp =  await self.tradeAsync(currencyPair, amount, price, self.trade_type_sell)
        return resp

    @abc.abstractmethod
    async def tradeAsync(self, currencyPair, amount, price, action):
        pass

    @abc.abstractmethod
    async def getOrderAsync(self, currencyPair, id):
        pass

    @abc.abstractmethod
    async def getOpenOrdersAsync(self, currencyPair, params = {}):
        pass

    @abc.abstractmethod
    async def cancelOrderAsync(self, currencyPair, id):
        pass

    # @abc.abstractmethod
    async def withdraw(self, currency, amount, address, memo, params={}):
        raise NotImplementedError("withdraw api not implemented")
