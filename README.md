# arbitrage

## 用法 ##

```
python arbitrage.py ETH
```

## TESTS ##

```
pytests  -v  --pdb tests/test_exchanges.py 
```

caution, test will do real orders, do with your own risk.

测试里有一些测试可以改掉，现在并不是所有的接口都可以用， `GET` 的功能可以随便测试，测试 `buy` 或者 `sell`
的时候注意价格和数量，小心价格问题带来损失。
