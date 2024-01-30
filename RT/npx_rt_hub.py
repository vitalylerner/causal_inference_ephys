##!/usr/bin/env python

#This is the main process of real time analysis 
# for neuropixel - tempo

import socket,struct,time
from threading import Timer
from npx_rt import npx_rt_globals
import numpy as np
from datetime import datetime

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
    root_folder='C:/npx_tempo/SYNC/'
    sync_folder=None
    sync_file={}
    
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
        
        def sync_log_start(device):
            self.sync_folder=self.root_folder
            now=datetime.now()
            self.sync_file[device]=self.sync_folder+device+now.strftime("_%Y%m%d_%H%M%S.txt")
            
        def sync_log_log(device):
            with open(self.sync_file[device],'a') as flog:
                flog.write (f'{n}\n')

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
        while not self.flags['stop']:
            connection,client_address=self.s.accept()
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
                            #print (f'received matrix {M.shape}')
                                        
                for event in self.npx_events:
                    if MSG[:len(event)]==event:
                        n=int(MSG[len(event):])
                        self.pos['npx'][event]=n
                        if   event == 'sync':
                            #print ('[dbg]* npx',self.pos['npx'])
                            sync_log_log('npx')
                        if   event == 'acquisition start':
                            self.flags['npx_acquisition']=True
                            sync_log_start('npx')        
                            #self.display()
                        elif event == 'acquisition stop':
                            self.flags['npx_acquisition']=False
                        elif event =='connection':
                                print ('npx connected!')    
                    
                    
                    connection.close()
                    
            elif ProcID==npx_rt_globals.processes.oe_nidaq:
                #print ('[dbg] nidaq ', MSG)
                for event in self.nidaq_events:
                    if MSG[:len(event)]==event:
                        n=int(MSG[len(event):])
                        self.pos['nidaq'][event]=n
                        if   event == 'sync':
                            sync_log_log('nidaq')
                        elif event == 'trial start':
                            print (f'trial start {n}')
                            self.flags['trial']=True
                        elif event == 'trial end':
                            self.flags['trial']=False
                        elif event == 'vstim start':
                            self.flags['vstim']=True
                            print ('vstim start')
                        elif event == 'vstim end':
                            self.flags ['vstim']=False
                        elif   event == 'acquisition start':
                            self.flags['nidaq_acquisition']=True
                            sync_log_start('nidaq')
                            #print ('[dbg] nidaq acq start! ',n)
                            #self.display()
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
        self.terminate()
            
    def terminate(self):
        self.s.close()
        print ('socket closed')
if __name__=="__main__":
    npx=npx_rt_hub()

