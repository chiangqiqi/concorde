#coding=utf-8
#加载必要的库
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.finance import quotes_historical_yahoo_ohlc, candlestick_ohlc, candlestick2_ohlc
from datetime import datetime

data_path = "./result/result_sim0.85_bars100_ev0.000040_loss_line1.000000_2016_12.csv"
# data_path = "./result/sim0.90_bars30_ev0.000040_loss_line1.000000_2016_02.csv"
# data_path = "./result/action_sim0.85_bars100_ev0.000040_loss_line1.000000_2016_12.csv"

def load_csv(csv_path):
  # df = pd.read_csv(csv_path)
  df = pd.read_csv(csv_path, parse_dates=["Timestamp"], infer_datetime_format=True)
  return df

def sim(df1, df2):
	action = False
	df1_long = False
	df2_long = False
	target_profit = 0.003
	cash = 1000
	start_point = []
	exit_point = []
	i = 0
	while i < len(df1):
		start_fee = (cash * 2) * 0.0025
		exit_fee = cash * (1.0 + target_profit) * 0.0025 * 2
		diff = abs(df1.iloc[i]["Close"] - df2.iloc[i]["Close"])
		direction = np.sign(df1.iloc[i]["Close"] - df2.iloc[i]["Close"])
		if ((diff - start_fee - exit_fee) > 1e-9):
			start_point.append(df1.iloc[i]["Timestamp"])
			s1_start = df1.iloc[i]
			s2_start = df2.iloc[i]
			df1_direction = np.sign(s2_start["Close"] - s1_start["Close"])
			df2_direction = np.sign(s1_start["Close"] - s2_start["Close"])
			print("start(%s), df1.close(%f), df2.close(%f)"
				%(s1_start["Timestamp"], s1_start["Close"], s2_start["Close"]))
			i += 1
			while i < len(df1) and (df1.iloc[i]["Close"] - df2.iloc[i]["Close"]) * direction > 0:
				i += 1
			if i < len(df1):
				exit_point.append(df1.iloc[i]["Timestamp"])
				s1_end = df1.iloc[i]
				s2_end = df2.iloc[i]
				df1_earn_ratio = (s1_end["Close"] - s1_start["Close"]) / s1_start["Close"] * df1_direction
				df1_earn_cash = cash * df1_earn_ratio
				df1_earn_stop_fee = df1_earn_cash * 0.0025

				df2_earn_ratio = (s2_end["Close"] - s2_start["Close"]) / s2_start["Close"] * df2_direction
				df2_earn_cash = cash * df2_earn_ratio
				df2_earn_stop_fee = df2_earn_cash * 0.0025

				total = cash + df1_earn_cash + df2_earn_cash - start_fee - df1_earn_stop_fee - df2_earn_stop_fee
				print("exit(%s), df1.close(%f), df2.close(%f), df1_earn_cash(%f), df2_earn_cash(%f), total(%f)"
					%(s1_end["Timestamp"], s1_end["Close"], s2_end["Close"], df1_earn_cash, df2_earn_cash,total))
		else:
			i += 1
	plt.figure()
	plt.plot(df1["Timestamp"], df1["Close"])
	plt.plot(df2["Timestamp"], df2["Close"])
	for x in start_point:
		plt.axvline(x)
	for x in exit_point:
		plt.axvline(x, color="r")
	plt.show()
	return start_point

def filter(df1, df2):
	filtered_df1 = df1[~(df1["Close"] > 9999)]
	filtered_df1.index = filtered_df1["Timestamp"]
	filtered_df2 = df2[~(df2["Close"] > 9999)]
	filtered_df2.index = filtered_df2["Timestamp"]

	common_time = np.sort(list(set(filtered_df1["Timestamp"]).intersection(set(filtered_df2["Timestamp"]))))
	# return(filtered_df1, filtered_df2)
	return (filtered_df1.filter(common_time, axis=0), filtered_df2.filter(common_time, axis=0))

def determine_mahr():
	data_path = "./result/action_sim0.85_bars100_ev0.000040_loss_line1.000000_2016.csv"
	def calculate_mahr(df, mahr_long_num, mahr_short_num):
		mahr_long = pd.rolling_mean(df["return"], mahr_long_num)
		mahr_short = pd.rolling_mean(df["return"], mahr_short_num)
		# mahr_long.index = df["datetime"]
		# mahr_short.index = df["datetime"]
		return (mahr_long.iloc[mahr_long_num-1:], mahr_short.iloc[mahr_short_num-1:])

	plt.figure()
	df = load_csv(data_path)
	# df = df.iloc[2600:3000]
	# plt.subplot(211)
	# plt.plot(df["return"])
	# plt.subplot(212)
	(mahr_long, mahr_short) = calculate_mahr(df, 30, 10)
	plt.plot(df.index, df["return"])
	plt.plot(mahr_long.index,mahr_long, "r")
	plt.plot(mahr_short.index,mahr_short, "g")
	# dates = matplotlib.dates.date2num(list(mahr_long.index))
	# matplotlib.pyplot.plot_date(dates, mahr_long)
	# dates = matplotlib.dates.date2num(list(mahr_short.index))
	# matplotlib.pyplot.plot_date(dates, mahr_short)
	plt.show()
# determine_mahr()
 
 
kraken = load_csv('./kraken.csv')
bitstamp = load_csv('./bitstamp.csv')
(df1, df2) = filter(kraken, bitstamp)
# print(df1)
# print(df2)
sim(df1, df2)
# plt.figure()
# data_path = "./result/action_sim0.85_bars100_ev0.000040_loss_line1.000000_2016_all.csv"
# df = load_csv(data_path)
# plt.plot(df["datetime"], df["return"], "k")
# data_path = "tmp.csv"
# data_path = "./result/action_12_3_sim0.80_bars100_ev0.000060_loss_line1.000000_1hour_2016.csv"
# df = load_csv(data_path)
# plt.plot(df["datetime"], df["return"], "r")
# plt.show()



