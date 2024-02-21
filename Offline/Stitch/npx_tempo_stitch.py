# -*- coding: utf-8 -*-
"""
Created on Mon Jan 15 14:33:28 2024

Vitaly Lerner
Stiching the .dat files from OpenEphys before kilosorting 

"""

import os
import numpy as np
import shutil 

import tkinter as tk
from tkinter import filedialog

#path="Z:/Data/MOOG/Dazs/OpenEphys/m42c461/"
root = tk.Tk()



def npx_oe_stitch(path_root:str):
    """Stitch data and timestamps of openephys recordings."""
    def assign_subfolder():
        if data_source=='AP':
            sf=[s for s in list(os.listdir(recfolder)) if (s[:5]=="Neuro") and (s[-2:]=="AP")][0]
        elif data_source=='LFP':
            sf=[s for s in list(os.listdir(recfolder)) if (s[:5]=="Neuro") and (s[-3:]=="LFP")][0]
        elif data_source == 'Analog':
            sf=[s for s in list(os.listdir(recfolder)) if s[:8]=="NI-DAQmx"][0]
        return sf
    RecNums=sorted([int(l[len("recording"):]) for l in list(os.listdir(path_root)) if l[:len("recording")]=="recording"])
    stitchpath=path_root+'STITCH/'
    if not os.path.exists(stitchpath):
        os.mkdir(stitchpath)
        
    
    for data_source in ['AP','LFP','Analog']:
        # stictch data
        """
        stitchfile=stitchpath+data_source+'.dat'
        fOut=open(stitchfile,'wb')
        for irec in RecNums: 
            recfolder=path+f"recording{irec}/continuous/"
            subfolder=assign_subfolder()
            infile=recfolder+subfolder+'/continuous.dat'
            fIn=open(infile,'rb')
            shutil.copyfileobj(fIn, fOut)
            fIn.close()
        fOut.close()
        """
        # stitch timestamps and sample numbers
        sync_file=stitchpath+data_source+'_sync.npz'
        time_stamps=[]
        sample_numbers=[]
        for irec in RecNums:
            recfolder=path+f"recording{irec}/continuous/"
            subfolder=assign_subfolder()
            sn_file=recfolder+subfolder+'/sample_numbers.npy'
            ts_file=recfolder+subfolder+'/timestamps.npy'
            time_stamps+=[np.load(ts_file)]
            sample_numbers+=[np.load(sn_file)]
        time_stamps=np.hstack(time_stamps)
        sample_numbers=np.hstack(sample_numbers)
        np.savez_compressed(sync_file, time_stamps=time_stamps,sample_numbers=sample_numbers)
        del(time_stamps)
        del(sample_numbers)

if __name__=="__main__"                                     :
    path = filedialog.askdirectory(title="Experiment path",initialdir='D:/DATA/IMEC_DATA/')+'/'#, filetypes=(("text    files","*.txt"), ("all files","*.*")))
    npx_oe_stitch(path)