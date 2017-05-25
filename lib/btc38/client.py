import urllib.request
import json
import hmac
import hashlib
import time
import logging
import aiohttp


# http://api.btc38.com/v1/getMyBalance.php
BASE_URL = 'http://api.btc38.com'


API_BASE_PATH = '/v1'
API_PATH_DICT = {

    'order': '%s/submitOrder.php',

    'openOrders': '%s/getOrderList.php',

    'cancelOrder': '%s/cancelOrder.php',

    'depth': '%s/depth.php',

    'balances': '%s/getMyBalance.php',
}

def get_api_path(name):
    path_pattern = API_PATH_DICT[name]
    return path_pattern % API_BASE_PATH

class Auth():
    def __init__(self, access_key, secret_key, user_id):
        self.access_key = access_key
        self.secret_key = secret_key
        self.user_id = user_id

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
        signature = hmac.new(self.secret_key.encode("utf8"), msg=msg.encode("utf8"), digestmod=hashlib.md5).hexdigest()
        return signature

    def sign_params(self, params=None):
        if params is None:
            params = {}
        tonce = int(time.time())
        params.update({'time': tonce, 'key': self.access_key})
        query = self.urlencode(params)
        msg = "%s_%s_%s_%s"%(self.access_key, self.user_id, self.secret_key, tonce)
        # signature = hmac.new(self.secret_key.encode("utf8"), msg=msg.encode("utf8"), digestmod=hashlib.md5).hexdigest()
        signature = hashlib.md5(msg.encode('utf8')).hexdigest()
        return signature, query

class Client():

    def __init__(self, access_key, secret_key, user_id):
        self.auth = Auth(access_key, secret_key, user_id)


    async def get(self, meth, params=None):
        path = get_api_path(meth)
        signature, query = self.auth.sign_params(params)
        url = "%s%s?%s&md5=%s" % (BASE_URL, path, query, signature)
        logging.debug("btc38 client get url: %s", url)
        header = {'Content-Type': 'application/x-www-form-urlencoded',
                  'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"}
        async with aiohttp.ClientSession() as session:
                async with session.get(url, headers = header, timeout = 20) as resp:
                    resp_text = await resp.text()
                    logging.debug("btc38 resp: %s", resp_text)
                    try:
                        ret = json.loads(resp_text)
                        return ret
                    except Exception as e:
                        return resp_text

    async def post(self, meth, params=None):
        path = get_api_path(meth)
        signature, query = self.auth.sign_params(params)
        url = "%s%s" % (BASE_URL, path)
        data = "%s&md5=%s" % (query, signature)
        header = {'Content-Type': 'application/x-www-form-urlencoded',
                  'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"}
        logging.debug("btc38 client post url: %s, data: %s, header: %s", url, data, header)
        async with aiohttp.ClientSession() as session:
                async with session.post(url, data = data.encode("utf8"), headers = header, timeout = 20) as resp:
                    resp_text = await resp.text()
                    logging.debug("btc38 resp: %s", resp_text)
                    try:
                        ret = json.loads(resp_text)
                        return ret
                    except Exception as e:
                        return resp_text
