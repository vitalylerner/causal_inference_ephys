# -*- coding: utf-8 -*-
"""
This is a UI for 
npx-tempo real time analysis
Currently, it is just sending kill signal
needs some work
"""

from npx_rt import npx_rt_globals,npx_rt_client
from threading import Timer
import time

from tkinter import *

class npx_rt_gui(npx_rt_client,Tk):
    """Neuropixel Real Time GUI
    
    Currently there is no gui, just functions for communication
    """
    
    flags={}
    hub_flags={}
    trial_params={}
    
    status=['acquisition','trial','vstim']
    status_lbl={}
    def monitor_trial(self):
        if not (self.flags['stop']):
            if True:#self.hub_flags['vstim']:
                self.trial_params=self.request('trial?')
                print (self.trial_params)
            Timer(2,self.monitor_trial).start()
            
    def monitor_status(self):
        if not(self.flags['stop']): 
            self.hub_flags=self.request('status?')
            #print (self.hub_flags)
            Timer(0.5,self.monitor_status).start()
    def __init__(self):
        npx_rt_client.__init__(self,npx_rt_globals.processes.gui,npx_rt_globals.processes.hub)
        Tk.__init__(self)
        self.flags['stop']=False
        self.layout()
        Timer(1,self.monitor_status).start()
        Timer(1.5,self.monitor_trial).start()
    
    def layout(self):
        self.title('Neuropixel Real Time Analysis')
        self.geometry('600x600')
        for ist,st in enumerate(self.status):
            self.status_lbl[st]=Label(self,text=st)
            self.status_lbl[st].grid(column=ist,row=0)
    def stop(self):
        
        self.send("stop")
        self.flags['stop']=True

if __name__=="__main__":
    n=npx_rt_gui()

    """lblAcquisition=Label(root,text='Acquisition')
    lblAcquisition.grid(column=1,row=1)
    lblAcquisition.config(bg='green')
    lblTrial=Label(root,text='Trial')
    lblTrial.grid(column=1,row=2)
    #lbl.grid()"""
    n.mainloop()
    #ntgui=npx_rt_gui()
    #time.sleep(0.5)
    #ntgui.stop()
    #x=ntgui.request('status?')
    #print (x)
    #time.sleep(20)
    #ntgui.stop()
    
    

