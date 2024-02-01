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

from tkinter import Tk,Label,Button

class npx_rt_gui(npx_rt_client,Tk):
    """Neuropixel Real Time GUI.
    
    Currently there is no gui, just functions for communication
    """
    
    flags={}
    hub_flags={}
    hub_report={}
    trial_params={}
    
    status={'nidaq':False,'npx':False,'acquisition':False,'recording':False,
            'trial':False,'vstim':False}
    n_indicators={'buffer cursor':0}
    
    status_lbl={}
    n_indicator_lbl={}
    n_indicator_val={}
    
    def monitor_trial(self):
        """Monitor trial parameters, retrieve from hub and display here."""
        if not (self.flags['stop']):
            if True:#self.hub_flags['vstim']:
                self.trial_params=self.request('trial?')
                #print (self.trial_params)
            Timer(2,self.monitor_trial).start()
            
    def monitor_status(self):
        """Monitor general status, such as acquisition, recording, stimuli etc."""
        if not(self.flags['stop']): 
            self.hub_flags=self.request('status?')
            #print (self.hub_flags)
            
            self.status['acquisition']=self.hub_flags['nidaq_acquisition']
            self.status['trial']=self.hub_flags['trial']
            self.status['vstim']=self.hub_flags['vstim']
            self.status['nidaq']=self.hub_flags['nidaq_connected']
            self.status['npx']=self.hub_flags['npx_connected']
            self.status['recording']=self.hub_flags['recording']
            
            for ist,st in enumerate(list(self.status.keys())):
                if self.status[st]:
                    self.status_lbl[st].config(bg='green')
                else:
                    self.status_lbl[st].config(bg='grey')
            self.hub_report=self.request('report?')
            self.n_indicators['buffer cursor']=self.hub_report['buffer_cursor']
            self.n_indicator_val['buffer cursor'].config(text=self.hub_report['buffer_cursor'])
            #print (self.hub_report)
            Timer(0.5,self.monitor_status).start()
    def __init__(self):
        npx_rt_client.__init__(self,npx_rt_globals.processes.gui,npx_rt_globals.processes.hub)
        Tk.__init__(self)
        self.flags['stop']=False
        self.layout()
        Timer(1,self.monitor_status).start()
        Timer(1.5,self.monitor_trial).start()
    
    def layout(self):
        """Build the layout of the window."""
        self.title('Neuropixel Real Time Analysis')
        self.geometry('600x600')
        design={'padx':1,'font':("Helvetica",11)}
        
        c=0
        for ist,st in enumerate(list(self.status.keys())):
            self.status_lbl[st]=Label(self,text=st,**design)
            #self.status_lbl[st].grid(column=ist+2,row=0)
            x=(len(st)+2)*7
            
            self.status_lbl[st].place(x=c,y=5)
            c+=x
        for j,i in enumerate(list(self.n_indicators.keys())):
            self.n_indicator_lbl[i]=Label(self,text=i,**design)
            #self.n_indicator_lbl[i].grid(column=0,row=j+1)
            self.n_indicator_val[i]=Label(self,
                                          text=f"""{self.n_indicators[i]}""",
                                          **design)
            #self.n_indicator_val[i].grid(column=1,row=j+1)
            self.n_indicator_lbl[i].place(x=j*200,y=40)
            self.n_indicator_val[i].place(x=j*200+100,y=40)
        self.cmdClose=Button(self,text="stop",command=self.stop)
        self.cmdClose.place(x=550,y=5)
    def stop(self):
        """Stop the socket and stop the hub."""
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
    
    

