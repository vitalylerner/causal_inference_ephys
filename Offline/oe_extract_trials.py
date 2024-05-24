# -*- coding: utf-8 -*-
"""
Created on Thu May  9 11:48:59 2024

@author: DeAngelis Lab
"""

"""
TODO: unify and structure directories, 
currently it's a mess. One place for all, at least
ephys. 
"""
from open_ephys.analysis import Session
import numpy as np
import pandas as pd

directory = 'D:/IMEC_DATA/m42/m42c527' 

session = Session(directory)
recordnode=session.recordnodes[0]
recnum=len(recordnode.recordings)

#the real time and the offline differ by 1
# because of the different counting
# OpenEphys starts counting from 1
nidaq_lines={'trial start':1,
             'vstim start':2,
             'vstim end'  :3,
             'trial end'  :4,
             'success'    :5,
             'break'      :6,
             'frame'      :8,
             'sync'       :13}

dev_name={'nidaq':'PXIe-6341','npx_ap':'ProbeA-AP','npx_lfp':'ProbeA-LFP'}
dev_index={'nidaq':2.0,'npx_ap':0.0,'npx_lfp':1.0}
dev_keys=list(dev_name.keys())
trials_table=[]

tmp_dev={}
for dev in dev_keys:
    tmp_dev[dev]=0
shift=[ tmp_dev.copy() for irec in range(recnum) ]



for irec in range(recnum):
    rec=recordnode.recordings[irec]
    for dev in dev_keys:
        sample_numbers   = rec.continuous[int(dev_index[dev])].sample_numbers
        
        
        shift[irec][dev]+=sample_numbers[0]
        for jrec in range(irec+1,recnum):
            shift[jrec][dev]-=len(sample_numbers)
shift=pd.DataFrame.from_dict(shift)    

 
for irec in range(recnum):
    print (f"processing triggers of recording#{irec+1}")
    rec=recordnode.recordings[irec]
    E=rec.events

    
    ts_nidaq   = rec.continuous[int(dev_index['nidaq'])].timestamps
    ts_npx_ap  = rec.continuous[int(dev_index['npx_ap'])].timestamps
    ts_npx_lfp = rec.continuous[int(dev_index['npx_lfp'])].timestamps
    
    sn_nidaq_stitch = rec.continuous[int(dev_index['nidaq'])].sample_numbers-list(shift['nidaq'])[irec]
    sn_nidaq_stitch = rec.continuous[int(dev_index['nidaq'])].sample_numbers-list(shift['nidaq'])[irec]
    sn_nidaq_stitch = rec.continuous[int(dev_index['nidaq'])].sample_numbers-list(shift['nidaq'])[irec]
    
    #print (E)
    events_nidaq=E[E['stream_index']==dev_index['nidaq']]
    events_nidaq_re=events_nidaq[events_nidaq['state']==1]
    sync_nidaq  = events_nidaq_re[events_nidaq_re['line']==nidaq_lines['sync'] ][['sample_number','timestamp']]
    vstim_start = events_nidaq_re[events_nidaq_re['line']==nidaq_lines['vstim start']][['sample_number','timestamp']]
    vstim_end   = events_nidaq_re[events_nidaq_re['line']==nidaq_lines['vstim end']][['sample_number','timestamp']]
    break_fix   = events_nidaq_re[events_nidaq_re['line']==nidaq_lines['break']][['sample_number','timestamp']]
    success     = events_nidaq_re[events_nidaq_re['line']==nidaq_lines['success']][['sample_number','timestamp']]
    
    sync_npx_ap=E[ (E['stream_index']==dev_index['npx_ap'] ) & (E['state']==1)][['sample_number','timestamp']]
    sync_npx_lfp=E[ (E['stream_index']==dev_index['npx_lfp'] ) & (E['state']==1)][['sample_number','timestamp']]
    
    
    trials=len(vstim_start)
    #print (trials)
    #print (list(sync_npx_ap['timestamp']))
    
    ard_sync_ap  = np.array(list(sync_npx_ap['timestamp']), dtype=float)
    #ard_sync_ap=[ard_sync_ap[k+1]-ard_sync_ap[]]
    ard_sync_lfp = np.array(list(sync_npx_lfp['timestamp']),dtype=float)
    trial_num=1
    for itrial in range(trials):
        
        #sample number and timestamp of visual stimulus start 
        # by an event set from tempo to nidaq
        trial_ts=float(list(vstim_start['timestamp'])[itrial])
        trial_index=int(list(vstim_start['sample_number'])[itrial])
        
        #find the closest sample at npx-ap
        npx_ap_sample_index=np.argmin(np.abs(ts_npx_ap-trial_ts))
        npx_ap_sample=ts_npx_ap[npx_ap_sample_index]
        
        #find the closest sample at npx-lfp
        npx_lfp_sample_index=np.argmin(np.abs(ts_npx_lfp-trial_ts))
        npx_lfp_sample=ts_npx_lfp[npx_lfp_sample_index]
        
        #validation by arduino generated signal
        ard_sync_trial_ap=ard_sync_ap-trial_ts
        ard_sync_trial_ap=ard_sync_trial_ap[abs(ard_sync_trial_ap)<1]*1000
        
        ard_pass=len(ard_sync_trial_ap)>0
        if ard_pass:
            ard_sync_trial_ap_min=np.min(np.abs(ard_sync_trial_ap))
            ard_pass=ard_sync_trial_ap_min<25
            
        if ard_pass:
            ard_sync_trial_ap=ard_sync_ap-trial_ts
            sample_ap=int(sync_npx_ap.iloc[np.argmin(np.abs(ard_sync_trial_ap))]['sample_number'])
            sample_ap_stitch=sample_ap-list(shift['npx_ap'])[irec]
            
            ard_sync_trial_lfp=ard_sync_lfp-trial_ts
            sample_lfp=int(sync_npx_lfp.iloc[np.argmin(np.abs(ard_sync_trial_lfp))]['sample_number'])
            sample_lfp_stitch=sample_lfp-list(shift['npx_lfp'])[irec]
            
            
            broke_fix=np.sum( (break_fix['timestamp']-trial_ts<2.1 )  & (break_fix['timestamp']-trial_ts>0.0) )==1
            trial_success=np.sum( (success['timestamp']-trial_ts<3.0) & (success['timestamp']-trial_ts>2.0))==1
            
            
            trials_table+=[{'rec':irec+1,'trial':trial_num,'broke_fix':broke_fix,
                            'success':trial_success,'ap in acq':sample_ap,'lfp in acq':sample_lfp,
                            'ap in stitch':sample_ap_stitch,'lfp in stitch':sample_lfp_stitch}]
            trial_num+=1
            #print (sample_ap,sample_lfp)
        #ard_sync= np.where( ((ard_sync-trial_ts)<0.5) &  ((ard_sync-trial_ts)>0)  )
        
        
        #print (trial_ts,ard_pass)
trials_data=pd.DataFrame.from_dict(trials_table)

trials_data.to_csv(directory+'/Trials.csv',index=False)
    #print (len(sync_npx_ap),len(sync_nidaq))

        