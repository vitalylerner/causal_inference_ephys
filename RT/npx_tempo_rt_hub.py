##!/usr/bin/env python

#This is the main process of real time analysis 
# for neuropixel - tempo

import socket,struct
from threading import Timer
from npx_tempo_rt_globals import npx_tempo_rt_processes,npx_tempo_rt_globals
from npx_tempo_rt_client import npx_tempo_rt_client



main_run=True

class npx_tempo_rt_hub():
    stop=False
    s=None
    
    c_nidaq=None
    c_npx  =None
    status_oe=False
    
    def ping_openephys(self):
        try:
            self.c_npx.send("ping")
            self.status_oe=True
        except:
            print ('ping not successful')
            self.status_oe=False
            if not self.stop:
                Timer(1,self.ping_openephys).start()
            
    def __init__(self):
        self.s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (npx_tempo_rt_globals.tempowave_tcpip,
                          npx_tempo_rt_processes.hub) 
        self.s.bind(server_address)
        self.s.listen(1)
        self.stop=False
        #self.c_nidaq=npx_tempo_rt_client(npx_tempo_rt_processes.hub, npx_tempo_rt_processes.oe_nidaq)
        self.c_npx  =npx_tempo_rt_client(npx_tempo_rt_processes.hub, npx_tempo_rt_processes.gui)
        
        Timer(1,self.listen).start()
        Timer(5,self.ping_openephys).start()
    
    def terminate(self):
        self.s.close()
        print ('socket closed')
        
    def listen(self):
        connection,client_address=self.s.accept()
        ProcID=struct.unpack("i",connection.recv(4))[0]
        MsgLen=struct.unpack("i",connection.recv(4))[0]
        MSG=connection.recv(MsgLen).decode('utf-8')
        connection.close()
        print (ProcID,MSG)
        if ProcID==npx_tempo_rt_processes.gui:
            
            if MSG=='STOP':
                print('aaa',MSG)
                self.stop=True
        elif ProcID==npx_tempo_rt_processes.oe_npx:
            print ('npx', MSG)
        elif ProcID==npx_tempo_rt_processes.oe_nidaq:
            print ('nidaq',MSG)
            
        if not self.stop:
            Timer(0.1,self.listen).start()
        else:
            self.terminate()

if __name__=="__main__":
    npx=npx_tempo_rt_hub()

