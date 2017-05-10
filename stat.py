from datetime import datetime
file_path = './tmp.txt'
alphas = []
pre_dircetion = None
reverse = 0

from_time = datetime(2017,5,6,14,0,0)
to_time = datetime(2017,5,7,14,0,0)
from_time = datetime(2017,5,9,0,0,0)
to_time = datetime(2018,5,9,13,0,0)
earn = {}
with open(file_path, 'r') as fn:
	for line in fn.readlines():
		dt_str = line[1:20]
		dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
		if dt < from_time or dt > to_time:
			continue
		#print(dt)

		idx = line.find("arbitrage")
		sub_line = line[:idx]
		idx2 = sub_line.rfind("(")
		cur_direction = sub_line[idx2:]
		if cur_direction not in earn:
			earn[cur_direction] = 0

		if pre_dircetion is not None and pre_dircetion != cur_direction:
			reverse += 1
		pre_dircetion = cur_direction
		alpha = float(line.split("alpha = ")[-1])
		alphaFlat = float(line.split("alpha_flat=")[-1].split(',')[0])
		earn[cur_direction] += alphaFlat
		if alpha > 0.0 and alpha <= 1.0:
			alphas.append(alpha)

print("reverse: %d"%(reverse))
print("mean: %f"%(sum(alphas)/len(alphas)))
print("max: %f"%(max(alphas)))
print("min: %f"%(min(alphas)))
print(earn)
