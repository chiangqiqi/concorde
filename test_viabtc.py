from exchange.viabtc import Exchange
import asyncio

pkey = '88BAB6BFD0CE44AB97CE99857B1D21EF'
skey = 'C3270BC1FB004F2B80F85AA62AB1E798BAB843EC99EF1A48' 

config = {'access_key': pkey, 'secret_key': skey}

exchange = Exchange(config)

loop = asyncio.get_event_loop()
loop.run_until_complete(exchange.getAccountInfo())

