import asyncio
import yaml
import importlib

config = yaml.load(open('config.yaml', encoding='utf8'))

def name2exchange(name):
    exch_config = list(filter(lambda x: x['name'] == name, config['exchange']))[0]
    e = importlib.import_module("exchange.%s"%name).Exchange(exch_config)
    return e


def async_test(f):
    """
    a simple wrapper for coroutine which should live in a event loop
    """
    def wrapper(*args, **kwargs):
        coro = asyncio.coroutine(f)
        future = coro(*args, **kwargs)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(future)
    return wrapper

