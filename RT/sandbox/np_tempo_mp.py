# -*- coding: utf-8 -*-
"""
Created on Tue Jan 23 17:49:09 2024

@author: DeAngelis Lab
"""

from multiprocessing import Pool
from multiprocessing import active_children, cpu_count

ncores=cpu_count()
Q=[queue.Queue() for core in range(ncores)]
global_stop=False
def npx_data_processor(procId:int):
   while not global_stop:
       if not Q[procId].empty():
          x=Q[procId].get()
          if procId==0:
              #if ==2:
              print ("[python] q0 size is ",Q[procId].qsize())