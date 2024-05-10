# -*- coding: utf-8 -*-
"""
Created on Fri May 10 16:24:55 2024

@author: Vitaly
"""
import pandas as pd
import numpy as np

from bokeh.plotting import figure as bk_figure, output_file as bk_output_file, save as bk_save, show as bk_show
from PIL import Image as im 

"""
The primary files you will need for your analysis now are 
spike_times.npy and spike_clusters.npy, identifying the times and 
identities of every spike, along with cluster_group.tsv, 
which has the labels you gave to the clusters (noise/MUA/good)."""

class vision_spikes:
    
    
    paths=None
    trials=None
    meta=None
    
    spike_times=None
    spike_clusters=None
    cluser_group=None
    
    def __init__(self,meta:dict,paths:dict):
        self.paths=paths
        self.meta=meta
        
        self.paths['Trials']=paths['kilosort']+'/Trials.csv'
        self.paths['log']=paths['tempo']+f'/m{meta["subject"]}m{meta["subject"]}r{meta["recording"]}'
        self.paths['spike_times']       = paths['kilosort']+'/spike_times.npy'
        self.paths['spike_clusters']    = paths['kilosort']+'/spike_clusters.npy'
        self.paths['cluster_group'] = paths['kilosort']+'/cluster_group.tsv'
        
        self.trials=pd.read_csv(self.paths['Trials'])
        self.spike_times=np.load(self.paths['spike_times'])
        self.spike_clusters=np.load(self.paths['spike_clusters'])
        self.cluster_group=pd.read_csv(self.paths['cluster_group'],sep='\t')
        
    def build_raster(self,unit:int):
        
        T=self.trials[(self.trials['rec']==self.meta['recording'])]
        trials=list(T['trial'])
        spk_sample=self.spike_times
        spk_unit  =self.spike_clusters
        #print (trials)
        filter_unit=spk_unit==unit
        raster=[]
        for trial in trials:
            TT=T[T['trial']==trial].iloc[0]
            sample_0=TT['ap in stitch']
            sample_start=sample_0-self.meta['pre']*self.meta['sampling_rate']
            sample_end=  sample_0+self.meta['post']*self.meta['sampling_rate']
            filter_spikes=(spk_sample>=sample_start) & (spk_sample<sample_end)
            filter_all=filter_spikes & filter_unit
            spikes_trial=spk_sample[filter_all]-sample_0
            raster+=[{'trial':trial,'spikes':spikes_trial*1.0/self.meta['sampling_rate']}]
        return raster
    def build_raster_matrix(self,unit:int):
        t_ms=np.arange(-self.meta['pre']*1000,self.meta['post']*1000)
        raster=self.build_raster(unit)
        trial_num=len(raster)
        M=np.zeros((trial_num,t_ms.size),dtype=bool)
        for r in raster:
            trial=r['trial']-1
            spikes=(np.array(r['spikes']*1000-self.meta['pre']*1000,dtype=float)).astype(np.int16)
            
            M[trial,spikes]=True
        return M
    def build_all(self):
        clas=self.cluster_group
        meta=self.meta
        MultiUnit=list(clas[clas['group']=='mua']['cluster_id'])
        SingleUnit=list(clas[clas['group']=='good']['cluster_id'])
        for unit in MultiUnit:
            raster=self.build_raster_matrix(unit)
            p=self.paths['output']+f'/m{meta["subject"]}c{meta["session"]}r{meta["recording"]}u{unit}_raster.npz'
            np.savez_compressed(p,raster=raster,meta=meta,group='MultiUnit')
        for unit in SingleUnit:
            raster=self.build_raster_matrix(unit)
            p=self.paths['output']+f'/m{meta["subject"]}c{meta["session"]}r{meta["recording"]}u{unit}_raster.npz'
            np.savez_compressed(p,raster=raster,meta=meta,group='SingleUnit')
        #print (mu)
        
        #rint (su)
            
        
vs=None    
if __name__=="__main__":
    for rec in range(1,7):
        m={}
        m['subject']=42
        m['session']=527
        m['recording']=rec
        m['sampling_rate']=30000
        m['pre']=1.5
        m['post']=3.5
        
        p={}
        
        p['kilosort']='C:/Sorting/m42c527'
        p['tempo']='Z:/Data/MOOG/Dazs/TEMPO'
        p['output']='Z:/Data/MOOG/DAZS/OpenEphys/m42c527/Spikes'
        vs=vision_spikes(m,p)
        vs.build_all()
    #raster_matrix=vs.build_raster_matrix(3)
    #raster_image = im.fromarray(raster_matrix) 
    #raster_image = raster_image.resize((300, 100), im.Resampling.BILINEAR)
    
    
    #raster_image.save('raster.png') 
    #fRaster=bk_figure(width=300,height=200)
    #for r in R:
    #    trial=r['trial']
    #    spikes=r['spikes']
    #    y_spikes=spikes*0+trial
    #    fRaster.scatter(spikes,y_spikes)
    #bk_output_file('raster_test.html')
    #bk_show(fRaster)
        