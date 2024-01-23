##!/usr/bin/env python

#This is the main process of real time analysis 
# for neuropixel - tempo

import socket,struct
from threading import Timer
from npx_tempo_rt_globals import npx_tempo_rt_processes,npx_tempo_rt_globals



main_run=True

class npx_tempo_rt_hub():
    stop=False
    s=None
    events=['trial start','vstim start','vstim end','trial end','sync']
    pos={}
    flags={}
    def __init__(self):
        self.s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (npx_tempo_rt_globals.tempowave_tcpip,
                          npx_tempo_rt_processes.hub) 
        self.s.bind(server_address)
        self.s.listen(1)
        
        self.flags['stop']   = False
        self.flags['trial']  = False
        self.flags['vstim']  = False
        
        
        
        for dev in ['nidaq','npx']:
            self.pos[dev]={}
            for ev in self.events:
              self.pos[dev][ev]=-1

        
        Timer(1,self.listen).start()

    def listen(self):
        connection,client_address=self.s.accept()
        ProcID=struct.unpack("i",connection.recv(4))[0]
        MsgLen=struct.unpack("i",connection.recv(4))[0]
        MSG=connection.recv(MsgLen).decode('utf-8')
        
        #print (ProcID,MSG)
        if ProcID==npx_tempo_rt_processes.gui:
            
            if MSG=='STOP':
                self.stop=True
                connection.close()
                
        elif ProcID==npx_tempo_rt_processes.oe_npx:
            print ('npx', MSG)
            if MSG[:4]=='SYNC':
                sync_npx=int(MSG[5:])
                
                
                connection.close()
                
        elif ProcID==npx_tempo_rt_processes.oe_nidaq:
            for event in self.events:
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
            connection.close()

            
        if not self.flags['stop']:
            Timer(0.1,self.listen).start()
        else:
            self.terminate()
            
    def terminate(self):
        self.s.close()
        print ('socket closed')
if __name__=="__main__":
    npx=npx_tempo_rt_hub()

