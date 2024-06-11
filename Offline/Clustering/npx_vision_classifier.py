import pandas as pd
import numpy as np
pd.options.mode.chained_assignment = None
import os
#graphical pachages for debugging, commented out when not in debugging mode
from bokeh.plotting import figure as bk_figure, output_file as bk_output_file, save as bk_save, show as bk_show
from bokeh.models import Label as bk_Label
from bokeh.layouts import row as bk_row, column as bk_column
import multiprocessing,pickle

class npx_vision_classifier:
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
        units=self.u_list()
        sp_t=self.spike_times
        sp_c=self.spike_clusters
        tbl=pd.DataFrame({'times':sp_t,'clusters':sp_c})
        tbl = tbl.groupby('clusters').count().reset_index()
        tbl.columns=['unit','n_spikes']
        #self.build_raster()
        #r=self.raster
        #n=[len(r_) for r_ in r]    
        #tbl=pd.DataFrame({'unit':u,'n_spikes':n})
        return tbl
    
    def u_features(self,u:int):
        #print (self.pc_features.shape)
        sp_t=self.spike_times
        sp_c=self.spike_clusters
        sp_pc=self.pc_features
        sp_pc_ind=self.pc_feature_ind
        
        sp_pc_=self.pc_features[sp_c==u,:2,:2]
        F=[bk_figure(width=200,height=200) for i in range(6)]
        CH=[0, 1, 0, 1]
        PC=[0, 0, 1, 1]
        k=0
        for i in range(4):
            ichannel=CH[i]
            ipc=PC[i]
            for j in range(i+1,4):
                jchannel=CH[j]
                jpc=PC[j]
                
                F[k].circle(sp_pc_[:,ichannel,ipc],sp_pc_[:,jchannel,jpc],size=2,alpha=0.2)
                F[k].title.text='PC'+str(ichannel)+str(ipc)+' vs PC'+str(jchannel)+str(jpc)
                k+=1
        FF=bk_row(bk_column( F[0],F[1],F[2]),bk_column(F[3],F[4],F[5]))
        bk_output_file(f'Offline/Clustering/Figures/features_u{u}.html')
        bk_save(FF)
        #print (sp_pc[0,:2,:2].squeeze())
        #print (sp_pc_ind[:2])
        return 1
    def batch_features(self,U:list):
        
        #with multiprocessing.Pool(5) as p:
        a=list(map(self.u_features,U))
        ##for iu,u in enumerate(U):
        #    FF=a[iu]
        #    bk_output_file(f'Offline/Clustering/Figures/features_u{u}.html')
        #    bk_save(FF)
            
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
        p['pc_features']       = path+'/pc_features.npy'
        p['pc_feature_ind']    = path+'/pc_feature_ind.npy'
        self.paths=p
        self.validate_files()
        
        self.trials=pd.read_csv(p['Trials'])
        
        self.spike_times=np.load(p['spike_times'])
        self.spike_clusters=np.load(p['spike_clusters'])
        self.spike_positions=np.load(p['spike_positions'])
        self.cluster_group=pd.read_csv(p['cluster_group'],sep='\t')
        self.pc_features=np.load(p['pc_features'])
        self.pc_feature_ind=np.load(p['pc_feature_ind'])
        
    def split(self):
        self.build_raster()
        print (self.raster[1])
    
    
        
if __name__=="__main__":
    
    path='C:/Sorting/m42c539/kilosort4'
    path_classifier=path+'/spikes_classifier.pkl'
    
    if os.path.exists(path_classifier):
        print ('loading classifier')
        vc=pickle.load(open(path_classifier,'rb'))
        print ('classifier loaded')
    else:
        print('Creating classifier')
        vc=npx_vision_classifier(path)
        pickle.dump(vc,open(path_classifier,'wb'))
        print ('classifier created')
    
    t=vc.u_table()
    print (t)
    
    #f=vc.u_features(200)
    vc.batch_features(range(2,600))
    #print(f)