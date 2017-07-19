import yaml
import pytest

from .jubi import Exchange as JubiExchange
from finance.currency import Currency, CurrencyPair

config = yaml.load(open('config.yaml', encoding='utf8'))

conf = list(filter(lambda x: x['name'] == 'jubi', config['exchange']))[0]

exchange = JubiExchange(conf)

@pytest.mark.asyncio
async def test_sell_bts():
    res = await exchange.buyAsync(CurrencyPair.BTS_CNY, 100.0, 0.5)
    assert int(res) > 0

@pytest.mark.asyncio
async def test_sell_ans():
    res = await exchange.sellAsync(CurrencyPair.ANS_CNY, 4.900001, 371.234567)
    assert int(res) > 0
    
@pytest.mark.asyncio
async def test_get_quotes():
    res = await exchange.getQuotes(CurrencyPair.ANS_CNY)
    assert res.asks[0].price >= 0
