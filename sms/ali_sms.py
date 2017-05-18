import urllib
import json
import urllib.request
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