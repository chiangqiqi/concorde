import urllib.request
import json
import hmac
import hashlib
import time
import logging
import aiohttp


# http://api.jubi.com/v1/getMyBalance.php
BASE_URL = 'http://www.jubi.com'


API_BASE_PATH = '/api/v1'
API_PATH_DICT = {

    'order': '%s/trade_add',

    'trade_view': '%s/trade_view',

    'trade_list': '%s/trade_list',

    'cancelOrder': '%s/trade_cancel',

    'depth': '%s/depth',

    'balances': '%s/balance',
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
        signature = hmac.new(self.secret_key.encode("utf8"), msg=msg.encode("utf8"), digestmod=hashlib.md5).hexdigest()
        return signature

    def sign_params(self, params=None):
        if params is None:
            params = {}
        tonce = int(time.time())
        params.update({'nonce': tonce, 'key': self.access_key})
        query = self.urlencode(params)
        logging.debug("jubi msg for encode: %s", query)
        # msg = "%s_%s_%s_%s"%(self.access_key, self.user_id, self.secret_key, tonce)
        md5Key = hashlib.md5(self.secret_key.encode("utf8")).hexdigest()
        signature = hmac.new(md5Key.encode("utf8"), msg=query.encode("utf8"), digestmod=hashlib.sha256).hexdigest()
        # signature = hashlib.md5(msg.encode('utf8')).hexdigest()
        return signature, query

class Client():

    def __init__(self, access_key, secret_key):
        self.auth = Auth(access_key, secret_key)


    async def get(self, meth, params=None):
        path = get_api_path(meth)
        signature, query = self.auth.sign_params(params)
        url = "%s%s?%s&signature=%s" % (BASE_URL, path, query, signature)
        logging.debug("jubi client get url: %s", url)
        async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout = 20) as resp:
                    resp_text = await resp.text()
                    logging.debug("jubi resp: %s", resp_text)
                    try:
                        ret = json.loads(resp_text)
                        return ret
                    except Exception as e:
                        return resp_text

    async def post(self, meth, params=None):
        path = get_api_path(meth)
        signature, query = self.auth.sign_params(params)
        url = "%s%s" % (BASE_URL, path)
        data = "%s&signature=%s" % (query, signature)
        header = {'Content-Type': 'application/x-www-form-urlencoded'}
        logging.debug("jubi client post url: %s, data: %s, header: %s", url, data, header)
        async with aiohttp.ClientSession() as session:
                async with session.post(url, data = data.encode("utf8"), headers = header, timeout = 20) as resp:
                    resp_text = await resp.text()
                    logging.debug("jubi resp: %s", resp_text)
                    try:
                        ret = json.loads(resp_text)
                        return ret
                    except Exception as e:
                        return resp_text
