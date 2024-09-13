import numpy as np
import oe_pyprocessor
import shelve
import socket,struct,time

#import queue


# Add additional imports here
from npx_rt import npx_rt_client,npx_rt_globals

hub_connect=True
             

class PyProcessor:
    nsmp=0
    
    #q=queue.Queue()
    
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
        #self.buffer_length=int(self.sample_rate)
        
        
        self.flags['trial']=False
        self.flags['acquisition']=False
        
        if num_channels==npx_rt_globals.npx_contacts:
            self.device="npx"
        else:
        #elif num_channels == npx_rt_globals.nidaq_channels:
            self.device="nidaq"
            
        #self.data_buff=np.zeros((self.num_channels,self.buffer_length),np.float32)
        self.seg_cnt=0
        
        print(f"[python] {self.device} | {self.sample_rate} sps | {self.num_channels} channels")

        #Timer(10,self.simulatetrial).start()
        if hub_connect:
            if self.device=='npx':
                self.ntc=npx_rt_client(npx_rt_globals.processes.oe_npx,
                                         npx_rt_globals.processes.hub)
                
            elif self.device=='nidaq':
                self.ntc=npx_rt_client(npx_rt_globals.processes.oe_nidaq,
                                         npx_rt_globals.processes.hub)
            self.ntc.send('connection 1')
            
    def simulatetrial(self):
        while self.flags['acquisition']:
            time.sleep(5)
            self.flags['trial']=True
            time.sleep(2)
            self.flags['trial']=False
            

            

        
    def process(self, data):
        """
        Process each incoming data buffer.
        
        Parameters:
        data - N x M numpy array, where N = num_channles, M = num of samples in the buffer.
        """
        infile=shelve.open('C:/npx_tempo/RealTime/myfile')
        start=infile["start"]
        skip=infile["skip"]
        downsample=infile["downsample"]
        if npx_rt_globals.send_data and (self.device=='npx'):
            x=np.shape(data)
            nsmp=x[1]

            if self.flags['trial']:
                self.cnt+=1
    
            self.nsmp+=nsmp 
            
            M=data[start:start+skip*(npx_rt_globals.npx_rt_channels):skip,::downsample]
            if hub_connect:
                self.ntc.send_matrix(M)

        
    def start_acquisition(self):
        """ Called at start of acquisition """
        self.flags['acquisition']=True
        """if self.device=='nidaq':
            self.simulatetrial()"""
        if hub_connect:
            self.ntc.send("acquisition start 1")
        
    
    def stop_acquisition(self):
        """ Called when acquisition is stopped """
        self.flags['acquisition']=False
        #while not self.q.empty():
        #    x=self.q.get()
        """if hub_connect:
            self.ntc.send("acquisition stop 1")"""
            


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
        
        if state: #if the event is rising edge of some TTL
            # various flags
            # the device is nidaq
            is_nidaq=self.device=='nidaq'
            # the event is sync in nidaq
            is_nidaq_sync= is_nidaq and (line==npx_rt_globals.nidaq_lines['sync']) 
            # the devoce is npx
            is_npx  = self.device=='npx'
            # the event is sync
            is_sync = is_nidaq_sync or is_npx
            if is_sync:                   
                if hub_connect:
                    self.ntc.send(f"sync {sample_number}")
                    
                    
            elif is_nidaq:
                #print (f'[python] nidaq ttl: {line} {sample_number}')
                lines=npx_rt_globals.nidaq_lines
                
                l=[k for k in lines.keys() if lines[k]==line]
                if (len(l)==1) and (not (line==7)):
                    print (f"{l[0]} {sample_number}")
                    if hub_connect:
                        self.ntc.send(f"{l[0]} {sample_number}")
                    


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
        if self.device=='nidaq':
            if hub_connect:
                self.ntc.send("recording start 1")
    
    def stop_recording(self):
        """ Called when recording stops """
        if self.device=='nidaq':
            if hub_connect:
                self.ntc.send("recording stop 1")