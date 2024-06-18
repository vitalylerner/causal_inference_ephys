# -*- coding: utf-8 -*-
"""
Created on Fri May 10 16:24:55 2024

@author: Vitaly

@Requirements:
numpy scipy bokeh pandas open-ephys-python-tools   

"""

"""
TODO: unify and structure directories, 
currently it's a mess. One place for all, at least
ephys. 

TODO: unite ci_tempo, moog_geometry and npx_tempo
to one repository
There are common funcitons, make sure to not duplicate them
"""

import pandas as pd
import numpy as np
pd.options.mode.chained_assignment = None
#graphical pachages for debugging, commented out when not in debugging mode
from bokeh.plotting import figure as bk_figure, output_file as bk_output_file, save as bk_save, show as bk_show
from bokeh.models import Label as bk_Label
from bokeh.layouts import row as bk_row, column as bk_column
from bokeh.colors import RGB
from scipy.ndimage import gaussian_filter1d
import os

from open_ephys.analysis import Session
import multiprocessing

def style_figure(f):
    sz='12pt'
    f.title.text_font_size=sz
    f.output_backend='svg'
    f.toolbar_location='below'
    for obj in [f.xaxis,f.yaxis]:
        obj.axis_label_text_font_size=sz
        obj.major_label_text_font_size=sz
        obj.major_label_text_font_size=sz


        
