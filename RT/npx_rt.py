"""*************************************
***      Vitaly Lerner               ***
***      2024                        *** 
*** Neuropixels real time analysis   ***
*************************************"""
import socket,struct
import numpy as np


class npx_rt_globals:
    tempowave_tcpip='128.151.171.161'

    npx_contacts=384
    npx_sampling_rate=30000
    npx_bufferlength=5*npx_sampling_rate
    
    nidaq_channels=8
    nidaq_sampling_rate=40000
    nidaq_bufferlength=5*nidaq_sampling_rate
    class processes:
        hub     = 10000     # main hub of rt analysis,  TEMPOWAVE
        gui     = 10001     # GUI,                      TEMPOWAVE
        tempow  = 10002     # TempoW,                   TEMPOClient 
        oe_npx  = 10003     # OpenEphys:neuropixel,     TEMPOWAVE
        oe_nidaq= 10004     # OpenEphys:nidaqmx,        TEMPOWAVE
    
    nidaq_lines={'trial start':0,
                 'vstim start':1,
                 'vstim end'  :2,
                 'trial end'  :3,
                 'success'    :4,
                 'frame'      :7,
                 'sync'       :12}


class npx_rt_client:
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
        s.connect((npx_rt_globals.tempowave_tcpip,self.serverid))
        #1. send this client process id
        s.send(struct.pack("i",self.myid))
        #2. send number of bytes of the message
        s.send(struct.pack("i",MSGl))
        #3.send the message
        s.send(bytes(MSG,'utf-8'))
        s.close()
        
    def send_matrix(self,data):
        #sends 2d numpy array:
        # protocol:
        #==============================================
        # order | content  |  type  | bytes           | 
        #----------------------------------------------
        #   1   | procId   |  int   |  4              |
        #   2   |    6     |  int   |  4              |
        #   3   | "matrix" |  str   |  6              |
        #   4   |   rows   |  int   |  4              |
        #   5   |   cols   |  int   |  4              |
        #   6   |   data   |  float | 4 × rows × cols |
        #==============================================

        rows=data.shape[0]
        cols=data.shape[1]
        
        data_flat=list(np.reshape(data,(data.shape[0]*data.shape[1])))
        data_len=len(data_flat)
        data_bytes=struct.pack('%sf' % data_len, *data_flat)
        head=bytes('matrix','utf-8')
        head_len=len(head)
        
        #connect
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((npx_rt_globals.tempowave_tcpip,self.serverid))
        
        #1. send this client process id
        s.send(struct.pack("i",self.myid))     
        #2. send number of bytes of the message "matrix" 
        s.send(struct.pack("i",head_len))
        #3. send the message "matrix"
        s.send(head)
        #4. send number of rows 
        s.send(struct.pack("i",rows))
        #5. send number of columns
        s.send(struct.pack("i",cols))
        #6. send the data
        s.send(data_bytes)
        #disconnect   
        s.close()
        
if __name__=="__main__":
    n=npx_rt_client(npx_rt_globals.processes.oe_nidaq,npx_rt_globals.processes.hub)
    n.send("Hello, World!")
    #n.send("Hello2")
    A=np.reshape(np.arange(100).astype(float),(4,25))-0.5
    
    n.send_matrix(A)
    #n2=npx_tempo_rt_client(npx_tempo_rt_processes.gui)
    #n2.send("STOP")    