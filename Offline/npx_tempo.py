""" Neuropixels - TEMPO
Offline Analysis

Vitaly Lerner 2024

TODO:
(1)in TEMPO, add another code: BrokeFix=32
Otherwise, in discrimination task it won't be possible to distinguish
between wrong and break_fixation cases.
For mp/mapping/tuning protocols it's the same

"""
import numpy as np
import pandas as pd
import logging,os,json
from  newloadmat import loadmat
from datetime import datetime
import pickle

from bokeh.plotting import  figure,show,save,output_file
from bokeh.layouts import row,column

class npx_tempo:
    """
    Offline analysis of neuropixel data.
    
    Align spikes recorded with OpenEphys
    with the stimuli and behavioral data from TEMPOW
    """    
    subjectID   = None
    subjectName = None
    sessionID   = None
    mainpath    = None
    recid_list  = None
    oebin       = None
    oe_events   = None
    codes  ={'trial_start':1,'stim_start':4,'stim_end':5,'trial_end':15,'success':12,'broke_fix':10}
    rtcodes={'TRIAL_START':1,'STIM_START':2,'STIM_END':4,'TRIAL_END':8,'SUCCESS':16,
             'BROKE_FIX':32,'FRAME':128}
    def __init__(self,**kwargs):
        bOK=False
        self.logging_start()
        self.logger.info("""\n ***** Vitaly Lerner, January 2024 ****
                     ** Offline preprocessing of ephys data recorded continuously **""")
        self.logger.warning("""Currently the filter by "success" is applied
                        to events recorded in OpenEphys, this is wrong generally It works for non-discrimination tasks,
                        but must be replaced with a filter by BROKE_FIX. """)

        # Validate arguments and fill the object parameters
        try:
            self.subjectID      = kwargs['subjectID']
            self.subjectName    = kwargs['subjectName']
            self.sessionID      = kwargs['sessionID']
            self.mainpath       = kwargs['mainpath']
            for var in kwargs.keys():
                self.logger.info(f"""{var}\t{kwargs[var]}""")
            bOK=True
        except:
            self.logger.error("not enough context information provided")

        #Count OpenEphys Recordings,
        #save recIDs to recid_list
        if bOK:
            bOK=self.oe_recordings_count()
                
        #retrieve OpenEphys structure for each recording,
        #save to oe_obin
        if bOK:
            bOK=self.oe_oebin_bulk_load()

        #Build trial log to align with TEMPO
        #based on TTL events
        if bOK:
            bOK=self.oe_ttl_bulk_load()
            
                    
    #***     SECTION 1                                                      ***#
    #***     Locating the files                                             ***#
                    
    #*** Path building Level 0                                              ***#
    #*** this section is straightforward path construction from context,    ***#
    #***including recording numbers                                         ***#
                    
    def path_tempo_log(self,recID):
        """Path of the log file created by TEMPO associated with a specific recording."""
        return self.mainpath+f"{self.subjectName}/m{self.subjectID}c{self.sessionID}r{recID}.log"
    def path_tempo_htb(self,recID):
        """Path of the htb file created by TEMPO associated with a specific recording."""
        x=self.path_tempo_log(recID)
        return x[:-4]+".htb"
    def path_tempo_mat(self,recID):
        """Path of the mat file created by TEMPO_GUI associated with a specific recording."""
        x=self.path_tempo_htb(recID)
        return x+".mat"
        
    def path_oe_root(self,recID):
        """Path of the a folder tree created by OpenEphys for a specific recording ."""
        return self.mainpath+f"{self.subjectName}/OpenEphys/m{self.subjectID}c{self.sessionID}/recording{recID}/"
    
    def path_oe_oebin(self,recID):
        """Path of the .oebin file (xml with the structure)."""
        x=self.path_oe_root(recID)
        return x+"structure.oebin"
    def path_oe_syncmessages(self,recID):
        """Path of the sync messages file, the one created by OE when rec button is pressed."""
        x=self.path_oe_root(recID)
        return x+"sync_messages.txt"
    def path_oe_events_fullwords(self,recID):
        """Path of the events file."""
        x=self.path_oe_events_folder(recID)
        return x+'full_words.npy'
    def path_oe_events_samplenumbers(self,recID):
        """Path of the sample numbers associated with the events."""
        x=self.path_oe_events_folder(recID)
        return x+'sample_numbers.npy'
    def path_phy(self):
        """Path of the kilosort-created, phy-curated unit-spikes files."""
        return self.mainpath+f"{self.subjectName}/OpenEphys/m{self.subjectID}c{self.sessionID}/output/"
    def oe_recordings_count(self):
        """Count recordings of OpenEphys and create data structures accordingly."""
        bOK=True
        oe_folder=self.mainpath+f"{self.subjectName}/OpenEphys/m{self.subjectID}c{self.sessionID}/"
        self.recid_list=sorted([ int(f.name[9:]) for f in os.scandir(oe_folder) if (f.is_dir() and f.name[:9]=='recording')])
        if len(self.recid_list)<1:
            self.logger.error ("No OpenEphys recordings found")
            bOK=False
        else:
            self.oebin     = [None for r in range(max(self.recid_list)+1)]
            self.oe_events = [  {} for r in range(max(self.recid_list)+1)]
            self.logger.info(f"E recordings: {self.recid_list}")
        return bOK
        

    #*** Path building Level 1                                                      ***#
    #*** here the path constructors rely on the OpenEphys structure files           ***#
    #*** Particularly, folder names are given by OpenEphys differently each session ***#
    def path_oe_events_folder(self,recID):
        """TBC."""
        x = self.path_oe_root(recID)+'events/'
        x += self.oebin[recID]['continuous'][0]['folder_name']
        x += 'TTL/'
        return x



    def oe_oebin_bulk_load(self):
        """Load OpenEphys native JSON file with description of structure of the rest of the files.
        
        see https://open-ephys.github.io/gui-docs/User-Manual/Recording-data/Binary-format.html
        Unfortunately, crucial information about start times is not in the JSON file, but in 
        sync_messages.txt
        """
        bOK=True
        for recID in self.recid_list:
            oebin_path  =self.path_oe_oebin       (recID)
            sync_path   =self.path_oe_syncmessages(recID)
            with open(oebin_path,encoding='utf-8') as f:
                self.oebin[recID]=json.load(f)
            
            nopening=len("Start Time for ")
            
            #Find the start positions of each device
            with open(sync_path,encoding='utf-8') as f:
                S=f.readlines()
                            
            self.oebin[recID]['starttime']=int(S[0].split(":")[1])
            dev={}
            dev['pname'] = self.oebin[recID]['continuous'][0]['source_processor_name']
            dev['pid']   = self.oebin[recID]['continuous'][0]['source_processor_id']
            dev['sname'] = self.oebin[recID]['continuous'][0]['stream_name']
            dev['sync_name']=f"""{dev['pname']} ({dev['pid']}) - {dev['sname']}"""
            dev['namechar']=len(dev['sync_name'])
            for l in S[1:]:
                devname=l[nopening:nopening+dev['namechar']]
                if devname==dev['sync_name']:
                    s=l[nopening+dev['namechar']+3:]
                    w=s.split(':')
                    n0=int(w[1])
                    self.oebin[recID]['continuous'][0]['starttime']=n0
            self.logger.info(f"""recording{recID}:\t{dev['pname']}\t{n0}""")
        return bOK

    #***     SECTION 2                                                      ***#
    #***     Alignment of TEMPO log and OpenEphys events                    ***#
    def oe_ttl_bulk_load(self):
        """Load all events from NIDAQ."""
        bOK=True
        for recID in self.recid_list:
            try:
                W     =np.load(self.path_oe_events_fullwords    (recID))
                W_noframes=W%self.rtcodes['FRAME']
                
                N =np.load(self.path_oe_events_samplenumbers(recID))
                oe_events={}
                for code in self.rtcodes:
                    oe_events[code]=np.where(W_noframes==self.rtcodes[code])[0]

                #for istim in range(len(oe_events['STIM'])-1):
                #    stim_end_this=oe_events[
                A=[]
                for istim,stim_start in enumerate(oe_events['STIM_START']):
                    trial_start=np.max([i for i in oe_events['TRIAL_START'] if i<stim_start])
                    stim_end   =np.min([i for i in oe_events['STIM_END'] if i>stim_start])
                    trial_end  =np.min([i for i in oe_events['TRIAL_END'] if i>stim_start])

                    if istim==len(oe_events['STIM_START'])-1:
                        success = sum(oe_events['SUCCESS']>stim_start)>0
                        brokefix = sum(oe_events['BROKE_FIX']>stim_start)>0
                    else:
                        stim_start_next=oe_events['STIM_START'][istim+1]
                        success=sum((oe_events   ['SUCCESS']>stim_start) & (oe_events['SUCCESS']<stim_start_next))>0
                        brokefix=sum((oe_events['BROKE_FIX']>stim_start) & (oe_events['BROKE_FIX']<stim_start_next))>0
                            

                    A+=[{'trial_start':N[trial_start],
                       'stim_start' :N[stim_start],
                       'stim_end'   :N[stim_end],
                       'trial_end'  :N[trial_end],
                       'broke_fix'  :brokefix,
                       'success'    :success
                       }]
                A=pd.DataFrame(A)
                self.oe_events[recID]=A
                if len(A)==0:
                    success=0
                else:
                    success=sum(A['success'])
                self.logger.info(f"""recording{recID}:\t{len(A):4} logged\t{success:4} success """)
            except:
                self.logger.error(f"""recording{recID}""")
                bOK=False
        return bOK
    
    def tempo_events_load(self,recID):
        """Load the events from TEMPO files."""
        a=loadmat(self.path_tempo_mat(recID))
        #event_codes=a['good_data']['event_names']
        
        event_data=a['good_data']['event_data']
        #bad_event_data=a['bad_data']['event_data']
        nTrials=event_data.shape[1]

        #build table 1: essencial for comparison and alignment with
        #openphys data
        A=[]
        for iTr in range(nTrials):
            a={}
            for code in self.codes.keys():
                x=event_data[:,iTr]==self.codes[code]
                if np.sum(x)==0:
                    a[code]=None
                else:
                    x=np.where(x)[0]
                    if len(x)==1:
                        a[code]=x[0]
                    else:
                        a[code]=x
            A+=[a]
        A=pd.DataFrame(A)
        return A
    
    def align_tempo_oe_events(self,recID):
        """Align TEMPO and OpenEphys-recorded events."""
        tempo_events=self.tempo_events_load(recID).copy()
        oe_events=self.oe_events[recID].copy()
        #temporarily apply filter by success,
        #later: replace by broke_fix
        oe_events=oe_events[oe_events['success']]

        self.logger.debug(f"""alignment of recording{recID} started""")
        bOK=True
        
        #validation step 1: count the rows of "good data"
        bOK=len(oe_events)==len(tempo_events)

        #validation step 2: compare stim_start,stim_end and trial_end in ms
        #The way the events are stored in htb is aligning all events by stim_start
        #All events for validation purposes are normalized
        #such that stim_start=0 and the units are ms
        #i would try to compare the trial_start, but for some trials the
        #latency is more than 1s and then there is no trial_start event
        if ~bOK:
            self.logger.error('Cannot align trials: not the same amount')
        if bOK:
            self.logger.debug('Same amount of trials: OK')
            oe_t0=np.array(oe_events['stim_start'])
            tempo_t0=np.array(tempo_events['stim_start']).astype(int)
            
            for col in ['stim_start','trial_start','stim_end','trial_end']:
                tempo_events[col]-=tempo_t0
                
                oe_events[col]-=oe_t0
                oe_events[col]/=40 #requires attention
                
            for col in ['trial_end']:
                oe_col=np.array(oe_events[col])
                tempo_col=np.array(tempo_events[col])
                diff=abs(oe_col-tempo_col)
                bOK=sum(diff>0.5)==0
                if bOK:
                    self.logger.debug(f'Maximal latency between Tempo and OpenEphys is {np.max(diff)}ms (htb time resolution is 1ms)')
                else:
                    badtrials=list(np.where(diff)[0])
                    self.logger.error(f"These trials require attention: {badtrials}")
        return bOK
                
            
    #***     SECTION 3 (preparation for spike sorting)                      ***#
    #***     Stiching the AP data                                           ***#
    #***    This is done by a separate script, Stitch/npx_tempo_stitch.py   ***#

    #***     SECTION 4  (following spike sorting)                           ***#
    #***     Raster Plots and export                                        ***#
    def load_cont_rasters(self):
        """
        Build raster for good units and multi units.
        
        structure: dict, keys: good, mua
            raster['good'] and raster['mua'] are dict
            keys: cluster numbers,
            values: spike times
            Assuming 624 is a good unit
            raster['good'][624] is list of spike times of unit 624
        """
        pth=self.path_phy()
        self.logger.info("""Loading rasters from phy started: """)
        spike_clusters=np.squeeze(np.load(pth+'spike_clusters.npy'))
        spike_times=np.squeeze(np.load(pth+'spike_times.npy'))
        spikes=pd.DataFrame({'cluster':spike_clusters,'time':spike_times})
        #print (spikes.head())
        cluster_group=pd.read_csv(pth+'cluster_group.tsv',sep='\t')
        clusters={}
        raster={}
        for group in ['good','mua']:
            raster[group]={}
            clusters[group]=list(cluster_group[cluster_group['group']==group]['cluster_id'])
            #print (len(clusters[group]))
            for c in clusters[group]:
                raster[group][c]=spikes[spikes['cluster']==c]['time']
        self.logger.info(f"""{len(raster['good'])} good units, {len(raster['mua'])} mua """)
        return raster
    
    def build_trig_raster(self,recID:int):
        """
        Build the main spike rasters for further analysis.
        
        Based on the continuous rasters, aligned events, and synchronization
        data, build raster plots for each unit (good and mua)
        
        Builds for a specific recording
        
        """
        raster=self.load_cont_rasters()
        oe_events=self.oe_events[recID].copy()
        
        #spikes_t0=self.oebin['']
        oe_t0=0
        
        ntrials=len(oe_events)
        
        nidaq_sampling_rate=40000
        npx_sampling_rate=30000
        
        samples_pre=2*npx_sampling_rate
        samples_post=3*npx_sampling_rate
        
        for group in ['good','mua']:
            trig_raster={}
            trig_raster[group]={}
            units=raster[group].keys()
            for unit in units:
                trig_raster[group][unit]=[[] for i in range(ntrials)]
                
            for iTrial in range(ntrials):
                vstart_nidaq_index=oe_events.loc[iTrial,'stim_start']
                vstart_time=vstart_nidaq_index*1.0/nidaq_sampling_rate
                vstart_npx_index=int(vstart_time*npx_sampling_rate)
                
                slice_start_acq=vstart_npx_index-samples_pre
                slice_n0_acq=vstart_npx_index
                slice_end_acq=vstart_npx_index+samples_post
                
                slice_start_phy=slice_start_acq
                slice_n0_phy=slice_n0_acq
                slice_end_phy=slice_end_acq
                
                
                spikes={}
                
                for unit in units:
                    trig_raster[group][unit][iTrial]=[round((s-slice_n0_phy)*1.0/npx_sampling_rate,3) for s in raster[group][unit] if (s>slice_start_phy) and (s<=slice_end_phy)]
        return trig_raster
            
        #print (oe_events)
        
        
    
    def logging_start(self):
        """Init logging procedures."""
        now = datetime.now() # current date and ti
        nowstr=now.strftime("%Y%m%d_%H%M%S")
        
        lg=logging.getLogger('npx_tempo')
        lg.setLevel(logging.DEBUG)
        frmt=logging.Formatter('%(filename)s:%(lineno)s \t  %(funcName)s \t %(levelname)s \t %(message)s')
                
        fh=logging.FileHandler('LOGS/npx_tempo'+nowstr+'.log')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(frmt)        
        lg.addHandler(fh)
        
        
        ch=logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(frmt)
        lg.addHandler(ch)
        
        
        lg.info('started')
        self.logger=lg
        self.logging_h={'fh':fh,'ch':ch}
        
    def logging_end(self):
        self.logger.removeHandler(self.logging_h['fh'])
        self.logger.removeHandler(self.logging_h['ch'])
        
if __name__=="__main__":
    #logging_start()
    #if True:
    """Init logging procedures."""
    now = datetime.now() # current date and ti
    nowstr=now.strftime("%Y%m%d_%H%M%S")
    
    
        
        
    PATH="Z:/Data/MOOG/"
    """C=npx_tempo(mainpath=PATH,subjectID=42,subjectName='Dazs',sessionID=461)
    
    raster=C.build_trig_raster(1)
    with open('raster.p','wb') as h:
        pickle.dump(raster,h)"""
    
    with open('raster.p','rb') as h:
        raster=pickle.load(h)
    #f=[None for i in [1,2]]
    f=figure(width=600,height=200)
    #f[1]=figure(width=600,height=600)
    group='good'
    units=list(raster[group].keys())
    nTrials=len(raster[group][units[0]])
    
    for iunit,unit in enumerate(units):
        output_file(f'Figures/raster_{group}_unit{unit}.html')
        for iTrial in range(nTrials):
            spike_times=np.array(raster[group][unit][iTrial])
            f.scatter(spike_times,0*spike_times+iTrial)
        save(f)


