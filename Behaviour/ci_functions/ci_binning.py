import pandas as pd
import numpy as np

class ci_binning:
    bins=None
    values=None
    def __init__(self,values,max_cat:int=20):
        
        self.values=values
        x_u=np.array(sorted(list(set(values))))
        if len(x_u)<=max_cat:
            self.bins=x_u
        else:
            self.bins=x_u
        
