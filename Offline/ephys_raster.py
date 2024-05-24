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
#from PIL import Image as im 
from scipy.ndimage import gaussian_filter1d


from open_ephys.analysis import Session

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
        self.paths['py_tempo']='tempo_py_LUT.xls'
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
    
    def tuning(self,unit:int,t_baseline:tuple,t_signal:tuple):
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
        R=self.raster[unit]
        
        vars_str=''.join(list(vs.condition_table.columns[:-1]))
        ttl=f'unit#{unit}, protocol#{self.protocol_num}: \n' + vars_str
        g_raster=bk_figure(height=400,width=400,x_range=(-2,5),title=ttl)
        
        height=0
        delta_firing=np.zeros(conditions_num)
        for icond in range(conditions_num):
            r=R[icond]
            if len(np.shape(r))==1:
                r=np.array([r])
            trials_num=r.shape[0]
            samples_num=r.shape[1]
            
            psth=r.sum(axis=0)
            
            t_psth=np.arange(samples_num,dtype=float)*0.001-self.meta['pre']
            bsl=psth[n_bsl0:n_bsl1].sum()/(trials_num*T_bsl)
            sig=psth[n_sig0:n_sig1].sum()/(trials_num*T_sig)
            
            delta_firing[icond]=sig-bsl
        
            
        return delta_firing        
    def plot_unit_ephys(self,unit:int):
        spk=self.spike_times
        spu=self.spike_clusters
        spp=self.spike_positions
        # ISI histpgram
        u_spk=spk[spu==unit]
        u_isi=np.diff(u_spk)/30.  

        
        fISI=bk_figure(height=400,width=400,title="ISI histogram",toolbar_location=None)

        bins = np.linspace(0, 50, 25)
        hist, edges = np.histogram(u_isi, density=True, bins=bins)
        fISI.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:],
                  fill_color="black", line_color="black",alpha=0.5,)
        
        # Waveform
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
        u_pos0=spp[spu==unit,0]
        u_pos1=spp[spu==unit,1]
        u_times=spk[spu==unit]
        fPos=bk_figure(height=400,width=400,title="Position",toolbar_location='below')
        #fPos.scatter(u_times,u_pos0)
        fPos.scatter(u_times,u_pos1,alpha=0.1,color='black',marker='dot',size=12)
        return bk_row([fISI,fPos])


    def plot_unit(self, unit:int):
        C=self.condition_table
        trials=self.trials
        
        conditions_num=len(C)
        R=self.raster[unit]
        
        vars_str=''.join(list(self.condition_table.columns[:-1]))
        ttl=f'unit#{unit}, protocol#{self.protocol_num}: \n' + vars_str
        g_raster=bk_figure(height=400,width=400,x_range=(-2,5),title=ttl)
       
        height=0
        
        df=self.tuning(unit,(-0.8,-0.4),(1,1.8))
        ncondvars=len(list(C.columns))-1
        x=C[C.columns[0]]
        if ncondvars==2:
            y=C[C.columns[1]]
        if self.protocol_num == 0:
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
                g_tuning.line(ax*(i10+1)*10,ay*(i10+1)*10,color='black',alpha=0.2)
                
                
            fr_x=df*np.cos(np.deg2rad(x))
            fr_y=df*np.sin(np.deg2rad(x))
            g_tuning.scatter(fr_x,fr_y,color='black',size=6,marker='o')

        elif self.protocol_num==1:
            g_tuning=bk_figure(height=300,width=400,x_axis_type='log')
            x=C.speed
            rng=x>=0
            x=x[rng]
            df=df[rng]
            g_tuning.line(x,df)
        elif self.protocol_num==2:
            g_tuning=bk_figure(height=300,width=400)
            x=C.disp
            rng=np.abs(x)<3.0
            x=x[rng]
            df=df[rng]
            g_tuning.line(x,df)
        elif self.protocol_num==12:
            g_tuning=bk_figure(height=300,width=400)

            rng=np.invert(np.isnan(df))
            x=C.x
            rng=np.abs(C.x)<30.
            df=df[rng]
            
            crc_size=np.abs(df)
            crc_color=np.sign(df)
            CC=C[rng][['x','y']].copy()
            CC["crc_size"]=crc_size
            CC["crc_color"]=crc_color
            #rng=[]
            #x=C.x[rng]
            #y=C.y[rng]
            #print (CC)
            for x_,y_ in zip(x,y):
                g_tuning.scatter(x='x',y='y',size='crc_size',source=CC)
        else:
            g_tuning=bk_figure(height=300,width=300)
            
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
                g_raster.scatter(spikes,height,marker='diamond',alpha=0.2)
                height-=1
            h1=height
            cond_text=f"{list(C.iloc[icond])[:-1]}"[1:-1]
            g_raster.add_layout(bk_Label(x=3.7,y=h1,text=cond_text))
            g_raster.line([3.6]*2,[h0,h1-10],color="black")
            
            
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
    REC=[1,2,3,4]
    G_SU=[None for r in REC]
    G_MU=[None for r in REC]
    
    plot_su=False
    plot_mu=True
    
    m={}
    m['subject']=42
    m['session']=527
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
    p['figures_su']=p['figures']+'/SU'
    p['figures_mu']=p['figures']+'/MU'
    
    m['recording']=1
    vs0=vision_spikes(m,p)        
    su=vs0.singleunit_list()
    mu=vs0.multiunit_list()
    #
    F=vs0.plot_unit_ephys(290)
    bk_output_file("test.html")
    bk_show(F)
    if False:
        for u in su:    
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
            bk_output_file(fName)
            bk_save(bk_row(G))
    if False:
        vs0.html_menu()
    

