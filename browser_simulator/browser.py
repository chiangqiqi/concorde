# -*- coding: utf-8 -*-
from six import with_metaclass
import abc
import asyncio
import time
import logging
import aiohttp
import sys, traceback
import json
from aiohttp import web

class Browser(with_metaclass(abc.ABCMeta)):
	'''
	Abstract class of exchange.
	Class properties:
	'''
	def __init__(self, config):
		self.config = config
		self.cookies = self.decodeCookie(config['headers']['Cookie'])

	def setCookie(self, cookies):
		self.cookies = cookies

	def getCookie(self):
		return self.cookies

	def encodeCookie(self, cookie):
		ret = ''
		for (k, v) in cookie.items():
			ret = "%s;%s=%s"%(ret, k, v)
		return ret

	def decodeCookie(self, cookiesStr):
		items = cookiesStr.split(';')
		ret = {}
		for item in items:
			# logging.debug("item: %s", item)
			(k,v) = item.split('=')
			ret.update({k: v})
		return ret

	def getHeaders(self):
		cookies = self.encodeCookie(self.getCookie())
		headers = {'User-Agent': self.config['headers']['User-Agent'],
				   'Accept': self.config['headers']['Accept'],
				   'Accept-Encoding': self.config['headers']['Accept-Encoding'],
				   'Accept-Language': self.config['headers']['Accept-Language'],
				   'Cookie': cookies}
		return headers

	# return [result, new_cookies]
	# result: True or False
	# new_cookies: new cookies
	@abc.abstractmethod
	async def heartbeat(self):
		pass

	async def startKeeplive(self):
		intervalSecond = self.config['hearbeat_interval_second']
		prevCheckTime = None
		while True:
			now = time.time()
			logging.info("time: %s, prevCheckTime: %s", now, prevCheckTime)
			if prevCheckTime is not None and now - prevCheckTime < intervalSecond:
				await asyncio.sleep(intervalSecond - (now - prevCheckTime))
				continue
			else:
				logging.info("heartbeating...")
				try:
					[success, new_cookies] = await self.heartbeat()
					if not success:
						logging.warn("heartbeat failed, please check your account.")
					else:
						logging.info("heartbeat success")
						if new_cookies is not None:
							logging.info("has new cookies(%s), now setting new cookies in browser.", new_cookies)
							self.setCookie(new_cookies)
				except Exception as e:
					logging.error("%s",e)
					ex_type, ex, tb = sys.exc_info()
					traceback.print_tb(tb)

			prevCheckTime = time.time()

class HttpClient():
	def __init__(self):
		pass

	def urlencode(self, params):
		keys = params.keys()
		# keys.sort()
		query = ''
		for key in keys:
			value = params[key]
			query = "%s&%s=%s" % (query, key, value) if len(query) else "%s=%s" % (key, value)
		return query

	async def get(self, path, params=None, headers={}):
		url = path
		if (params is not None):
			url += "?" + self.urlencode(params)
		logging.debug("HttpClient get url: %s, headers: %s", url, headers)
		async with aiohttp.ClientSession() as session:
			async with session.get(url, headers = headers, timeout = 10) as resp:
				respText = await resp.text()
				# logging.debug("HttpClient resp: %s", respText)
				headers = resp.headers
				try:
					ret = json.loads(respText)
					return [ret, headers]
				except Exception as e:
					logging.debug("json.loads error: %s", e)
					return [respText, headers]


class ResultCode():
	SUCCESS = 0
	LIMIT = 1 #提币限制
	PROCESSING = 2
	FAIL = 3
	SYSTEM_BUSY = 4
	PARAMS_ERROR = 5
	INTERNAL_SERVER_ERROR = 6
	OVER_BALANCE = 7 #币不够

class Btc38Browser(Browser):
	def __init__(self, config):
		super().__init__(config)
		self.client = HttpClient()

	async def getAddressIndex(self, coinname, address):
		logging.debug("getAddressIndex for coinname %s, address %s", coinname, address)
		path = self.config['address_index_url']
		headers = self.getHeaders()
		(resp, respHeaders) = await self.client.get(path, params = {'coinname': coinname}, headers = headers)
		logging.debug("getAddressIndex resp: %s", resp)
		for i in range(len(resp)):
			if resp[i]['addr'] == address:
				logging.debug("find addindex %s for address %s", i + 1, address)
				return i + 1
		logging.debug("cannot find addindex for address %s", address)
		return -1

	async def withdraw(self, coinname, addrindex, balance, memo):
		logging.debug("Btc38Browser::withdraw: coinname %s, addrindex %s, balance %s, memo %s",
					  coinname, addrindex, balance, memo)
		headers = self.getHeaders()
		withdrawPath = self.config['withdraw_url']
		params = {'coinname': coinname, 'addrindex': addrindex, 'balance': balance, 'memo': memo}
		(resp, respHeaders) = await self.client.get(withdrawPath, params = params, headers = headers)
		logging.info("btc38 withdraw resp: %s", resp)
		if resp.strip() == "succ":
			return (ResultCode.SUCCESS, "ok")
		if resp.strip() == "limit1" or resp.strip() == "limit2":
			return (ResultCode.LIMIT, "reach withdraw limit")
		if resp.strip().startswith("fail"):
			return (ResultCode.FAIL, "failed")
		if resp.strip() == "processing":
			return (ResultCode.PROCESSING, "processing")
		if resp.strip() == "system_busy":
			return (ResultCode.SYSTEM_BUSY, "system_busy")
		if resp.strip() == "overBalance":
			return (ResultCode.OVER_BALANCE, "overBalance")
		return (ResultCode.INTERNAL_SERVER_ERROR, "INTERNAL_SERVER_ERROR")

	async def heartbeat(self):
		url = self.config['heartbeat_url']
		headers = self.getHeaders()

		result = True
		newCookies = None

		[resp, respHeaders] = await self.client.get(url, headers = headers)
		if 'Set-Cookie' in respHeaders:
			newCookies = self.decodeCookie(respHeaders['Set-Cookie'])

		# TODO: 根据请求结果判断用户是否需要重新登录
		
		return (result, newCookies)






