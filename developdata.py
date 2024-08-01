##!/usr/bin/env python

#This is the main process of real time analysis 
# for neuropixel - tempo

import socket,struct,time,json
from threading import Timer
from npx_rt import npx_rt_globals
import numpy as np
from datetime import datetime

main_run=True

class npx_rt_hub():
    """
    Neuropixel real time hub.
    
    Processes data, events, stimuli params received
    from TEMPOW, OpenEphys, GUI
    
    Runs separately without parameters
    
    Receives data through tcpip socket
    """
    # Most events are processed through the following protocol:
    
        
    #|===================================================================|
    #| order | content  |  type  | bytes | description                   | 
    #|-------------------------------------------------------------------|
    #|   1  | procId    |  int   |  4    | process identification        |
    #|   2  |    L      |  int   |  4    | length (bytes) of the message |
    #|   3  | event,n   |  str   |  L    | event name and one integer    | 
    #|      |           |        |       | parameter separated by space  |
    #|===================================================================|    
    """
    Data reveived from npx has more complicated protocol, described further in
    the protocol functions
    """
    
    #tcpip socket for communication with the rest of the modules/processes
    s=None
    
    #status flags for internal synchronization
    flags={}
    report={}
    
    #list of all possible events that can be received from
    # nidaq branch of OpenEphys
    events={}
    events_sp={}
    events['nidaq']=['connection','trial start','vstim start',
                  'vstim end','trial end','sync',
                  'acquisition start','acquisition stop',
                  'recording start', 'recording stop']
    
    events['npx']=['connection','sync','acquisition start','acquisition stop']
    
    events_sp['npx']=['matrix']
    
    #status information, mostly used for storing sample numbers for each
    # important parameter
    pos={}
    
    
    sync_root_folder='C:/npx_tempo/SYNC/'
    sync_folder=None
    sync_file={}
    
    
    buffer=None
    buffer_cursor=0
    buffer_n0=0
    nchannels=0
    
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
        self.flags[ 'npx_connected']    = False
        self.flags['nidaq_connected']   = False
        self.flags['recording']         = False
        
        for device in ['nidaq','npx']:
            self.pos[device]={}
            for ev in self.events[device]:
              self.pos[device][ev]=-1

        self.buffer=np.zeros((npx_rt_globals.npx_rt_channels,
                            npx_rt_globals.npx_bufferlength),
                           dtype=np.float32)
        self.report['buffer_cursor']=-1
        
        Timer(1,self.listen).start()
        
    def display(self):
        """
        Temporary function for displaying the flags and metadata.
        
        GUI indicators will be used instead.
        """
        while self.flags[f'nidaq_acquisition']:
            print(self.pos['nidaq'])
            time.sleep(2)
            
    def buffer_reset(self):
        self.buffer*=0.
        self.buffer_cursor=0
        self.report['buffer_cursor']=0
        
    def buffer_insert(self,M,n0:int):
        nsmp=M.shape[1]
        if self.buffer_cursor==0:
            self.buffer_n0=n0
        if not ((self.buffer_cursor+nsmp)>self.buffer.shape[1]):
            self.buffer[:,self.buffer_cursor:self.buffer_cursor+nsmp]=M
            self.buffer_cursor+=nsmp
        else:
            overlap=nsmp-(self.buffer.shape[1]-self.buffer_cursor)
            self.buffer[:,:-overlap]=self.buffer[:,overlap:]
            self.buffer[:,-nsmp:]=M
            self.buffer_cursor=self.buffer.shape[1]
            self.buffer_n0+=overlap
         
        self.report['buffer_cursor']=self.buffer_cursor
        #print ('dbg127',self.buffer_cursor,n0,nsmp)
    def std (self.buffer,self.buffer_n0, samplenum):
        before=(samplenum-F*ms*tmebfr)-self.buffer_n0
        after=(samplenum+F*ms*tmeaftr)-self.buffer_n0
        sbfr=np.std(self.buffer[:,before:(before+tstd)])
        saftr=np.std(self.buffer[:,after:(after+tstd)])
        diff=(saftr-sbfr)/sbfr

    def listen(self):
        """Communication function."""
        
        def sync_log_start(device):
            self.sync_folder=self.sync_root_folder
            now=datetime.now()
            self.sync_file[device]=self.sync_folder+device+now.strftime("_%Y%m%d_%H%M%S.txt")
            
        def sync_log_log(device,n):
            with open(self.sync_file[device],'a') as flog:
                flog.write (f'{n}\n')

        def recv_str(l:int):
            return connection.recv(MsgLen).decode('utf-8')
        def recv_int():
            return struct.unpack("i",connection.recv(4))[0]
        
        def respond2query(query:str):
            response=''
            if query=='status':
                response=json.dumps(self.flags)
            elif query=='trial':
                response=json.dumps({'response':'trial data here'})
            elif query=='report':
                response=json.dumps(self.report)
            L=len(response)
            connection.send(struct.pack("i",L))
            connection.send(bytes(response,'utf-8'))
                
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
        #   6   |   p      |  int   |  4              |   
        #   7   |   data   |  float | 4 × rows × cols |
        #==============================================
        # * these are received prior to receiving matrix, so here 
        #   we start with row#4
            rows=recv_int()
            cols=recv_int()
            p=recv_int()
            l=rows*cols
            try: 
                x=np.reshape(list(struct.unpack("%sf"%l,connection.recv(l*4))),(rows,cols))
            except struct.error:
                x=None
            return x,p
            
            #np.reshape(list(struct.unpack("%sf"%10,m)),(2,5))
        #print (ProcID,MSG)
        
        
        def process_npx():  
            for event in self.events_sp['npx']:
                if MSG[:len(event)]==event:
                    if event=='matrix':
                        M,n0=recv_matrix()
                        
                        if self.flags['trial'] and (not M is None):
                            self.buffer_insert(M,n0)
                        #print (f'received matrix {M.shape}')
                                    
            for event in self.events['npx']:
                if MSG[:len(event)]==event:
                    n=int(MSG[len(event):])
                    self.pos['npx'][event]=n
                    if   event == 'sync':
                        sync_log_log('npx',n)
                    elif   event == 'acquisition start':
                        self.flags['npx_acquisition']=True
                        sync_log_start('npx') 
                    elif event == 'acquisition stop':
                        self.flags['npx_acquisition']=False
                    elif event =='connection':
                        self.flags['npx_connected']=True
                        #print ('npx connected!')    
                    
                    
        def process_nidaq():
            for event in self.events['nidaq']:
                if MSG[:len(event)]==event:
                    n=int(MSG[len(event):])
                    self.pos['nidaq'][event]=n
                    if   event == 'sync':
                        sync_log_log('nidaq',n)
                    elif event == 'trial start':
                        self.flags['trial']=True
                        self.buffer_reset()
                    elif event == 'trial end':
                        self.flags['trial']=False
                    elif event == 'vstim start':
                        self.flags['vstim']=True
                    elif event == 'vstim end':
                        self.flags ['vstim']=False
                    elif   event == 'acquisition start':
                        self.flags['nidaq_acquisition']=True
                        sync_log_start('nidaq')
                    elif event == 'acquisition stop':
                        self.flags['nidaq_acquisition']=False
                    elif event =='connection':
                        self.flags['nidaq_connected']=True
                    elif event == 'recording start':
                        self.flags['recording']=True
                    elif event == 'recording stop':
                        self.flags['recording']=False

        def process_tempow():
            pass
        def process_gui():
            if MSG=='stop':
                self.flags['stop']=True
                
            elif MSG=='status?':
                respond2query('status')
            
            elif MSG=='trial?':
                respond2query('trial')
            
            elif MSG=='report?':
                respond2query('report')
                
        while not self.flags['stop']:
            connection,client_address=self.s.accept()
            ProcID=recv_int()
            MsgLen=recv_int()
            MSG=recv_str(MsgLen)
            
            if ProcID==npx_rt_globals.processes.gui:
                process_gui()
            elif ProcID==npx_rt_globals.processes.oe_npx:
                process_npx()
            elif ProcID==npx_rt_globals.processes.oe_nidaq:
                process_nidaq()
            elif ProcID==npx_rt_globals.processes.tempow:
                process_tempow()
            connection.close()
        self.terminate()
            
    def terminate(self):
        self.s.close()
        print ('socket closed')
if __name__=="__main__":
    npx=npx_rt_hub()