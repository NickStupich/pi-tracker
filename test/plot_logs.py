import numpy as np
import matplotlib.pyplot as plt
import scipy.signal


log_lines = open('../log.txt').read().split('\n')

adjustments = list(map(lambda s2: float(s2.split(' ')[-1]), filter(lambda s: 'adjustment: ' in s, log_lines)))

n = 100
lp_filter = np.ones((n)) / n

filtered_adjustments = scipy.signal.convolve(adjustments, lp_filter)

print(np.mean(adjustments))
plt.plot(adjustments)
plt.plot(filtered_adjustments)
plt.show()

