select sum(price*qty)/sum(qty) as avgprice, sum(qty)
from btcusdt
where time > '2017-12-20 00:00:00'
group by isBuyer;

-- all time profit 
select sum(price*qty)/sum(qty) as avgprice, sum(qty)
from btcusdt
group by isBuyer;
