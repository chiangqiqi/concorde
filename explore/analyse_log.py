import fileinput
import re

def parse_price(s):
    res = re.findall( r'\d+\.*\d*', s)
    return list(res)


print("huobi_ask,huobi_bid,bian_ask,bian_bid")
def gen_data():
    res = []
    for line in fileinput.input():
        timestr,left = line[:23],line[24:]

        if left.startswith('binance'):
            res.extend(parse_price(left))
        elif left.startswith('huobi'):
            if len(res) == 2:
                res.extend(parse_price(left))
                print(",".join(res))

            res = []

gen_data()
