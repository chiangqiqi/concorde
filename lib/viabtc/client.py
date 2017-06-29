import urllib.request
import json
import hmac
import hashlib
import time
import logging
import aiohttp

BASE_URL = 'http://www.viabtc.cn'

API_BASE_PATH = '{}/api/v1'.format(BASE_URL)
API_PATH_DICT = {
    'order': '%s/add',
    'trade_view': '%s/trade_view',
    'trade_list': '%s/trade_list',
    'cancelOrder': '%s/trade_cancel',
    'depth': '%s/market/depth',
    'balances': '%s/balance',
}

def get_api_path(name):
    path_pattern = API_PATH_DICT[name]
    return path_pattern % API_BASE_PATH

import json as complex_json
import requests
from .utils import verify_sign
from .utils import get_sign


class Client(object):
    __headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json'
    }

    def __init__(self, access_id, secret_key):
        self.access_id = access_id
        self.secret_key = secret_key
        self.headers = self.__headers

    def __set_authorization(self, params):
        params['access_id'] = self.access_id
        self.headers['access_id'] = self.access_id
        self.headers['AUTHORIZATION'] = get_sign(params, self.secret_key)

    async def get(self, method, params):
        # method = method.upper()
        url = get_api_path(method)
        self.__set_authorization(params)
        async with aiohttp.ClientSession() as session:
            async with session.get(url,params=params, headers=self.headers) as resp:
                d = await resp.json()
                print(d)
                return d

    async def post(self, meth, url, params):
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout = 20) as resp:
                self.__set_authorization(json)
                result = requests.request(method, url, json=json, headers=self.headers)
                return result
