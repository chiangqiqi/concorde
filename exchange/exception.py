# -*- coding: utf-8 -*-

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class CurrencyNotExistException(Error):
	def __init__(self, currency):
		self.currency = currency
		self.message = "currency %s not exist"%(currency)

class ApiErrorException(Error):
	def __init__(self, code, msg):
		self.code = code
		self.message = msg
