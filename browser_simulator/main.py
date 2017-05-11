#coding=utf-8
#加载必要的库
# import numpy as np
# import pandas as pd
from __future__ import print_function
from datetime import datetime
import time
import json, requests
import time
import importlib
import asyncio
import logging
import logging.config
import yaml
import os
from browser import Btc38Browser, ResultCode
import aiohttp
from aiohttp import web

logging.config.fileConfig("./logging.config")
config = yaml.load(open(os.path.join("", 'config.yaml'), encoding='utf8'))
port = config['listen_port']

async def error(flag):
	if flag:
		raise ValueError("value error")
	else:
		return 1

async def test(url="http://www.baidu.com"):
	async with aiohttp.ClientSession() as session:
	    async with session.get(url, timeout = 10) as resp:
	        resp_text = await resp.text()
	        print(resp.headers['Set-Cookie'])

def handler(browser):
	logging.info("browser: %s", browser)
	def decodeQuery(query):
		items = query.split('&')
		ret = {}
		for item in items:
			(k,v) = item.split('=')
			ret.update({k:v})
		return ret

	# coinname, addrindex, balance, memo):
	def checkParams(params):
		rk_secret_key = config['rk_secret_key']
		if 'coinname' not in params:
			return (False, "need coinname")
		if 'address' not in params:
			return (False, "need address")
		if 'balance' not in params:
			return (False, "need balance")
		if 'memo' not in params:
			return (False, "need memo")
		if 'rk_secret_key' not in params:
			return (False, "need rk_secret_key")
		if params['rk_secret_key'] != rk_secret_key:
			return (False, "rk_secret_key error")
		return (True, "")

	async def btc38WithdrawHandler(request):
		try:
			logging.info("request: %s", request)
			path = request.path
			logging.debug("path: %s", path)
			if path != '/bter/withdraw':
				result = json.dumps({'code': ResultCode.PARAMS_ERROR, 'message': "path error"})
				return web.Response(text=result)
			query = decodeQuery(request.query_string)
			logging.debug("query_string: %s", query)
			(isParamsCorrected, errorMsg) = checkParams(query)
			if not isParamsCorrected:
				result = json.dumps({'code': ResultCode.PARAMS_ERROR, 'message': errorMsg})
				return web.Response(text=result)
			coinname = query['coinname']
			address = query['address']
			balance = query['balance']
			memo = query['memo']

			# 定位地址在btc38中的addrindex
			logging.info("calling Btc38Browser to getAddressIndex: coinname %s, address %s", coinname, address)
			addrindex = await browser.getAddressIndex(coinname, address)
			if (addrindex == -1):
				logging.debug("(%s)cannot find addindex for address %s", coinname, address)
			logging.info("calling Btc38Browser to withdraw: coinname %s, addrindex %s, balance %s, memo %s",
					  	 coinname, addrindex, balance, memo)
			(ret, msg) = await browser.withdraw(coinname = coinname,
											  addrindex = addrindex,
											  balance = balance,
											  memo = memo)
			logging.info("Btc38Browser::withdraw resp: (%s,%s)", ret, msg)
			result = json.dumps({'code': ret, 'message': msg})
			return web.Response(text=result)
		except Exception as e:
			logging.error("send http request to btc38 error: %s"%(e))
			ex_type, ex, tb = sys.exc_info()
			traceback.print_tb(tb)
		return web.Response(text="OK")

	return btc38WithdrawHandler

async def listen(loop, browser, port):
	h = handler(browser)
	server = web.Server(h)
	await loop.create_server(server, "127.0.0.1", port)
	logging.info("======= Serving on http://127.0.0.1:%s/ ======", port)
	while True:
		# pause here for very long time by serving HTTP requests and
		# waiting for keyboard interruption
		await asyncio.sleep(100*3600)

browser = Btc38Browser(config['browsers'][0])
loop = asyncio.get_event_loop()
futs = asyncio.wait([browser.startKeeplive(), listen(loop, browser, port)])
loop.run_until_complete(futs)
# loop.run_until_complete(main(loop))
# loop.run_until_complete(listen(loop, browser, 8080))
