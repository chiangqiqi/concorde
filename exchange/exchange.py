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
    @abc.abstractmethod
    def calculateTradeFee(self, currencyPair, amount, price):
        pass

    ##
    #param:
    #amount - 提现数量
    #return: 手续费数量，单位个
    @abc.abstractmethod
    def calculateWithdrawFee(self, currency, amount):
        pass

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

    @abc.abstractmethod
    async def getCurrencyAmountAsync(self, currency):
        pass

    @abc.abstractmethod
    async def getCurrencyAddressAsync(self, currency):
        pass

    @abc.abstractmethod
    async def buyAsync(self, currencyPair, amount, price):
        pass

    @abc.abstractmethod
    async def sellAsync(self, currencyPair, amount, price):
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
