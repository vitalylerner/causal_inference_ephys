from numba import jit, cuda 
import numpy as np 
# to measure exec time 
from timeit import default_timer as timer 

# normal function to run on cpu 
def func(a):	
	
	b=np.argsort(a)	
	return b[:100]

# function optimized to run on gpu 
@jit(target_backend='cuda',nopython=True)						 
def func2(a): 			
	
	b=np.argsort(a)
	return b[:100]
	
if __name__=="__main__": 

	n = 50000000	
	a = np.random.random(n).astype(np.float16)
	start = timer() 
	b=func(a) 
	print("without GPU:", timer()-start)	 
	
	start = timer() 
	b=func2(a) 
	print("with GPU:", timer()-start) 
