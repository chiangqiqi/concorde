#!/usr/bin/env python

"""
Created by bu on 2018-01-17
"""
import time
import hashlib
import json as complex_json
import requests
import logging


class RequestClient(object):
    __headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
    }

    def __init__(self, pkey, skey, headers={}):
        self.access_id = pkey      # replace
        self.secret_key = skey     # replace
        self.headers = self.__headers
        self.headers.update(headers)

    @staticmethod
    def get_sign(params, secret_key):
        sort_params = sorted(params)
        data = []
        for item in sort_params:
            data.append(item + '=' + str(params[item]))
        str_params = "{0}&secret_key={1}".format('&'.join(data), secret_key)
        token = hashlib.md5(str_params.encode('utf8')).hexdigest().upper()
        return token

    def set_authorization(self, params):
        params['access_id'] = self.access_id
        params['tonce'] = int(time.time()*1000)
        self.headers['AUTHORIZATION'] = self.get_sign(params, self.secret_key)

    def request(self, method, url, params={}, data='', json={}):
        method = method.upper()
        if method == 'GET':
            self.set_authorization(params)
            return requests.get(url, params=params, headers=self.headers)
        if method == 'DELETE':
            self.set_authorization(params)
            return requests.delete(url, params=params, headers=self.headers)
        else:
            if data:
                json.update(complex_json.loads(data))
            self.set_authorization(json)
            return requests.request(method, url, json=json, headers=self.headers)

# from datetime import datetime
import time       

class Client:
    def __init__(self, pkey, skey):
        self.auth = RequestClient(pkey, skey)
        self._pkey = pkey
        
    def get_account(self):
        resp = self.auth.request('GET', 'https://api.coinex.com/v1/balance/')
        return resp.json()

    def trade(self, market, price, amt, ttype):
        price = '%.7f' % (price)

        data = {
            "amount": amt,
            "price": price,
            "type": ttype,
            "market": market
        }
        
        resp = self.auth.request(
            'POST',
            'https://api.coinex.com/v1/order/limit',
            json=data,
        )
        logging.info('place {} order in market {} at price {} with amt {}'.format(ttype, market, price, amt))
        return resp.json()
    
    def get_orders(self, market):
        """
        Get current orders
        """ 
        tonce = int(time.time() * 1000)
        data = {
            'market' : market, 
            'access_id': self._pkey,
            'page': 1,
            'limit': 100,
            'tonce': tonce
        }
        resp = self.auth.request(
            'GET', 
            'https://api.coinex.com/v1/order/pending',
            params = data
        )
        return resp

    def delete_order(self, order_id, market):
        """Cancel an order 
        """ 
        tonce = int(time.time() * 1000)
        data = {
            'access_id': self._pkey,
            'id': order_id, 
            'market': market,
            'tonce': tonce
        }
        resp = self.auth.request(
            'DELETE',
            'https://api.coinex.com/v1/order/pending',
            params=data
        )
        return resp.json()
        
    
    def depth(self, market):
        resp = self.auth.request(
            'GET',
            'https://api.coinex.com/v1/market/depth',
            params={'market': market, 'merge': 0}
        )
        return resp.json()

    def cancel_all_orders(self, market):
        resp = self.get_orders(market)
        return [self.delete_order(d['id'], 'LTCBTC') for d in resp.json()['data']['data']]
