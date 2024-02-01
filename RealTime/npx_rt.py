"""*************************************
***      Vitaly Lerner               ***
***      2024                        *** 
*** Neuropixels real time analysis   ***
*************************************"""
import socket,struct,json
import numpy as np


class npx_rt_globals:
    tempowave_tcpip='128.151.171.161'

    npx_contacts=384
    npx_sampling_rate=30000
    npx_bufferlength=8*npx_sampling_rate
    npx_rt_channels=16
    
    
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
    """
    General class of neuropixel tcpip communication client.
    
    Inherited by npx, nidaq,tempow, gui .
    """
    
    myid=-1
    serverid=-1
    port=10000
    s=None
    def __init__(self,myid:int,serverid:int):
        self.myid=myid
        self.serverid=serverid

    def send(self,MSG):
        """Send a message, no request."""
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
        
    def request(self,query):
        """Send request and returns the response.""" 
        # protocol:
        #==============================================
        # order | send/recv | content  | type | bytes | 
        #----------------------------------------------
        #   1   |   send   | procId   |  int  |  4    |
        #   2   |   send   |  L       |  int  |  4    |
        #   3   |   send   |  query   |  str  |  L    |
        #   4   |   recv   |  L2      |  int  |  4    |
        #   5   |   recv   |  response|  str  |  L2   |
        #==============================================
        L=len(query)
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((npx_rt_globals.tempowave_tcpip,self.serverid))
        
        #1.send this client process id
        s.send(struct.pack("i",self.myid))
        #2. send number of bytes of the query
        s.send(struct.pack("i",L))
        #3.send the message
        s.send(bytes(query,'utf-8'))
        buff=s.recv(4)
        #print ('debug',buff)
        #4. receive length of the response
        L2=struct.unpack("i",buff)[0]
        #5. receive the response
        response_txt=s.recv(L2).decode('utf-8')
        try: 
            response_dict=json.loads(response_txt)
            return response_dict
        except json.JSONDecodeError:
            return response_txt
        
               
    def send_matrix(self,data,p:int=0):
        """Send 2d numpy array, no request."""
        # protocol:
        #==============================================
        # order | content  |  type  | bytes           | 
        #----------------------------------------------
        #   1   | procId   |  int   |  4              |
        #   2   |    6     |  int   |  4              |
        #   3   | "matrix" |  str   |  6              |
        #   4   |   rows   |  int   |  4              |
        #   5   |   cols   |  int   |  4              |
        #   6   |   p      |  int   |  4              |   
        #   7   |   data   |  float | 4 × rows × cols |
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
        #6. send the additional parameter
        s.send(struct.pack("i",p))
        #7. send the data
        s.send(data_bytes)
        #disconnect   
        s.close()
        
if __name__=="__main__":
    #this block is used for debugging only
 
    #test connection
    #pretend to be nidaq
    n=npx_rt_client(npx_rt_globals.processes.oe_nidaq,npx_rt_globals.processes.hub)
    
    #test sending string
    #n.send("Hello, World!")
    
    #test sending matrix 4x25
    #A=np.reshape(np.arange(100).astype(float),(4,25))-0.5
    #n.send_matrix(A)
    
    #test requesting status
    x=n.request("status")   
    