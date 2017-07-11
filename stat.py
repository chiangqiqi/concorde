import json
import fileinput

alphas = []
pre_dircetion = None
reverse = 0

earn = {}
alpha_exchange = {}
for line in fileinput.input():
	data = json.loads(line)
	alpha = float(data['alpha'])
	alphaFlat = float(data['alphaFlat'])
	print(alphaFlat)
