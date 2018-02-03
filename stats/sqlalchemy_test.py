from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy import Float,Boolean
from sqlalchemy import create_engine
from sqlalchemy import desc
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import sys

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
    coin_from = Column(String(length=16))
    coin_to = Column(String(length=16))
    order_id = Column(Integer)
    commission_asset = Column(String(length=16))
    commission = Column(Float)
    is_best_match = Column(Boolean)
    is_buyer = Column(Boolean)
    is_maker= Column(Boolean)
    price = Column(Float)
    qty = Column(Float)
    time = Column(DateTime)


engine = create_engine('postgresql://qiqi:qiqi123@118.190.202.41:5432/trader_test')

from analysis import client

def save_recs(session, recs, coina, coinb):
    for rec in recs:
        print(rec)

        to_save = TradeHistory(
            tid=rec['id'], order_id=rec['orderId'], commission=rec['commission'],
            commission_asset= rec['commissionAsset'],is_buyer= rec['isBuyer'],
            price=rec['price'], qty=rec['qty'],
            time=datetime.fromtimestamp(rec['time']/1000),
            is_maker= rec['isMaker'], is_best_match=rec['isBestMatch'],
            coin_from=coina, coin_to=coinb
        )
        instance = session.query(TradeHistory).filter_by(tid=rec['id']).first()
        if instance:
            print('already exists')
        else:
            session.add(to_save)
        # import ipdb; ipdb.set_trace()
    session.commit()


def lastest_order(session, coina, coinb):
    """the max id of the stored order
    """
    rec = session.query(TradeHistory).filter(
        TradeHistory.coin_from == coina,
        TradeHistory.coin_to == coinb
    ).order_by(desc(TradeHistory.tid)).first()

    import ipdb; ipdb.set_trace()
    return rec.tid

def fetch_all_trades(coina, coinb, last_id=0):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    last_id = lastest_order(session, coina, coinb)

    res = client.get_my_trades(symbol=coina + coinb, fromId=last_id)
    # import ipdb; ipdb.set_trace()
    save_recs(session, res, coina, coinb)

    while(len(res) == 500):
        last_id = int(res[-1]['id'])
        res = client.get_my_trades(symbol=coina + coinb, fromId=last_id)
        save_recs(session, res, coina, coinb)

def main():
    coina,coinb = sys.argv[1],sys.argv[2]

    # res = client.get_my_trades(symbol=coina + coinb, fromId=0)

    fetch_all_trades(coina, coinb)


from collections import defaultdict
def profit_stats(from_date='2018-02-03', to_date='2018-03-01', coin_pair=None):
    # for every trade, get

    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    coina,coinb = coin_pair
    if coin_pair is not None:
         cursor = session.query(
            TradeHistory
        ).filter(
            TradeHistory.time >= from_date,
            TradeHistory.time < to_date,
            TradeHistory.coin_from==coina,
            TradeHistory.coin_to==coinb
        ).order_by(TradeHistory.time).all()
    else:
        cursor = session.query(
            TradeHistory
        ).filter(
            TradeHistory.time >= from_date,
            TradeHistory.time < to_date,
        ).order_by(TradeHistory.time).all()

    balance = defaultdict(float)

    for rec in cursor:
        if rec.is_buyer:
            balance[rec.coin_from] += rec.qty
            balance[rec.coin_to] -= rec.qty * rec.price
        else:
            balance[rec.coin_from] -= rec.qty
            balance[rec.coin_to] += rec.qty * rec.price

        balance[rec.commission_asset] -= rec.commission

    print(dict(balance))

    # TradeHistory.__table__.create(engine)

if __name__ == '__main__':
    # try:
    #     ModelBase.metadata.create_all(engine)
    # except:
    #     pass
    # main()
    markets =  [('ETH', 'BTC'), ('BTC', 'USDT'), ('ICX', 'BTC'), ('ICX', 'ETH')]
    for symbol in markets:
        print(symbol)
        profit_stats(coin_pair=symbol)
