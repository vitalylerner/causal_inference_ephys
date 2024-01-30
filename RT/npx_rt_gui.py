# -*- coding: utf-8 -*-
"""
This is a UI for 
npx-tempo real time analysis
Currently, it is just sending kill signal
needs some work
"""

from npx_rt import npx_rt_globals,npx_rt_client

import time

class npx_rt_gui(npx_rt_client):
    
    flags={}
    def __init__(self):
        npx_rt_client.__init__(self,npx_rt_globals.processes.gui,npx_rt_globals.processes.hub)
        self.flags['stop']=False
    
    def stop(self):
        
        self.send("stop")
        self.flags['stop']=True

if __name__=="__main__":
    ntgui=npx_rt_gui()
    time.sleep(2)
    ntgui.stop()

