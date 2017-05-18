# -*- coding: utf-8 -*-

def enum(**enums):
	return type('Enum', (), enums)

Currency = enum(CNY = "CNY",
				BTC = "BTC", 
				LTC = "LTC", 
				ZEC = "ZEC", 
				ETH = "ETH", 
				ETC = "ETC",
				BTS = "BTS",
				DASH = "DASH",
				DOGE = "DOGE",
				XRP = "XRP")

CurrencyPair = enum(BTC_CNY = "BTC_CNY", 
					LTC_CNY = "LTC_CNY", 
					ZEC_CNY = "ZEC_CNY", 
					ETH_CNY = "ETH_CNY", 
					ETC_CNY = "ETC_CNY",
					BTS_CNY = "BTS_CNY",
					DASH_CNY = "DASH_CNY",
					DOGE_CNY = "DOGE_CNY",
					XRP_CNY = "XRP_CNY")

def currencyPair2Currency(currencyPair):
	__CurrencyPair2Currency = {
		CurrencyPair.BTC_CNY: Currency.BTC,
		CurrencyPair.LTC_CNY: Currency.LTC,
		CurrencyPair.ZEC_CNY: Currency.ZEC,
		CurrencyPair.ETH_CNY: Currency.ETH,
		CurrencyPair.ETC_CNY: Currency.ETC,
		CurrencyPair.BTS_CNY: Currency.BTS,
		CurrencyPair.DASH_CNY: Currency.DASH,
		CurrencyPair.DOGE_CNY: Currency.DOGE,
		CurrencyPair.XRP_CNY: Currency.XRP,
	}
	return __CurrencyPair2Currency[currencyPair]

def getCurrencyByName(name):
	if name in Currency.__dict__:
		return name
	return None

def getCurrencyPairByName(name):
	if name in Currency.__dict__:
		return name
	return None


