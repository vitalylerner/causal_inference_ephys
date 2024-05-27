# -*- coding: utf-8 -*-
"""
Created on Mon May 27 15:28:30 2024

@author: Vitaly
"""

import pandas as pd
import numpy as np
pd.options.mode.chained_assignment = None
#graphical pachages for debugging, commented out when not in debugging mode
from bokeh.plotting import figure as bk_figure, output_file as bk_output_file, save as bk_save, show as bk_show
from bokeh.models import Label as bk_Label
from bokeh.layouts import row as bk_row, column as bk_column
#from PIL import Image as im 
from scipy.ndimage import gaussian_filter1d

from scipy.fft import fft, fftfreq

def figure_60Hz():
    #Root='Z:/Data/MOOG/Dazs/OpenEphys'
    
    #ks_folders=['m42c461/output','m42c485/output',
    #ks_folders=['m42c527/kilosort4',
    #            'm42c539/experiment1/kilosort']
    nch=384
    T=20
    sr=30000
    
    tstart=10
    nstart=32*nch*sr*tstart
    t=np.arange(T*sr,dtype=float)/sr
    
    fl='C:/Sorting/m42c539/rec1AP.dat'
    fl='C:/Sorting/m42c461rec1AP.dat'
    output='Figures/60Hz_539.html'
    output='Figures/60Hz_461.html'
    
    #fl='Z:/Data/MOOG/Dazs/OpenEphys/m42c461/recording1/continuous/Neuropix-PXI-109.ProbeA-AP/continuous.dat'
    tp=np.int32
    tp=np.int32
    A=np.fromfile(fl,count=int(nch*T*sr), dtype=tp,offset=nstart)
    
    A=A.reshape((int(T*sr),nch)).T.astype(np.float64)
    
    gp={'width':400,'height':250,'output_backend':'svg'}
    fsig=bk_figure(**gp)
    fF=bk_figure(y_axis_type='linear',x_axis_type='linear',y_range=[-20,60],**gp)
    
    amp=np.max(A,axis=1)-np.min(A,axis=1)
    best=np.argsort(amp)[-20:-1:3]
    worst=np.argsort(amp)[:5]
    
    N=A.shape[1]
    f = fftfreq(N, 1./sr)[:N//2]
    
    #print(iamp)
    #print (amp)
    A-=A.mean()
    A/=A.std()
    S=np.std(A)*15
    for ip,p in enumerate(best):
        fsig.line(t[:sr],A[p,:sr]+ip*S,color="black",alpha=1.0)
    #Vworst=np.mean(np.array([ 2.0/N*np.abs(fft(A[p,:]))[:N//2] for p in worst]),axis=0)
    #Vbest =np.mean(np.array([ 2.0/N*np.abs(fft(A[p,:]))[:N//2] for p in best]),axis=0)

    
    Vall=np.mean(np.array([ (20*np.log10(1./N*np.abs(fft(A[p,:]))**2))[:N//2] for p in range(0,384,5)]),axis=0)
    rng=(f>2) & (f<2000)
    #fF.line(f[rng],Vworst[rng],color="black",alpha=0.2)
    #fF.line(f[rng],Vbest[rng],color='red',alpha=0.2)
    for i60 in range(1,40):
        if (i60*60)<=2000:
            fF.line([i60*60]*2,[Vall[rng].min(),Vall[rng].max()*1.1],line_width=3,color='black',alpha=0.2)
        
    fF.line(f[rng],Vall[rng],color='black',alpha=1.0)
    #output='Figures/drift.html'

    F=bk_column([fsig,fF])
    bk_output_file(output)
    bk_show(F)
    return F
    
def  figure_drift():
    Root='Z:/Data/MOOG/Dazs/OpenEphys'
    
    #ks_folders=['m42c461/output','m42c485/output',
    ks_folders=['m42c527/kilosort4',
                'm42c539/experiment1/kilosort']
    F=[bk_figure(height=400,width=400,) for k in ks_folders]
    bins_s=5
    for ifold in [0,1]:#],1,2]:
        fold=ks_folders[ifold]
        fld=Root+'/'+fold
        spk_t  = np.load(fld+'/spike_times.npy')
        spk_p  = np.load(fld+'/spike_positions.npy')
        spk_u  = np.load(fld+'/spike_clusters.npy')
        spk_tpl=np.load(fld+'/spike_templates.npy')
        spk_p1=spk_p[:,0].squeeze()
        
        print (spk_tpl.shape)
        #print (spk_t.shape,spk_p1.shape,spk_u.shape)
        D=pd.DataFrame.from_dict({'time':spk_t*1.0/30000.,'position':spk_p1,'unit':spk_u})
        
        D2=D.groupby(by='unit',as_index=False).count()
        D2=D2[D2['position']>10000]
        #print (len(D2))
        units= sorted(list(set(D2.unit)))
                
        for i in range(10,101,10):
            u=units[i]
            D3=D[D.unit==u]
            D3.position-=np.mean(D3.position.to_list()[:100])
            D3['time_sec']=np.floor(D3.time*bins_s,dtype=float)/bins_s
            D4=D3.groupby(by='time_sec',as_index=False).mean()
            #F[ifold].line(x='time_sec',y='position',color="black",alpha=0.05,line_width=1,source=D4)
            F[ifold].scatter(x='time_sec',y='position',color="black",alpha=0.02,size=1,source=D4)
            #print (D4)
        return bk_column(F)
            #secs=np.array(sorted(list(set(np.floor(D3.time)))),dtype=int)
            #print (secs)
            #
            #print (D3)
        #D2=D.groupby()
        #print (D)
    
if __name__=='__main__':
    #F=figure_drift()
    figure_60Hz()
    
  