#Decorator for timed debugging
from time import time
def debug_timing(function):
    def timed_execution(*args, **kwargs):
        start = time()
        returns = function(*args, **kwargs)
        ex_time = (time()-start) * 1000
        print(f'{function.__name__} took {ex_time}ms')
        return returns
    return timed_execution