class vision_spikes:
    """preprocessing and initial analysis of ephys data.
    
    ephys recorded with Neuropixel,
    behavior data from TEMPO,
    ephys pre-processed with ks4 and phy2
    """

    paths=None
    trials=None
    meta=None
    
    spike_times=None
    spike_clusters=None
    cluser_group=None
    
    tempo_vars=None
    condition_table=None
    protocol_num=None
    raster_by_condition=None
    
    def __init__(self,meta:dict,paths:dict):
        self.paths=paths
        self.meta=meta
        self.paths['py_tempo']='Offline/VisualResponses/tempo_py_LUT.xls'
        self.paths['Trials']=paths['kilosort']+'/Trials.csv'
        self.paths['log']=paths['tempo']+f'/m{meta["subject"]}c{meta["session"]}r{meta["recording"]}.log'
        self.paths['spike_times']       = paths['kilosort']+'/spike_times.npy'
        self.paths['spike_clusters']    = paths['kilosort']+'/spike_clusters.npy'
        self.paths['cluster_group'] = paths['kilosort']+'/cluster_group.tsv'
        self.paths['spike_positions']= paths['kilosort']+'/spike_positions.npy'
        
        self.trials=pd.read_csv(self.paths['Trials'])
        self.spike_times=np.load(self.paths['spike_times'])
        self.spike_clusters=np.load(self.paths['spike_clusters'])
        self.spike_positions=np.load(self.paths['spike_positions'])
        self.cluster_group=pd.read_csv(self.paths['cluster_group'],sep='\t')
        self.tempo_vars=pd.read_excel(self.paths['py_tempo'])
        self.build_conditions_table()
        
        
    def unit_filename(self,unit:int):
        meta=self.meta
        return self.paths['output']+f'/m{meta["subject"]}c{meta["session"]}r{meta["recording"]}u{unit}_raster.npz'
    
    def raster_filename(self):
        meta=self.meta
        return self.paths['output']+f'/m{meta["subject"]}c{meta["session"]}r{meta["recording"]}_raster.npz'
    
    def multiunit_list(self):
        clus=self.cluster_group
        return list(clus[clus['group']=='mua']['cluster_id'])
    
    def singleunit_list(self):
        clus=self.cluster_group
        return list(clus[clus['group']=='good']['cluster_id'])
        
    def chrono_raster_sparse(self,unit:int):
        """Build raster in a sparse form for a given unit.
        
        (trials)x[nspikes], nspikes differs for each trial
        """
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
    
    def chrono_raster_matrix(self,unit:int):
        """Build raster in a matrix form for a given unit.
        
        (trials)x(tpre+tpost), tpre and tpost in ms
        """
        t_ms=np.arange(-self.meta['pre']*1000,self.meta['post']*1000)
        raster=self.chrono_raster_sparse(unit)
        trial_num=len(raster)
        M=np.zeros((trial_num,t_ms.size),dtype=bool)
        for r in raster:
            trial=r['trial']-1
            spikes=(np.array(r['spikes']*1000+self.meta['pre']*1000,dtype=float)).astype(np.int16)
            M[trial,spikes]=True
        return M
    
    def condition_grand_raster(self):
        """

        Returns
        -------
        R : dict, keys: number of units
            each element: raster,  list of n_conditions, 
                each element: ntrials x 5000(ms) bool

        """
        su=self.singleunit_list()
        mu=self.multiunit_list()
        
        R={}
        
        for u in su+mu:
            R[u]=self.condition_raster(u)
        return R
    
 
    def load_condition_raster(self):
        try:
            self.raster={}
            with np.load(self.raster_filename(),allow_pickle=True)  as r:
                for k in r.keys():
                    self.raster[int(k)]=r[k]
        except FileNotFoundError:
            print ('Creating and saving rasters, will run faster next time...')
            self.raster=self.condition_grand_raster()
            r={}
            for k in self.raster.keys():
                r[f"{k}"]=self.raster[k]
            np.savez_compressed(self.raster_filename(),**r)


    def condition_raster(self,unit:int):
        """Convert ungrouped rasters to a list of rasters.
        
        n_unique_conditions. 
        Each item is a 2d raster corresponding to unique condition
        in condition_table
        dimensions of each item are trials x ms
        """
        conditions=self.condition_table
        cond_num = len(conditions) 

        chrono_raster=self.chrono_raster_matrix(unit)
        trials_num,samples_num=chrono_raster.shape

        Raster_Grouped=[None for i in range(cond_num)]
        for i in range(cond_num):
            cond=conditions.iloc[i]
            try:
                broken = list(np.where(self.trials['broke_fix'])[0])
                trials=np.array(cond['trials'].split(','),dtype=int)
                trials=[t-1 for t in trials if not t in broken ]
            except ValueError:
                print ('---------')
                print ('ERROR! ERROR!')
                print (cond)
                trials=[]
                print ('---------')
            Raster_Grouped[i]=chrono_raster[trials,:]
        return Raster_Grouped
            
    def build_conditions_table(self):
        """Extract the necessary information from .log file.
        
        generated by TEMPO
        This is a minimalistic parser for .log file
        It does not parse .htb files and does not read all geometric
        parameters.
        Uses log files to arrange trials in groups for grouped rasters and PSTH
        
        the result is stored in the pandas table, each column corresponds
        to a variable that changes from trial to trial,
        and the last column is a string containing comma separated list of
        trials, started with 1
        
        each row corresponds to a unique combination of the variables 
        
        TODO either merge or at least unify with ci_tempo in moog_ci repository
         might be tricky, since ci_tempo is restricted to causal inference task (154)
         and this one is more general

        """
        condition_table={}
        logfile=self.paths['log']
        with open(logfile) as input_file:
            protocol_num = int ([next(input_file) for _ in range(5)][-1].split(' ')[1])
        self.protocol_num=protocol_num
        tvars=self.tempo_vars[self.tempo_vars['protocol']==protocol_num]    
        
        if len(tvars)==0:
            print(f"no variables found in python_tempo_LUT.xls for protocol #{protocol_num}")
        
        
        for ivar in range(len(tvars)):
            tvar=tvars.iloc[ivar]
            tvar_pystr=str(tvar['py_str'])
            tvar_str = str(tvar['tempo_str'])
            tvar_py_array=bool(tvar['py_array'])
            tvar_tempo_array=bool(tvar['tempo_array'])
            with open(self.paths['log'],'r') as f:
                lines = [ [float(s) for s in line.split(' ')[1:] if not len(s)==0] for line in f if line.split(' ')[0]==tvar_str]
            values=np.array(lines,dtype=np.float32)
            if (~tvar_py_array) and tvar_tempo_array:
                values=values[:,0].squeeze()
            condition_table[tvar_pystr]=values
        condition_table['trials']=["" for v in values]
        condition_table=pd.DataFrame.from_dict(condition_table)
        TrialByTrial=condition_table.copy()
        unique_condition_table=condition_table.drop_duplicates()
        py_vars=list(tvars['py_str'])
        for icond in range(len(unique_condition_table)):
            cond=unique_condition_table.iloc[icond]
            flt=[True for i in range(len(condition_table))]
            for py_var in py_vars:
                flt&=np.array(condition_table[py_var].to_list())==cond[py_var]
            flt=f"{list(np.where(flt)[0]+1)}"[1:-1]
            unique_condition_table.loc[icond,'trials']=flt
        unique_condition_table.sort_values(by=py_vars,inplace=True,ignore_index=True)
        self.condition_table=unique_condition_table
        return TrialByTrial.drop('trials',axis=1)


    def tuning(self,unit:int,t_baseline:tuple=(-0.8,-0.4),t_signal:tuple=(1,1.8)):
        #sr=self.meta['sampling_rate']
        m=1000
        n0=int(self.meta['pre']*m)
        def t2n(t):
            return int(t*m)+n0
        n_bsl0=t2n(t_baseline[0])
        n_bsl1=t2n(t_baseline[1])
        n_sig0=t2n(t_signal[0])
        n_sig1=t2n(t_signal[1])
        
        T_bsl=t_baseline[1]-t_baseline[0]
        T_sig=t_signal[1]-t_signal[0]
        
        C=self.condition_table
        trials=self.trials
        
        conditions_num=len(C)
        #print (C)
        R=self.raster[unit]
        
        vars_str=''.join(list(vs.condition_table.columns[:-1]))
        ttl=f'unit#{unit}, protocol#{self.protocol_num}: \n' + vars_str
        g_raster=bk_figure(height=400,width=400,x_range=(-2,5),title=ttl)
        
        height=0
        delta_firing=np.zeros(conditions_num)
        delta_firing_sem=np.zeros(conditions_num)
        for icond in range(conditions_num):
            r=R[icond]
            if len(np.shape(r))==1:
                r=np.array([r])
            trials_num=r.shape[0]
            samples_num=r.shape[1]
            
            psth=r.sum(axis=0)
            
            t_psth=np.arange(samples_num,dtype=float)*0.001-self.meta['pre']
            
            dfr=r[:,n_sig0:n_sig1].sum(axis=1)-r[:,n_bsl0:n_bsl1].sum(axis=1)
            delta_firing[icond]=dfr.mean()
            delta_firing_sem[icond]=dfr.std()/np.sqrt(trials_num)
            #bsl=psth[n_bsl0:n_bsl1].sum()/(trials_num*T_bsl)
            #sig=psth[n_sig0:n_sig1].sum()/(trials_num*T_sig)
            
            #delta_firing[icond]=sig-bsl
        
            
        return delta_firing,delta_firing_sem     
    
    def plot_unit_ephys(self,unit:int):
        spk=self.spike_times
        spu=self.spike_clusters
        spp=self.spike_positions
        # ISI histpgram
        
        
        u_spk=spk[spu==unit]
        u_isi=np.diff(u_spk)/30.  

        
        fISI=bk_figure(height=400,width=400,title=f"u{unit} ISI histogram",toolbar_location=None)
        style_figure(fISI)
        isi_step=2
        isi_max=200
        bins = np.linspace(0, isi_max+isi_step, isi_max//isi_step)
        hist, edges = np.histogram(u_isi, density=True, bins=bins)
        fISI.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:],
                  fill_color="black", line_color="black",alpha=0.5,)
        
        # Waveform
        #fDAT=self.paths['rec1dat']
        nch=384
        
        
        sr=30000
        
        npre=  int(sr*0.002)
        npost= int(sr*0.010)
        nseg=npre+npost
        
        tseg=(np.arange(nseg,dtype=float) -npre) /30
        
        """fWave=bk_figure(height=1000,width=400,title=f"u{unit}",toolbar_location='below')
        VV=[]
        for i in range(30):
            nstart=(u_spk[i]-npre)*nch
            
            A=np.fromfile(fDAT,count=nseg*nch, dtype=np.int32,offset=nstart)
            A=A.reshape( (nseg,nch)).T.astype(np.float64)
            #A-=np.mean(A)
            
            #A/=np.std(A)
            #thr=0.1
            VV+=[A]
            #for i in range(191):
                #for k in [0,1]:
            #        V=A[2*i+k,:]
                    #V-=V.mean()
                    #V/=V.std()
                    #if (V.max()>V.std()*thr) or (V.min()<-thr*V.std()):
            #            fWave.line(tseg+k*50,V+i*0.,color='black',alpha=0.05)
                #fWave.line(tseg+50,A[2*i+1,:]+i*10,color='black',alpha=0.2)
        VV=np.array(VV).mean(axis=0)   
        VV-=VV.mean()
        VV/=VV.std()
        for i in range(192):
            for k in [0,1]:
                v=VV[i,:]
            #V-=V.mean()
            #V/=V.std()
            #if (V.max()>V.std()*thr) or (V.min()<-thr*V.std()):
                fWave.line(tseg+k*10,(v-v[:npre].mean())*2+i*1.0,color='black',alpha=1.0)
        #print (VV.shape)
        
        
        """
        """u_spk2=u_spk[:10]
        print (self.paths['recording'])
        session = Session(self.paths['recording']+'/recording1')
        
        rec=session.recordnodes[0].recordings[0]
        for sample0 in u_spk2[:1]:
            sample_start=sample0-60
            sample_end=sample0+150
            
            data = rec.continuous[0].get_samples(start_sample_index=sample_start, end_sample_index=sample_end)
            print (data.shape)
        """
        #print (spp.shape)
        
        # POSITION
        u_pos0=spp[spu==unit,0]
        u_pos1=spp[spu==unit,1]
        u_times=spk[spu==unit]
        fPos=bk_figure(height=400,width=400,title=f"u{unit} Position",toolbar_location='below')
        #fPos.scatter(u_times,u_pos0)
        fPos.scatter(u_times,u_pos1,alpha=0.1,color='black',marker='dot',size=12)
        style_figure(fPos)
        return bk_row([fISI,fPos])
    
    def mapping_all(self):
       # C=self.conditions_table
        su=self.singleunit_list()
        mu=self.multiunit_list()
        #with multiprocessing.Pool(10) as p:
        DF=np.array(list(map(self.tuning,su+mu)))

        act_i=np.abs(DF).argmax(axis=1)
        act_v=np.array([DF[iu,act_i[iu]] for iu in range(len(act_i))])
        act_pot=act_v>10
        act_supp=act_v<-4
        #print (act_pot)
        DFa=DF[act_pot,:]
        DFa=np.array([(DFa[i,:]-DFa[i,0].min())/DFa[i,:].std() for i in range(DFa.shape[0])])
        DFs=DF[act_supp,:]
        DFs=np.array([(DFs[i,:]-DFs[i,0])/DFs[i,:].std() for i in range(DFs.shape[0])])
        #DF2=np.abs(DF)#DF[np.abs(DF).max(axis=1).argsort(),:]
        #print (DF)
        print (f"activated:{len(DFa)}/{len(su)+len(mu)}, {int(100*len(DFa)/(len(su)+len(mu)))}%")
        print (f"suppressed:{len(DFs)}/{len(su)+len(mu)}, {int(100*len(DFs)/(len(su)+len(mu)))}%")
        
        fM=bk_figure(width=400,height=800,title="mapping")
        #fTs=bk_figure(width=200,height=800,y_range=fTa.y_range,title="tuning-")
        k=0
        for i in range(4):
            for j in range(4):
                k=i*4+j+1
                
                rng=np.where(DFa.argmax(axis=1)==k)[0]
                
                for i_n,n in enumerate(rng):
                    a=DFa[n,1:].reshape((4,4))
                    fM.image(image=[a],y=k*5,x=i_n*5,dw=4,dh=4,palette="Turbo256",level="image")
                
        """for fig in [fTa]:
            fig.xgrid.grid_line_color = None
            fig.ygrid.grid_line_color = None
            fig.axis.visible=False
        fTa.image(image=[DFa_ordered], x=1, y=len(dfs_order), 
                  dw=DFa.shape[1], dh=DFa.shape[0], 
                  palette="Turbo256", level="image")
        fTa.image(image=[DFs_ordered], x=1, y=0,
                  dw=DFs.shape[1], dh=DFs.shape[0],
                  palette="Turbo256", level="image")
        fTa.line([7.5]*2,[0,len(dfs_order)+len(dfa_order)],color="black",alpha=0.2,line_width=2)
        fTa.line(np.array([3,3,7,7,7,11,11])+0.5,np.array([0,1,1,0,1,1,0])*2-2.5,color="black",line_width=2)
        fTa.line([-1]*2,[0,20],color="black",line_width=2)
        """
        return fM
        #df=self.tuning(unit,(-0.8,-0.4),(1,1.8))
    def tuning_all(self):
       # C=self.conditions_table
        su=self.singleunit_list()
        mu=self.multiunit_list()
        #with multiprocessing.Pool(10) as p:
        DF=np.array(list(map(self.tuning,su+mu)))

        act_i=np.abs(DF).argmax(axis=1)
        act_v=np.array([DF[iu,act_i[iu]] for iu in range(len(act_i))])
        act_pot=act_v>4
        act_supp=act_v<-4
        #print (act_pot)
        DFa=DF[act_pot,:]
        DFa=np.array([(DFa[i,:]-DFa[i,0].min())/DFa[i,:].std() for i in range(DFa.shape[0])])
        DFs=DF[act_supp,:]
        DFs=np.array([(DFs[i,:]-DFs[i,0])/DFs[i,:].std() for i in range(DFs.shape[0])])
        
        print (f'max z={DFa.max():.2f},min z={DFs.min():.2f}')
        #DF2=np.abs(DF)#DF[np.abs(DF).max(axis=1).argsort(),:]
        dfa_argmax=np.argmax(DFa,axis=1)
        DFa=DFa[dfa_argmax>0,:]
        
        dfs_argmin=np.argmin(DFs,axis=1)
        DFs=DFs[dfs_argmin>0,:]
        
        dfa_order=DFa.max(axis=1).argsort()
        DFa=DFa[dfa_order,:]
        dfa_order=np.argmax(DFa,axis=1).argsort()[::-1]
        dfs_order=np.argmin(DFs,axis=1).argsort()[::-1]
        DFa_ordered=DFa[dfa_order,:]
        DFs_ordered=DFs[dfs_order,:]
        #print (DF)
        print (f"activated:{len(dfa_order)}/{len(su)+len(mu)}, {int(100*len(dfa_order)/(len(su)+len(mu)))}%")
        print (f"suppressed:{len(dfs_order)}/{len(su)+len(mu)}, {int(100*len(dfs_order)/(len(su)+len(mu)))}%")
        
        fTa=bk_figure(width=200,height=800,title="tuning+")
        #fTs=bk_figure(width=200,height=800,y_range=fTa.y_range,title="tuning-")
        for fig in [fTa]:
            fig.xgrid.grid_line_color = None
            fig.ygrid.grid_line_color = None
            fig.axis.visible=False
        fTa.image(image=[DFa_ordered], x=1, y=len(dfs_order), 
                  dw=DFa.shape[1], dh=DFa.shape[0], 
                  palette="Turbo256", level="image")
        fTa.image(image=[DFs_ordered], x=1, y=0,
                  dw=DFs.shape[1], dh=DFs.shape[0],
                  palette="Turbo256", level="image")
        fTa.line([7.5]*2,[0,len(dfs_order)+len(dfa_order)],color="black",alpha=0.2,line_width=2)
        fTa.line(np.array([3,3,7,7,7,11,11])+0.5,np.array([0,1,1,0,1,1,0])*2-2.5,color="black",line_width=2)
        fTa.line([-1]*2,[0,20],color="black",line_width=2)
        
        return bk_row(fTa)
        #df=self.tuning(unit,(-0.8,-0.4),(1,1.8))
        
    def plot_unit(self, unit:int):
        
        #gr_ephys=self.plot_unit_ephys(unit)
        C=self.condition_table
        trials=self.trials
        
        conditions_num=len(C)
        R=self.raster[unit]
        
        vars_str=''.join(list(self.condition_table.columns[:-1]))
        ttl=f'unit#{unit}, protocol#{self.protocol_num}: \n' + vars_str
        g_raster=bk_figure(height=400,width=400,x_range=(-2,5),title=ttl)
        g_raster.xaxis.ticker=[-2,0,2,4]
        style_figure(g_raster)
        height=0
        
        df,df_sem=self.tuning(unit,(-0.8,-0.4),(1,1.8))
        ncondvars=len(list(C.columns))-1
        x=C[C.columns[0]]
        
        if ncondvars==2:
            y=C[C.columns[1]]
        if self.protocol_num == 0: #direction tuning
            g_tuning=bk_figure(height=300,width=300)
            
            x=C.direction
            
            rng=(x>=0) & (x<=360) & np.invert(np.isnan(df))
            x=x[rng]
            #print (x)
            df=df[rng]
            #print(df)
            
            a=np.deg2rad(np.arange(360))
            ax=np.cos(a)
            ay=np.sin(a)
            for i10 in range(5):
                g_tuning.line(ax*(i10+1)*10,ay*(i10+1)*10,line_width=2,color='black',alpha=0.2)
                
                
            fr_x=df*np.cos(np.deg2rad(x))
            fr_y=df*np.sin(np.deg2rad(x))
            g_tuning.scatter(fr_x,fr_y,color='black',size=6,marker='o')

        elif self.protocol_num==1: #speed tuning
            g_tuning=bk_figure(height=300,width=400,x_axis_type='log')
            
            x=C.speed
            rng=x>=0
            x=x[rng]
            df=df[rng]
            g_tuning.line(x,df)
        elif self.protocol_num==2: #disparity tuning
            g_tuning=bk_figure(height=300,width=400)
            x=C.disp
            rng=np.abs(x)<3.0
            x=x[rng]
            df=df[rng]
            
            g_tuning.line(x,df,line_width=2,color="black")
            for x_,df_,df_sem_ in zip(x,df,df_sem):
                g_tuning.line([x_]*2,[df_-df_sem_,df_+df_sem_],color='black')
                
        elif self.protocol_num==12: # RF Mapping
            g_tuning=bk_figure(height=300,width=300)

            rng=np.invert(np.isnan(df))
            x=C.x
            rng=np.abs(C.x)<30.
            df=df[rng]
            
            crc_size=np.abs(df)
            #crc_color=np.sign(df)
            s=np.sign(df)
            crc_color=["white" for ss in s]
            for iss,ss in enumerate(s):
                if ss==-1.0:
                    crc_color[iss]="red"
                else:
                    crc_color[iss]="blue"
                    
                    
            #crc_color=RGB([ if ss==1 "blue"])
            #s_clr=(100-s*80).astype(int)
            #crc_color=RGB(s_clr,s_clr,s_clr)
            CC=C[rng][['x','y']].copy()
            CC["crc_size"]=crc_size
            CC["crc_color"]=crc_color
            #rng=[]
            #x=C.x[rng]
            #y=C.y[rng]
            #print (CC)
            for x_,y_ in zip(x,y):
                g_tuning.scatter(x='x',y='y',size='crc_size',source=CC,color='crc_color',alpha=0.8)
        else:
            g_tuning=bk_figure(height=300,width=300)
        style_figure(g_tuning)
        
        for icond in range(conditions_num):
            r=R[icond]
            if len(np.shape(r))==1:
                r=np.array([r])
            trials_num=r.shape[0]
            samples_num=r.shape[1]
            
            psth=r.sum(axis=0)
            t_psth=np.arange(samples_num,dtype=float)*0.001-self.meta['pre']
            h0=height
            for itrial in range(trials_num):
                spikes=np.where(r[itrial,:])[0]*0.001-self.meta['pre']
                g_raster.scatter(spikes,height,marker='diamond',alpha=0.2,color="black")
                height-=1
            h1=height
            cond_text=f"{list(C.iloc[icond])[:-1]}"[1:-1]
            g_raster.add_layout(bk_Label(x=3.7,y=h1,text=cond_text))
            g_raster.line([3.6]*2,[h0,h1-10],color="black",line_width=2)
            
            
            psth_flt = gaussian_filter1d(psth*1.0, 20)
            psth_std=psth_flt[:1000].std()
            psth_bsl=psth_flt[:1000].mean()
            g_raster.line(t_psth,(psth_flt-psth_bsl)*30+h1-10,color="black",alpha=0.2,line_width=2)
            
            height-=20
        return bk_column([g_raster,g_tuning])
    
    def html_menu(self):
        su=self.singleunit_list()
        mu=self.multiunit_list()
        
        m=self.meta
        htmlp=self.paths['figures']+'/Units.html'
        
        l=['<html>\n<!--VITALY 2024-->\n']
        l+=['<body>']
        l+=[f'<h1>m{m["subject"]} session{m["session"]}</h1>']
        l+=['<h2> Single Units </h2>']
        cnt=1
        for u in su:
            fname=f'SU/m{m["subject"]}c{m["session"]}u{u}.html'
            l+=[f'<a href={fname} target="_blank" rel="noopener noreferrer">{u}</a>\t ']
            if cnt%10==0:
                l+=['<br>']
            cnt+=1
            
        l+=['<h2> Multinuts </h2>']
        cnt=1
        for u in mu:
            fname=f'MU/m{m["subject"]}c{m["session"]}u{u}.html'
            l+=[f'<a href={fname} target="_blank" rel="noopener noreferrer">{u}</a>\t ']  
            if cnt%10==0:
                l+=['<br>']
            cnt+=1
        l+=['</body>']
        l+=['</html>']
        with open(htmlp,'w') as fhtml:
            fhtml.writelines(l)
        

            
