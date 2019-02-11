import numpy as np
import matplotlib.pyplot as plt


log_lines = open('../log.txt').read().split('\n')

adjustments = list(map(lambda s2: float(s2.split(' ')[-1]), filter(lambda s: 'adjustment: ' in s, log_lines)))

print(np.mean(adjustments))
plt.plot(adjustments); plt.show()

