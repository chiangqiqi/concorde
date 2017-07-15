import yaml
import pytest

from .viabtc import Exchange as ViaBTC
from finance.currency import Currency, CurrencyPair

config = yaml.load('../config.yaml')


conf = {'access_key': 'pkey', 'secret_key': 'skey'}
exchange = ViaBTC(conf)

@pytest.mark.asyncio
async def test_get_cash():
    res = await exchange.getCashAsync()
    assert res >= 0

@pytest.mark.asyncio
async def test_get_account_info():
    res = await exchange.getAccountInfo()
    assert res['balances']['ETH'] >= 0

@pytest.mark.asyncio
async def test_get_depth():
    res = await exchange.getQuotes(CurrencyPair.ETH_CNY)
    assert res.asks[0].price >= 0


# @pytest.mark.asyncio
# async def test_sell():
#     res = await exchange.sellAsync(CurrencyPair.ETH_CNY, 0.1, 2000)
    
#     assert res.asks[0].price >= 0
