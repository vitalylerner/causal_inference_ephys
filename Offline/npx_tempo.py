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

"""
This class aligns events recorded with OpenEphys
with the stimuli and behavioral data from TEMPOW
"""

class npx_tempo:
        subjectID   = None
        subjectName = None
        sessionID   = None
        mainpath    = None

        recid_list  = None
        oebin       = None
        oe_events   = None

        codes  ={'trial_start':1,'stim_start':4,'stim_end':5,'trial_end':15,'success':12,'broke_fix':10}
        rtcodes={'TRIAL_START':1,'STIM_START':2,'STIM_END':4,'TRIAL_END':8,'SUCCESS':16,'BROKE_FIX':32,'FRAME':128}

    

        def __init__(self,**kwargs):
                argnames=kwargs.keys
                bOK=False
                logging.info('\n ***** Vitaly Lerner, January 2024 ****\n ** Offline preprocessing of ephys data recorded continuously **')
                logging.warning('Currently the filter by "success" is applied\n to events recorded in OpenEphys, this is wrong generally It works for non-discrimination tasks, but must be replaced with a filter by BROKE_FIX. ')

                # Validate arguments and fill the object parameters
                try:
                        self.subjectID      = kwargs['subjectID']
                        self.subjectName    = kwargs['subjectName']
                        self.sessionID      = kwargs['sessionID']
                        self.mainpath       = kwargs['mainpath']
                        for var in kwargs.keys():
                                logging.info(f"""{var}\t{kwargs[var]}""")
                        bOK=True
                except:
                        logging.error("not enough context information provided")

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
                return self.mainpath+f"{self.subjectName}/m{self.subjectID}c{self.sessionID}r{recID}.log"
        def path_tempo_htb(self,recID):
                x=self.path_tempo_log(recID)
                return x[:-4]+".htb"
        def path_tempo_mat(self,recID):
                x=self.path_tempo_htb(recID)
                return x+".mat"
            
        def path_oe_root(self,recID):
                return self.mainpath+f"{self.subjectName}/OpenEphys/m{self.subjectID}c{self.sessionID}/recording{recID}/"
        def path_oe_oebin(self,recID):
                x=self.path_oe_root(recID)
                return x+"structure.oebin"
        def path_oe_syncmessages(self,recID):
                x=self.path_oe_root(recID)
                return x+"sync_messages.txt"
        def path_oe_events_fullwords(self,recID):
                x=self.path_oe_events_folder(recID)
                return x+'full_words.npy'
        def path_oe_events_samplenumbers(self,recID):
                x=self.path_oe_events_folder(recID)
                return x+'sample_numbers.npy'
        def oe_recordings_count(self):
                bOK=True
                oe_folder=self.mainpath+f"{self.subjectName}/OpenEphys/m{self.subjectID}c{self.sessionID}/"
                self.recid_list=sorted([ int(f.name[9:]) for f in os.scandir(oe_folder) if (f.is_dir() and f.name[:9]=='recording')])
                if len(self.recid_list)<1:
                        logging.error ("No OpenEphys recordings found")
                        bOK=False
                else:
                        self.oebin     = [None for r in range(max(self.recid_list)+1)]
                        self.oe_events = [  {} for r in range(max(self.recid_list)+1)]
                        logging.info(f"E recordings: {self.recid_list}")
                return bOK


        #*** Path building Level 1                                                      ***#
        #*** here the path constructors rely on the OpenEphys structure files           ***#
        #*** Particularly, folder names are given by OpenEphys differently each session ***#
        def path_oe_events_folder(self,recID):
                x = self.path_oe_root(recID)+'events/'
                x += self.oebin[recID]['continuous'][0]['folder_name']
                x += 'TTL/'
                return x



        def oe_oebin_bulk_load(self):
                # load open-ephys native JSON file with description of structure of the rest of the files
                # see https://open-ephys.github.io/gui-docs/User-Manual/Recording-data/Binary-format.html
                # Unfortunately, crucial information about start times is not in the JSON file, but in 
                # sync_messages.txt
                bOK=True
                for recID in self.recid_list:
                        oebin_path  =self.path_oe_oebin       (recID)
                        sync_path   =self.path_oe_syncmessages(recID)
                        with open(oebin_path) as f:
                                        self.oebin[recID]=json.load(f)
                        
                        nopening=len("Start Time for ")
                        
                        #Find the start positions of each device
                        with open(sync_path) as f:
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
                        logging.info(f"""recording{recID}:\t{dev['pname']}\t{n0}""")
                return bOK

        #***     SECTION 2                                                      ***#
        #***     Alignment of TEMPO log and OpenEphys events                    ***#
        def oe_ttl_bulk_load(self):
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
                                logging.info(f"""recording{recID}:\t{len(A):4} logged\t{success:4} success """)
                        except:
                                logging.error(f"""recording{recID}""")
                                bOK=False
                return bOK
        
        def tempo_events_load(self,recID):
                
            a=loadmat(self.path_tempo_mat(recID))
            event_codes=a['good_data']['event_names']
            
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
            tempo_events=self.tempo_events_load(recID).copy()
            oe_events=self.oe_events[recID].copy()
            #temporarily apply filter by success,
            #later: replace by broke_fix
            oe_events=oe_events[oe_events['success']]

            logging.debug(f"""alignment of recording{recID} started""")
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
                logging.error('Cannot align trials: not the same amount')
            if bOK:
                logging.debug('Same amount of trials: OK')
                nTrials=len(oe_events)
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
                        logging.debug(f'Maximal latency between Tempo and OpenEphys is {np.max(diff)}ms (htb time resolution is 1ms)')
                    else:
                        badtrials=list(np.where(diff)[0])
                        logging.error(f"These trials require attention: {badtrials}")
            return bOK
                    
                
        #***     SECTION 3 (preparation for spike sorting)                      ***#
        #***     Stiching the AP data                                           ***#


        #***     SECTION 4  (following spike sorting)                           ***#
        #***     Raster Plots and export                                        ***#



PATH="Z:/Data/MOOG/"

if __name__=="__main__":
        now = datetime.now() # current date and ti
        nowstr=now.strftime("%Y%m%d_%H%M%S")
        logging.basicConfig(level=logging.DEBUG,
            handlers=[
                    logging.FileHandler('LOGS/npx_tempo'+nowstr+'.log'),
                    logging.StreamHandler()
                    ],
             format='%(filename)s:%(lineno)s \t  %(funcName)s \t %(levelname)s \t %(message)s')
        logging.info('started')
        C=npx_tempo(mainpath=PATH,subjectID=42,subjectName='Dazs',sessionID=454)
        bOK=C.align_tempo_oe_events(6)
        #print (C.path_oe_oebin(1))
