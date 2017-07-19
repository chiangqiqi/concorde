#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created by bu on 2017-05-10
"""
from __future__ import unicode_literals
import sys
import datetime
import decimal
import hashlib
from urllib.parse import urlencode

unicode_type = str
bytes_type = bytes


def verify_sign(obj, secret_key, signature):
    return signature == get_sign(obj, secret_key)


def get_sign(obj, secret_key):
    """生成签名"""
    # 签名步骤一：按字典序排序参数,format_biz_query_para_map
    String = format_biz_query_para_map(obj)
    
    # 签名步骤二：在string后加入KEY
    String = "{0}&secret_key={1}".format(String, secret_key).encode('utf-8')
    # 签名步骤三：MD5加密
    String = hashlib.md5(String).hexdigest()
    # 签名步骤四：所有字符转为大写
    result_ = String.upper()
    return result_


def format_biz_query_para_map(para_map):
    """格式化参数，签名过程需要使用"""
    if isinstance(para_map, str):
        return para_map
    # paraMap = to_unicode(para_map)
    slist = sorted(para_map)
    buff = []
    for k in slist:
        v = para_map[k]
        if v is None or v == "":
            # 为空直接跳过
            continue
        buff.append("{0}={1}".format(k, str(v)))
    return "&".join(buff)


def to_unicode(data, encoding='UTF-8'):
    """Convert a number of different types of objects to unicode."""
    type_to_str = (datetime.datetime, decimal.Decimal)

    if isinstance(data, type_to_str):
        data = str(data)
    elif hasattr(data, '__iter__'):
        if isinstance(data, list):
            # Assume it's a one list data structure
            data = [to_unicode(i, encoding) for i in data]
        else:
            # We support 2.6 which lacks dict comprehensions
            if hasattr(data, 'items'):
                data = list(data.items())
            data = dict([(to_unicode(k, encoding), to_unicode(v, encoding)) for k, v in data])
    return data
