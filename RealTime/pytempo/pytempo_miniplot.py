import pandas as pd
import pyqtgraph as pg

class pytempo_miniplot:
    ax=None    
    def __init__(self,ax:pg.PlotWidget):
        self.ax=ax
        pass

    def plot_depth(self,D:pd.DataFrame):
        u_sigma=sorted(list(set(D.vert_disp)))
        #clr=['black','green','red','blue']
        #for isigma,sigma in enumerate(u_sigma):
        #    d=D[D.vert_disp==sigma]
        
        d2=D.groupby(['disp_incr']).mean().reset_index()
        self.ax.clear()
        self.ax.plot(d2['disp_incr'], d2['chosen_target']-1, pen='lightgrey', symbol='o', symbolBrush='darkgrey')
        
        self.ax.setLabel('bottom', 'disp-incr')
        self.ax.setLabel('left', 'prop "near"')
        #self.ax.addLegend()
        #self.ax.show()

    def plot(self,protocol:int=154,type:str='depth',D:pd.DataFrame=None):
        if protocol==154:
            if type=='depth':
                self.plot_depth(D)

if __name__=='__main__':
    print ('do not use this file directly')