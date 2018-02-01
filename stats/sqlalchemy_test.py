from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy import Float,Boolean
ModelBase = declarative_base()

class TradeHistory(ModelBase):
    """date is like
     {'commission': '0.08285806',
    'commissionAsset': 'BNB',
    'id': 1925591,
    'isBestMatch': True,
    'isBuyer': True,
    'isMaker': False,
    'orderId': 9815671,
    'price': '15773.07000000',
    'qty': '0.03080900',
    'time': 1513228880628} 
    """
    __tablename__ = "trade_history"

    tid = Column(Integer, primary_key=True)
    commissionAsset = Column(String(length=16))
    commission = Column(Float)
    isBestMatch = Column(Boolean)
    isBuyer = Column(Boolean)
    orderId = Column(Integer)
    price = Column(Float)
    qty = Column(Float)
    

from sqlalchemy import create_engine
engine = create_engine('postgresql://qiqi:qiqi123@118.190.202.41:5432/trader_test')

from analysis import client

# if __name__ == '__main__':
def main():
    res = client.get_my_trades(symbol='BTCUSDT')
    for rec in res:
        print(rec)
        to_save = TradeHistory(
            tid=rec['id'], order_id=rec['orderId'], commision=rec['commission'],
            commissionAsset= rec['commissionAsset'],isBuyer= rec['isBuyer'],
            isMaker= rec['isMaker'])
        to_save.insert()
