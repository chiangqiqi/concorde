from finance.quotes import Quotes, OrderBookItem
import math

def get_order_book_item(x):
    return OrderBookItem(price = float(x[0]), amount = float(x[1]))

def _floor(num, precision=4):
    multiplier = math.pow(10.0, precision)
    return math.floor(num * multiplier) / multiplier
