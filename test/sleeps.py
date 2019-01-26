from datetime import datetime
import time
import numpy as np

def eval_sleeping_accuracy(sleep_func, sleep_time_us, n):
    counts = np.zeros(n)
    
    for i in range(-10, n):
        if i < 0:
            continue
        start = datetime.now()
        sleep_func(sleep_time_us)
        end = datetime.now()
        delta = end - start
        us = delta.seconds * 1000000 + delta.microseconds
        counts[i] = us
        
    print(np.mean(counts), np.std(counts), np.min(counts), np.max(counts))
    
def sleep_func2(us, offset_us = 34):
    start = datetime.now()
    
    while(1):
        now = datetime.now()
        delta = now - start
        us_elapsed = delta.seconds * 1000000 + delta.microseconds
        if us_elapsed + offset_us >= us:
            break

if __name__ == "__main__":
    time_us = 900
    
    sleep_func1 = lambda t: time.sleep(t / 1000000.)
    #sleep_func2 = lambda t: sleep(t / 1000000.)
    
    #eval_sleeping_accuracy(sleep_func1, time_us, 10000)
    eval_sleeping_accuracy(sleep_func2, time_us, 100000)
    