if __name__=="__main__":
    

    
    plot_su=False
    plot_mu=True
    
    m={}
    m['subject']=42
    m['session']=539
    #m['session']=527
    #m['recording']=rec
    m['sampling_rate']=30000
    m['pre']=1.5
    m['post']=3.5
    
    p={}
    
    p['kilosort']=f'Z:/DATA/MOOG/Dazs/OpenEphys/m{m["subject"]}c{m["session"]}/kilosort4'
    p['tempo']='Z:/Data/MOOG/Dazs/TEMPO'
    p['recording']=f'Z:/Data/MOOG/DAZS/OpenEphys/m{m["subject"]}c{m["session"]}'
    p['output']=f'Z:/Data/MOOG/DAZS/OpenEphys/m{m["subject"]}c{m["session"]}/Spikes'
    p['figures']=f'Z:/Data/MOOG/DAZS/Results/m{m["subject"]}c{m["session"]}'
    
    #p['rec1dat']=f'C:/Sorting/m42c539/rec1AP.dat'
    
    p['figures_su']=p['figures']+'/SU'
    p['figures_mu']=p['figures']+'/MU'
    
    for fld in ['output','figures','figures_su','figures_mu']:

        if not os.path.exists(p[fld]):
            os.makedirs(p[fld])
            print("The new directory is created! " + p[fld])
            
    m['recording']=1
    vs0=vision_spikes(m,p)        
    su=vs0.singleunit_list()
    mu=vs0.multiunit_list()
    #
    su_super=[69,158,205,221,278,305,347,385,410,506,542,605,618,647,724,758]
    su_super=[61,176,194,199,305,347,385,410,758]
    su_super=[385,347]
    su_super=[191]
    T=vs0.build_conditions_table()
    T.to_excel( f"""Offline/VisualResponses/m{m["subject"]}c{m["session"]}_trial_conditions.xlsx""",index=False)
    print(T)
    if False:
        #su_super=[191]
        print (f"""m{m["subject"]}c{m["session"]}""")
        print (f"{len(su)} single units")
        print (f"{len(mu)} multiunits")
        if False:
            F=list(map(vs0.plot_unit_ephys,su))
            #for iu in range(len(su)):
            #    F[iu]=vs0.plot_unit_ephys(su[iu])
                
            bk_output_file("Figures/m42c527_all_ephys.html")
            bk_show(bk_column(F))
        
        #G_SU=[None for r in REC]
        #G_MU=[None for r in REC]
        if False:
            vs0.html_menu()
        if False:
            m['recording']=2
            vs=vision_spikes(m,p)
            print (vs.protocol_num)
            vs.load_condition_raster()
            F=vs.tuning_all()
            bk_output_file("Figures/disp_tuning_all.html")
            bk_show(F)
        if False:
            m['recording']=1
            vs=vision_spikes(m,p)
            print (vs.protocol_num)
            vs.load_condition_raster()
            F=vs.mapping_all()
            bk_output_file("Figures/mapping_all.html")
            bk_show(F)
        if True:
            REC=[3]
            for u in [191]:#mu:    
                fEphys=vs0.plot_unit_ephys(u)
                G=[None for rec in REC]
                for irec,rec in enumerate(REC):#range(1,7):
                    m['recording']=rec
                    vs=vision_spikes(m,p)
                    vs.load_condition_raster()
                    g=vs.plot_unit(u)
                    G[irec]=g
                if u in su:            
                    fName=p['figures_su']+f'/m{m["subject"]}c{m["session"]}u{u}.html'
                elif u in mu:
                    fName=p['figures_mu']+f'/m{m["subject"]}c{m["session"]}u{u}.html'
                print (fName)
                bk_output_file(fName)
                F=bk_column([fEphys,bk_row(G)])
                bk_save(F)

        

