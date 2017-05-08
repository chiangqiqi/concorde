import urllib
import urllib.request
import json
import time
import hmac
import hashlib
import struct
import logging
import aiohttp

TRADE_BASE_URL = 'https://trade.chbtc.com'
MARKET_BASE_URL = 'http://api.chbtc.com'

TRADE_API_BASE_PATH = '/api'
MARKET_API_BASE_PATH = '/data/v1'

API_PATH_DICT = {
    'depth': '%s%s/depth'%(MARKET_BASE_URL, MARKET_API_BASE_PATH),

    'getUserAddress': '%s%s/getUserAddress'%(TRADE_BASE_URL, TRADE_API_BASE_PATH),

    'getAccountInfo': '%s%s/getAccountInfo'%(TRADE_BASE_URL, TRADE_API_BASE_PATH),

    'order': '%s%s/order'%(TRADE_BASE_URL, TRADE_API_BASE_PATH),

    'cancelOrder': '%s%s/cancelOrder'%(TRADE_BASE_URL, TRADE_API_BASE_PATH),

    'getOrder': '%s%s/getOrder'%(TRADE_BASE_URL, TRADE_API_BASE_PATH),

    'getUnfinishedOrdersIgnoreTradeType': '%s%s/getUnfinishedOrdersIgnoreTradeType'%(TRADE_BASE_URL, TRADE_API_BASE_PATH),

    'withdraw': '%s%s/withdraw'%(TRADE_BASE_URL, TRADE_API_BASE_PATH)
}

PARAM_ORDERS = {
    "depth": ["method", "accesskey", "currency", "size"],
    "getAccountInfo": ["method", "accesskey"],
    "getUserAddress": ["method", "accesskey", "currency"],
    "order": ["method", "accesskey", "price", "amount", "tradeType", "currency"],
    "cancelOrder": ["method", "accesskey", "id", "currency"],
    "getOrder": ["method", "accesskey", "id", "currency"],
    "getUnfinishedOrdersIgnoreTradeType": ["method", "accesskey", "currency", "pageIndex", "pageSize"],
    "withdraw": ["method", "accesskey", "amount", "currency", "fees", "receiveAddr", "safePwd"]
}

def get_api_path(name):
    return API_PATH_DICT[name]

class Auth():
    def __init__(self, access_key, secret_key):
        self.access_key = access_key
        self.secret_key = secret_key

    def urlencode(self, meth, params):
        keys = PARAM_ORDERS[meth]
        # keys.sort()
        query = ''
        for key in keys:
            value = params[key]
            query = "%s&%s=%s" % (query, key, value) if len(query) else "%s=%s" % (key, value)
        return query

    def __digest(self, aValue):
        value  = struct.pack("%ds" % len(aValue), aValue.encode("utf8"))
        h = hashlib.sha1()
        h.update(value)
        dg = h.hexdigest()
        return dg.encode("utf8")

    def sign(self, meth, params):
        msg = self.urlencode(meth, params)
        signature = hmac.new(self.__digest(self.secret_key), msg=msg.encode("utf8"), digestmod=hashlib.md5).hexdigest()
        return signature
    
    def sign_params(self, meth, params=None):
        if not params:
            params = {}
        params.update({'method': meth, 'accesskey': self.access_key})
        signature = self.sign(meth, params)
        query = self.urlencode(meth, params)
        # print(params)
        # print(query)
        # print(signature)
        # signature = self.sign(query, self.__digest(self.secret_key))
        return signature, query

class Client():

    def __init__(self, access_key=None, secret_key=None):
        if access_key and secret_key:
            self.auth = Auth(access_key, secret_key)
        else:
            from conf import ACCESS_KEY, SECRET_KEY
            self.auth = Auth(ACCESS_KEY, SECRET_KEY)

    async def get(self, meth, params=None):
        signature, query = self.auth.sign_params(meth, params)
        reqTime = int(1000*time.time())
        url = "%s?%s&sign=%s&reqTime=%s" % (get_api_path(meth), query, signature, reqTime)
        logging.debug("chbtc client get url: %s", url)
        async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout = 5) as resp:
                    resp_text = await resp.text()
                    logging.debug("chbtc resp: %s", resp_text)
                    return json.loads(resp_text)
        # resp = urllib.request.urlopen(url)
        # data = resp.readlines()
        # if len(data):
        #     return json.loads(data[0].decode("utf8"))
