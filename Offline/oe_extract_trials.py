# -*- coding: utf-8 -*-
"""
Created on Thu May  9 11:48:59 2024

@author: DeAngelis Lab
"""

from open_ephys.analysis import Session
import numpy as np

directory = 'D:/IMEC_DATA/m42/m42c527' 

session = Session(directory)
recordnode=session.recordnodes[0]
recnum=len(recordnode.recordings)

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

for irec in [0]:#range(recnum):
    print (irec)
    rec=recordnode.recordings[irec]
    E=rec.events

    
    ts_nidaq   = rec.continuous[int(dev_index['nidaq'])].timestamps
    ts_npx_ap  = rec.continuous[int(dev_index['npx_ap'])].timestamps
    ts_npx_lfp = rec.continuous[int(dev_index['npx_lfp'])].timestamps
    
    #print (E)
    events_nidaq=E[E['stream_index']==dev_index['nidaq']]
    events_nidaq_re=events_nidaq[events_nidaq['state']==1]
    sync_nidaq  = events_nidaq_re[events_nidaq_re['line']==nidaq_lines['sync'] ][['sample_number','timestamp']]
    vstim_start = events_nidaq_re[events_nidaq_re['line']==nidaq_lines['vstim start']][['sample_number','timestamp']]
    vstim_end   = events_nidaq_re[events_nidaq_re['line']==nidaq_lines['vstim end']][['sample_number','timestamp']]
    break_fix   = events_nidaq_re[events_nidaq_re['line']==nidaq_lines['break']][['sample_number','timestamp']]
    
    sync_npx_ap=E[ (E['stream_index']==dev_index['npx_ap'] ) & (E['state']==1)][['sample_number','timestamp']]
    sync_npx_lfp=E[ (E['stream_index']==dev_index['npx_lfp'] ) & (E['state']==1)][['sample_number','timestamp']]
    
    
    trials=len(vstim_start)
    print (trials)
    print (list(sync_npx_ap['timestamp']))
    for itrial in range(trials):
       
        trial_ts=float(list(vstim_start['timestamp'])[itrial])
        trial_index=int(list(vstim_start['sample_number'])[itrial])
        
        npx_ap_sample_index=np.argmin(np.abs(ts_npx_ap-trial_ts))
        npx_ap_sample=ts_npx_ap[npx_ap_sample_index]
        
        print (trial_ts,npx_ap_sample)
        #print (npx_ap_sample_index)
        
                                
        
    #print(events_npx)
    print (len(sync_npx_ap),len(sync_nidaq))
   # print (len(vstim_start),len(break_fix))
    #for dev in range(3):
    #    ts=rec.continuous[dev].timestamps
    #    print (len(ts),ts[0],ts[-1])
        