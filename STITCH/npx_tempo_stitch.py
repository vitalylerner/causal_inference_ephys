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

path = filedialog.askdirectory(title="Experiment path",initialdir='D:/DATA/IMEC_DATA/')+'/'#, filetypes=(("text    files","*.txt"), ("all files","*.*")))
print (path)

#root.mainloop()
#print ("aa")
#root.quit()

#path='D:/IMEC_DATA/m42/m42c461/Record Node 107/experiment2/'

RecNums=sorted([int(l[len("recording"):]) for l in list(os.listdir(path)) if l[:len("recording")]=="recording"])
#nums=[l for l in L]
stitchpath=path+'STITCH/'

for data_source in ['AP','LFP','Analog']:
    
    stitchfile=stitchpath+data_source+'.dat'
    if not os.path.exists(stitchpath):
        os.mkdir(stitchpath)
        
    fOut=open(stitchfile,'wb')
    
    for irec in RecNums: 
        recfolder=path+f"recording{irec}/continuous/"
        if data_source=='AP':
            subfolder=[s for s in list(os.listdir(recfolder)) if (s[:5]=="Neuro") and (s[-2:]=="AP")][0]
        elif data_source=='LFP':
            subfolder=[s for s in list(os.listdir(recfolder)) if (s[:5]=="Neuro") and (s[-3:]=="LFP")][0]
        elif data_source == 'Analog':
            subfolder=[s for s in list(os.listdir(recfolder)) if s[:8]=="NI-DAQmx"][0]
            
        
        infile=recfolder+subfolder+'/continuous.dat'
        #with load
        print (infile)
        fIn=open(infile,'rb')
        shutil.copyfileobj(fIn, fOut)
        fIn.close()
    fOut.close()
