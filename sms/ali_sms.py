import json
import aiohttp
import logging
from urllib.parse import urlencode, quote_plus

class AliSms():
    def __init__(self, config):
        self.config = config

    async def sendOpenOrderSms(self, phonenum, exchange, orderId, amount, price):
        path = self.config['api_url']
        appCode = self.config['app_code']
        signName = self.config['sign_name']
        templateCode = self.config['template_code']
        paramString = '{"name": "%s", "order_id": "%s", "amount": "%.4f", "price": "%.4f"}'%(exchange, 
                                                                                            orderId, 
                                                                                            amount,
                                                                                            price)
        headers = {'Authorization': "APPCODE %s"%(appCode)}
        query = {"ParamString": paramString, "RecNum": phonenum, "SignName": signName, "TemplateCode": templateCode}
        url = "%s?%s"%(path, urlencode(query, quote_via=quote_plus))
        logging.debug("AliSms client get url: %s", url)
        async with aiohttp.ClientSession() as session:
                async with session.get(url, headers = headers, timeout = 20) as resp:
                    resp_text = await resp.text()
                    logging.debug("AliSms client resp: %s", resp_text)
                    try:
                        ret = json.loads(resp_text)
                        return ret
                    except Exception as e:
                        return resp_text

class TgMiddleMan:
    def __init__(self, config):
        self.addr = config['middleman_addr']

    async def sendOpenOrderSms(self, exchange, orderId, amount, price):
        boturl = 'http://middleman.ferdinand-muetsch.de/api/messages'

        msg = "平台 {} 订单 {} 数量 {} 价格 {} 未成功".format(
                exchange, orderId, amount, price
        )
        # here you go
        req_msg = {'recipient_token': self.addr,
                   'text': msg , 'origin': 'Captain'}

        async with aiohttp.ClientSession() as session:
                async with session.post(boturl, json=req_msg) as resp:
                    resp_text = await resp.text()
                    try:
                        ret = json.loads(resp_text)
                        return ret
                    except Exception as e:
                        return resp_text
