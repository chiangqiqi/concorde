# -*- coding: utf-8 -*-
from copy import copy

ORDER_ID_FILLED_IMMEDIATELY = "FILLED_IMMEDIATELY"

class OrderState:
    INITIAL = 'INITIAL' # 待成交
    # SUBMITTED = 'SUBMITTED'
    # ACCEPTED = 'ACCEPTED'
    PARTIALLY_FILLED = 'PARTIALLY_FILLED'
    FILLED = 'FILLED'
    CANCELLED = 'CANCELLED'

class OrderDirection:
	BUY = "buy"
	SELL = "sell"

class Order():
	def __init__(self, 
				currencyPair, 
				id, 
				buyOrSell, 
				price, 
				amount, 
				filledPrice, 
				filledAmount, 
				fee, 
				state, 
				tradeDate):
		self.currencyPair = currencyPair
		self.id = id
		self.buyOrSell = buyOrSell
		self.price = price
		self.amount = amount
		self.filledPrice = filledPrice
		self.filledAmount = filledAmount
		self.fee = fee
		self.state = state
		self.tradeDate = tradeDate

	def _to_dict(self):
		fields = copy(self.__dict__)
		return fields

	def __repr__(self):
		return self._to_dict().__repr__()

	def __str__(self):
		return self._to_dict().__str__()
