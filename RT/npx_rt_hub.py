##!/usr/bin/env python

#This is the main process of real time analysis 
# for neuropixel - tempo

import socket,struct,time
from threading import Timer
from npx_rt import npx_rt_globals
import numpy as np


main_run=True

class npx_rt_hub():
    stop=False
    s=None
    nidaq_events=['connection','trial start','vstim start',
                  'vstim end','trial end','sync',
                  'acquisition start','acquisition stop']
    
    npx_events=['connection','sync','acquisition start','acquisition stop']
    
    events_sp=['matrix']
    
    pos={}
    flags={}
    def __init__(self):
        self.s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (npx_rt_globals.tempowave_tcpip,
                          npx_rt_globals.processes.hub) 
        self.s.bind(server_address)
        self.s.listen(1)
        
        self.flags['stop']              = False
        self.flags['trial']             = False
        self.flags['vstim']             = False
        self.flags[  'npx_acquisition'] = False
        self.flags['nidaq_acquisition'] = False
        
        
        
        self.pos['nidaq']={}
        for ev in self.nidaq_events:
          self.pos['nidaq'][ev]=-1
          
        self.pos['npx']={}
        for ev in self.npx_events:
          self.pos['npx'][ev]=-1

        
        Timer(1,self.listen).start()
    def display(self):
        
        while self.flags[f'nidaq_acquisition']:
            print(self.pos['nidaq'])
            time.sleep(2)
            
    def listen(self):
        connection,client_address=self.s.accept()

        
        
        def recv_str(l:int):
            return connection.recv(MsgLen).decode('utf-8')
        def recv_int():
            return struct.unpack("i",connection.recv(4))[0]
        
        def recv_matrix():
        # protocol:
        #==============================================
        # order | content  |  type  | bytes           | 
        #----------------------------------------------
        #   1*  | procId   |  int   |  4              |
        #   2*  |    6     |  int   |  4              |
        #   3*  | "matrix" |  str   |  6              |
        #   4   |   rows   |  int   |  4              |
        #   5   |   cols   |  int   |  4              |
        #   6   |   data   |  float | 4 × rows × cols |
        #==============================================
        # * these are received prior to receiving matrix, so here 
        #   we start with row#4
            rows=recv_int()
            cols=recv_int()
            l=rows*cols
            return np.reshape(list(struct.unpack("%sf"%l,connection.recv(l*4))),(rows,cols))
            #np.reshape(list(struct.unpack("%sf"%10,m)),(2,5))
        #print (ProcID,MSG)
        
        ProcID=recv_int()
        MsgLen=recv_int()
        MSG=recv_str(MsgLen)
        if ProcID==npx_rt_globals.processes.gui:
            
            if MSG=='stop':
                self.flags['stop']=True
                connection.close()
                
        elif ProcID==npx_rt_globals.processes.oe_npx:
            #print ('npx', MSG)
            
            for event in self.events_sp:
                if MSG[:len(event)]==event:
                    if event=='matrix':
                        M=recv_matrix()
                        print ('received matrix M.shape')
                                    
            for event in self.npx_events:
                if MSG[:len(event)]==event:
                    n=int(MSG[len(event):])
                    self.pos['npx'][event]=n
                    if   event == 'acquisition start':
                        self.flags['npx_acquisition']=True
                        self.display()
                    elif event == 'acquisition stop':
                        self.flags['npx_acquisition']=False
                    elif event =='connection':
                            print ('npx connected!')    
                
                
                connection.close()
                
        elif ProcID==npx_rt_globals.processes.oe_nidaq:
            for event in self.nidaq_events:
                if MSG[:len(event)]==event:
                    n=int(MSG[len(event):])
                    self.pos['nidaq'][event]=n
                    if   event == 'trial start':
                        self.flags['trial']=True
                    elif event == 'trial end':
                        self.flags['trial']=False
                    elif event == 'vstim start':
                        self.flags['vstim']=True
                    elif event == 'vstim end':
                        self.flags ['vstim']=False
                    elif   event == 'acquisition start':
                        self.flags['nidaq_acquisition']=True
                        self.display()
                    elif event == 'acquisition stop':
                        self.flags['nidaq_acquisition']=False
                    elif event =='connection':
                        print ('nidaq connected!')
            for event in self.events_sp:
                if MSG[:len(event)]==event:
                    if event=='matrix':
                        M=recv_matrix()
                        print (M)
            connection.close()

            
        if not self.flags['stop']:
            Timer(0.1,self.listen).start()
        else:
            self.terminate()
            
    def terminate(self):
        self.s.close()
        print ('socket closed')
if __name__=="__main__":
    npx=npx_rt_hub()

