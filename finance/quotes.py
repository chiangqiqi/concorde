# -*- coding: utf-8 -*-
from copy import copy
class OrderBookItem:
	def __init__(self, price, amount):
		self.price = price
		self.amount = amount

	def _to_dict(self):
		fields = copy(self.__dict__)
		return fields

	def __repr__(self):
		return self._to_dict().__repr__()

	def __str__(self):
		return self._to_dict().__str__()

class Quotes:
	def __init__(self, bids, asks):
		self.bids = sorted(bids, key = lambda x: x.price, reverse=True)
		self.asks = sorted(asks, key = lambda x: x.price)

	#return list of OrderBookItem, 从小到大排序
	def getAsks(self):
		return self.asks

	#return list of OrderBookItem, 从大到小排序
	def getBids(self):
		return self.bids

	def _to_dict(self):
		fields = copy(self.__dict__)
		return fields

	def __repr__(self):
		return self._to_dict().__repr__()

	def __str__(self):
		return self._to_dict().__str__()