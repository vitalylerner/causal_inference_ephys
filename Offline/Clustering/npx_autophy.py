import pandas as pd
import numpy as np
pd.options.mode.chained_assignment = None
import os
#graphical pachages for debugging, commented out when not in debugging mode
from bokeh.plotting import figure as bk_figure, output_file as bk_output_file, save as bk_save, show as bk_show
from bokeh.models import Label as bk_Label
from bokeh.layouts import row as b
import multiprocessing

class spikes_classifier:
    kspath=""
    paths={}
    spike_times=None
    spike_clusters=None
    spike_positions=None
    cluster_group=None
    
    trials=None
    
    
    raster=None
    def u_list(self):
        return sorted(list(set(self.spike_clusters))) 
    
    def u_table(self)    :
        u=self.u_list()
        self.build_raster()
        r=self.raster
        n=[len(r_) for r_ in r]    
        tbl=pd.DataFrame({'unit':u,'n_spikes':n})
        return tbl
    
    def u_spikes(self,u:int):
        return self.spike_times[self.spike_clusters==u]
    
    def build_raster(self):
        sp_t=self.spike_times
        sp_c=self.spike_clusters
        units=self.u_list()
        with multiprocessing.Pool(16) as p:
           self.raster=list( p.map(self.u_spikes,units))
        #self.raster=map(self.u_spikes,units)
        
    def validate_files(self):
        for f in self.paths.keys():
            if not os.path.exists(self.paths[f]):
                raise FileExistsError (self.paths[f] + ' does not exist')
                
    def __init__(self,path:str):
        p={}
        p['folder']=path        

        p['Trials']            = path+'/Trials.csv'
        p['spike_times']       = path+'/spike_times.npy'
        p['spike_clusters']    = path+'/spike_clusters.npy'
        p['cluster_group']     = path+'/cluster_group.tsv'
        p['spike_positions']   = path+'/spike_positions.npy'
        self.paths=p
        self.validate_files()
        
        self.trials=pd.read_csv(p['Trials'])
        
        self.spike_times=np.load(p['spike_times'])
        self.spike_clusters=np.load(p['spike_clusters'])
        self.spike_positions=np.load(p['spike_positions'])
        self.cluster_group=pd.read_csv(p['cluster_group'],sep='\t')
    
    def split(self):
        self.build_raster()
        print (self.raster[1])
        
        
if __name__=="__main__":
    
    sc=spikes_classifier("C:/Sorting/m42c539/kilosort4")
    t=sc.u_table()
    print (t)