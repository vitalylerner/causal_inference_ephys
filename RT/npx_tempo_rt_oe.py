import numpy as np
import oe_pyprocessor

import socket,struct,time
from threading import Timer,Thread



import queue


# Add additional imports here
from npx_tempo_rt_client import npx_tempo_rt_client
from npx_tempo_rt_globals import npx_tempo_rt_processes,npx_tempo_rt_globals


hub_connect=False

              

class PyProcessor:
    nsmp=0
    
    q=queue.Queue()
    
    seg_cnt=0
    
    s=None
    ntc=None

    device=None
    num_channels=0
    sampling_rate=0
    buffer_length=0
    data_buff=None
    
    flags={}
    
    def __init__(self, processor, num_channels, sample_rate):
        #pass
        """ 
        A new processor is initialized whenever the plugin settings are updated
        
        Parameters:
        processor (object): Python Processor class object used for adding events from python.
        num_channels (int): number of input channels in the selected stream.
        sample_rate (float): sample rate of the selected stream
        """
        
        self.num_channels=num_channels
        self.sample_rate=sample_rate
        self.buffer_length=int(self.sample_rate)
        self.flags['trial']=False
        self.flags['acquisition']=False
        
        if num_channels==npx_tempo_rt_globals.npx_contacts:
            self.device="npx"
            
        elif num_channels == npx_tempo_rt_globals.nidaq_channels:
            self.device="nidaq"
            
        #self.data_buff=np.zeros((self.num_channels,self.buffer_length),np.float32)
        self.seg_cnt=0
        
        print(f"[Python] {self.device} | {self.sample_rate} sps | {self.num_channels} channels")

        Timer(5,self.simulatetrial).start()
        """if hub_connect:
            self.ntc=npx_tempo_rt_client(npx_tempo_rt_processes.oe_npx,
                                         npx_tempo_rt_processes.hub)"""
        
    def simulatetrial(self):
        if self.flags['trial']:
            self.flags['trial']=False
            Timer(3,self.simulatetrial).start()
        else:
            self.flags['trial']=True
            #print ('trial start 000')
            Timer(1.5,self.simulatetrial).start()
            
    """def segmentprc(self):
        q=self.q
        
        if not q.empty():
            #print ('aaa')
            smp,data=q.get()
            #print ()
            nsmp=np.shape(data)[1]
            
            self.data_buff[:,:-nsmp]=self.data_buff[:,nsmp:]
            self.data_buff[:,-nsmp:]=data
            
            print(q.qsize())
            #if q.qsize()==2:
            #    print (np.mean(self.data_buff,axis=1))
            
        if self.flags['acquisition']:
            Timer(0.01,self.segmentprc).start()
  """
        
    def process(self, data):
        """
        Process each incoming data buffer.
        
        Parameters:
        data - N x M numpy array, where N = num_channles, M = num of samples in the buffer.
        """
        x=np.shape(data)
        nsmp=x[1]
        
        global ncores
        global Q
        
        if self.flags['trial']:
            self.cnt+=1
            procId=self.cnt%ncores
            Q[procId].put( (self.nsmp,data))
            #self.data_buff[:,:-nsmp]=self.data_buff[:,nsmp:]
            #self.data_buff[:,-nsmp:]=data[:,:]
            
            #Process(target=self.q.put,args=( (self.nsmp,data),)).start()
#            self.q.put((self.nsmp,data[::5,:]))
            
        self.nsmp+=nsmp 
        #self.data_buff[:2,-nsmp:]=data[:2,:]
        try:
            #print (f"[Python] smples since acq start: {self.cnt}")\
            pass
        except:
            print ('[Python Error]')
            #pass"""
        
    def start_acquisition(self):
        self.flags['acquisition']=True
        Timer(0.1,self.segmentprc).start()
        """ Called at start of acquisition """
        #pass
        """if hub_connect:
            time.sleep(0.5)
            self.ntc.send("ACQ_START")"""
        
    
    def stop_acquisition(self):
        """ Called when acquisition is stopped """
        self.flags['acquisition']=False
        while not self.q.empty():
            x=self.q.get()
        """if hub_connect:
            self.ntc.send("ACQ_STOP")
            time.sleep(0.5)"""


    def handle_ttl_event(self, source_node, channel, sample_number, line, state):
        """
        Handle each incoming ttl event.
        
        Parameters:
        source_node (int): id of the processor this event was generated from
        channel (str): name of the event channel
        sample_number (int): sample number of the event
        line (int): the line on which event was generated (0-255) 
        state (bool): event state True (ON) or False (OFF)
        """
        if False:
            if state:
                
                if (channel[:3])=="PXI" and (line==12):
                    if sample_number<10:
                        md='w'
                    else:
                        md='a'
                    with open('C:/npx_tempo/DEBUG/pxi.log',md) as log_pxi:
                        log_pxi.write (f'{sample_number}\n')
                    if hub_connect:
                        self.ntc.send(f"SYNC {sample_number}")
                elif (channel[:3]=='Neu') and (line==0):
                    with open('C:/npx_tempo/DEBUG/npx.log',md) as log_npx:
                        log_npx.write (f'{sample_number}\n')
                    if hub_connect:
                        self.ntc.send(f"SYNC {sample_number}")
      #  if state:
            #if source_node[:3]=='PXI':
                #if line==12:
                  #  print (f'[Python] {channel,sample_number,line}')
            #elif source_node[:3]=='Neu':
                #if line==0:
                
                 #   print (f'[Python] {channel,sample_number,line}')
        #    if source_node[:4]=="PXIe":
        #        if  line ==0:
        
       # pass

    def handle_spike(self, source_node, electrode_name, num_channels, num_samples, sample_number, sorted_id, spike_data):
        """
        Handle each incoming spike.
        
        Parameters:
        source_node (int): id of the processor this spike was generated from
        electrode_name (str): name of the electrode
        num_channels (int): number of channels associated with the electrode type
        num_samples (int): total number of samples in the spike waveform 
        sample_number (int): sample number of the spike
        sorted_id (int): the sorted ID for this spike
        spike_data (numpy array): N x M numpy array, where N = num_channels & M = num_samples (read-only).
        """
        pass
    
    def start_recording(self, recording_dir):
        """ 
        Called when recording starts

        Parameters:
        recording_dir (str): recording directory to be used by future record nodes.
        """
        pass
    
    def stop_recording(self):
        """ Called when recording stops """
        pass