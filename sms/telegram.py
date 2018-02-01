import requests

class TgMiddleMan:
    boturl = 'http://middleman.ferdinand-muetsch.de/api/messages'
    def __init__(self, addr):
        self.addr = addr

    def send_msg(self, msg):

       # here you go
        req_msg = {'recipient_token': self.addr,
                   'text': msg , 'origin': 'Captain'}

        requests.post(self.boturl, json=req_msg)
