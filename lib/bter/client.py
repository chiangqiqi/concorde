import urllib.request
import json
import hmac
import hashlib
import time
import logging
import aiohttp

# http://data.bter.com/api2/1/orderBook/bts_cny
BASE_URL = 'http://data.bter.com'


API_BASE_PATH = '/api2/1'
API_PATH_DICT = {

    'buy': '%s/private/buy',

    'sell': '%s/private/sell',

    'getOrder': '%s/private/getOrder',

    'openOrders': '%s/private/openOrders',

    'cancelOrder': '%s/private/cancelOrder',

    'depth': '%s/orderBook/%%s',

    'balances': '%s/private/balances',

    'deposite_address': '%s/private/depositAddress',

    'withdraw': '%s/private/withdraw'
}

def get_api_path(name):
    path_pattern = API_PATH_DICT[name]
    return path_pattern % API_BASE_PATH

class Auth():
    def __init__(self, access_key, secret_key):
        self.access_key = access_key
        self.secret_key = secret_key

    def urlencode(self, params):
        keys = params.keys()
        # keys.sort()
        query = ''
        for key in keys:
            value = params[key]
            if key != "orders":
                query = "%s&%s=%s" % (query, key, value) if len(query) else "%s=%s" % (key, value)
            else:
                #this ugly code is for multi orders API, there should be an elegant way to do this
                d = {key: params[key]}
                for v in value:
                    ks = v.keys()
                    ks.sort()
                    for k in ks:
                        item = "orders[][%s]=%s" % (k, v[k])
                        query = "%s&%s" % (query, item) if len(query) else "%s" % item
        return query

    def sign(self, params=None):
        query = self.urlencode(params)
        msg = query
        signature = hmac.new(self.secret_key.encode("utf8"), msg=msg.encode("utf8"), digestmod=hashlib.sha512).hexdigest()
        return signature

    def sign_params(self, params=None):
        if not params:
            params = {}
        params.update({'tonce': int(1000*time.time())})
        query = self.urlencode(params)
        signature = self.sign(params)
        return signature, query
        
class Client():

    def __init__(self, access_key=None, secret_key=None):
        if access_key and secret_key:
            self.auth = Auth(access_key, secret_key)
        else:
            from conf import ACCESS_KEY, SECRET_KEY
            self.auth = Auth(ACCESS_KEY, SECRET_KEY)


    async def get(self, path, params=None):
        signature, query = self.auth.sign_params(params)
        url = "%s%s?%s&signature=%s" % (BASE_URL, path, query, signature)
        logging.debug("bter client get url: %s", url)
        async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout = 20) as resp:
                    resp_text = await resp.text()
                    logging.debug("bter resp: %s", resp_text)
                    try:
                        ret = json.loads(resp_text)
                        return ret
                    except Exception as e:
                        return resp_text
        # req = urllib.request.Request(url, headers = header)
        # resp = urllib.request.urlopen(req)
        # data = resp.readlines()
        # # print(data)
        # if len(data):
        #     return json.loads(data[0].decode("utf8"))

    async def post(self, path, params=None):
        # print(params)
        signature, query = self.auth.sign_params(params)
        url = "%s%s" % (BASE_URL, path)
        data = "%s" % (query)
        header = {'KEY': self.auth.access_key, 'SIGN': signature, 'Content-Type': 'application/x-www-form-urlencoded'}
        logging.debug("bter client post url: %s, data: %s, header: %s", url, data, header)
        async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data.encode("utf8"), headers=header, timeout=10) as resp:
                    resp_text = await resp.text()
                    logging.debug("bter resp: %s", resp_text)
                    try:
                        ret = json.loads(resp_text)
                        return ret
                    except Exception as e:
                        return resp_text
        # req = urllib.request.Request(url, data.encode("utf8"), headers = header)
        # resp = urllib.request.urlopen(req)
        # data = resp.readlines()
        # # print(data)
        # if len(data):
        #     return json.loads(data[0].decode("utf8"))
