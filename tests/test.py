# from arbitrage import amount_and_price
from arbitrage import polo,binance

ask = [[100 , 0.1], [101, 0.2], [102, 0.2]]
bid = [[101, 0.1], [100.5, 0.1], [99, 0.1]]


def test_amt_price():
    p1,p2,amt = amount_and_price(ask, bid)

    # import pdb; pdb.set_trace()

def test_balance():
    b_balance = binance.balance()
    p_balance = polo.balance()

    binance.trade("ETHUSDT", 420, 0.01101, "Sell")
    # info = binance.client.get_exchange_info()
    import pdb; pdb.set_trace()
    # binance.trade("ETHUSDT", 500, 0.1, "Sell")
   
def test_float_precision():
    import pdb; pdb.set_trace()
    
# test_amt_price()
# test_balance()

test_float_precision()
