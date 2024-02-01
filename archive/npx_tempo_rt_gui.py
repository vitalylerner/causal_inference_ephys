# -*- coding: utf-8 -*-
"""
This is a prototype client for communicating with the 
npx-tempo rt analysis hub
"""
import socket,struct

class npx_tempo_proc_e:
    GUI=101
    TEMPOCLIENT=102
    OE_AP=103
    OE_PXI=104
    
class npx_tempo_client:
    myid=-1
    tempowave="128.151.171.161"
    port=10000
    proc={'TEMPO_CLIENT':102,'OE_AP':103,'OE_PXI':104,'GUI':101}
    def __init__(self,id:int,tempowave:str='128.151.171.161'):
        self.myid=id
        self.tempowave=tempowave
    def send(self,MSG):
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((self.tempowave,self.port))
        MSGl=len(MSG)
        s.send(struct.pack("i",self.myid))
        s.send(struct.pack("i",MSGl))
        s.send(bytes(MSG,'utf-8'))
        s.close()

