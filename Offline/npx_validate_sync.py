# -*- coding: utf-8 -*-
"""
Created on Sat May  4 13:10:19 2024

@author: DeAngelis Lab
"""
from bokeh.plotting import figure as bk_figure, output_file as bk_output_file, save as bk_save, show as bk_show
import numpy as np    
import os

def npx_validate_sync(path:str,graphics:bool=False):
    folder_sync=path+'SYNC/'
    file_nidaq_name=[a for a in list(os.listdir(folder_sync)) if a[:5]=='nidaq'][0]
    file_npx_name=[a for a in list(os.listdir(folder_sync)) if a[:3]=='npx'][0]
    #print (file_nidaq_name,file_npx_name)
    
    nidaq_sr=40000
    npx_sr=30000
    
    nidaq_clk=np.loadtxt(folder_sync+file_nidaq_name,dtype=np.float32)/nidaq_sr
    npx_clk  =np.loadtxt(folder_sync+file_npx_name,dtype=np.float32)/npx_sr
    
    nidaq_clk_period=np.diff(nidaq_clk)
    npx_clk_period  =np.diff(npx_clk)
    
    nidaq_n=np.arange(nidaq_clk.size)
    npx_n  = np.arange(npx_clk.size)
    
    
    
    if graphics:
        f1=bk_figure(width=800,height=400)
        f1.line(npx_n[:-1],npx_clk_period,color='green')
        f1.line(nidaq_n[:-1],nidaq_clk_period,color='red')
        bk_show(f1)
if __name__=="__main__"                                     :
    #path = filedialog.askdirectory(title="Experiment path",initialdir='D:/DATA/IMEC_DATA/')+'/'#, filetypes=(("text    files","*.txt"), ("all files","*.*")))
    path='D:/IMEC_DATA/m42/m42c527/'
    bk_output_file('test.html')
    npx_validate_sync(path,True)
   