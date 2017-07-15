import yaml
import pytest

from .jubi import Exchange as JubiExchange
from finance.currency import Currency, CurrencyPair

config = yaml.load('../config.yaml')

exchange = JubiExchange(conf)

@pytest.mark.asyncio
async def test_sell_bts():
    res = await exchange.buyAsync(CurrencyPair.BTS_CNY, 100.0, 0.5)
    assert int(res) > 0

@pytest.mark.asyncio
async def test_sell_ans():
    res = await exchange.sellAsync(CurrencyPair.ANS_CNY, 4.0, 100.0)
    assert int(res) > 0
