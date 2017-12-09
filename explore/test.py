from arbitrage import amount_and_price

ask = [[100 , 0.1], [101, 0.2], [102, 0.2]]
bid = [[101, 0.1], [100.5, 0.1], [99, 0.1]]


def test_amt_price():
    p1,p2,amt = amount_and_price(ask, bid)

    import pdb; pdb.set_trace()


test_amt_price()
