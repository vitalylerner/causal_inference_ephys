# -*- coding: utf-8 -*-
"""
This is a prototype client for communicating with the 
npx-tempo rt analysis hub
"""
import socket,struct
from npx_tempo_rt_globals import npx_tempo_rt_processes,npx_tempo_rt_globals
import numpy as np
    
class npx_tempo_rt_client:
    myid=-1
    serverid=-1
    port=10000
    s=None
    def __init__(self,myid:int,serverid:int):
        self.myid=myid
        self.serverid=serverid
        
    def send(self,MSG):
        MSGl=len(MSG)
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((npx_tempo_rt_globals.tempowave_tcpip,self.serverid))
        s.send(struct.pack("i",self.myid))
        s.send(struct.pack("i",MSGl))
        s.send(bytes(MSG,'utf-8'))
        s.close()
    def send_matrix(self,data):
        rows=data.shape[0]
        data_flat=list(np.reshape(data,(data.shape[0]*data.shape[1])))
        data_len=len(data_flat)
        data_bytes=struct.pack('%sf' % data_len, *data_flat)
        
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((npx_tempo_rt_globals.tempowave_tcpip,self.serverid))
        s.send(struct.pack("i",self.myid))
        
        msg_head=bytes('MATRIX ','utf-8')
        msg_rows=struct.pack("f",rows)
        msg=msg_head+msg_rows+data_bytes
        msg_len=len(msg)
        s.send(struct.pack("i",msg_len))
        s.send(msg)
        s.close()
        
if __name__=="__main__":
    n=npx_tempo_rt_client(npx_tempo_rt_processes.oe_npx,npx_tempo_rt_processes.hub)
    n.send("Hello, World!")
    #n.send("Hello2")
    data=np.random.rand(8,20).astype(np.float32)
    
    data=list(np.reshape(data,(data.shape[0]*data.shape[1])))
    n.send_matrix(data)
    #n2=npx_tempo_rt_client(npx_tempo_rt_processes.gui)
    #n2.send("STOP")