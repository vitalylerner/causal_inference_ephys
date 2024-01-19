import numpy as np
import oe_pyprocessor

import socket,struct,time
from threading import Timer

# Add additional imports here
from npx_tempo_rt_client import npx_tempo_rt_client
from npx_tempo_rt_globals import npx_tempo_rt_processes,npx_tempo_rt_globals

nContacts=npx_tempo_rt_globals.npx_contacts
srate=npx_tempo_rt_globals.sampling_rate
bufflength=npx_tempo_rt_globals.bufferlength

class PyProcessor:
    nsmp=0

    data_buff=np.zeros((nContacts,bufflength),np.double)

    s=None
    ntc=None
    socket_live=False
    
    def __init__(self, processor, num_channels, sample_rate):
        """ 
        A new processor is initialized whenever the plugin settings are updated
        
        Parameters:
        processor (object): Python Processor class object used for adding events from python.
        num_channels (int): number of input channels in the selected stream.
        sample_rate (float): sample rate of the selected stream
        """
        print("[Python] Num Channels: ", num_channels, " | Sample Rate: ", sample_rate)
        self.socket_live=False
        self.ntc=npx_tempo_rt_client(npx_tempo_rt_processes.oe_npx,
                                     npx_tempo_rt_processes.hub)
        
        # pass
    def socket_start(self):
        self.s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (npx_tempo_rt_globals.tempowave_tcpip,
                          npx_tempo_rt_processes.gui) 
        self.s.bind(server_address)
        self.s.listen(1)
        self.socket_live=True
        Timer(1,self.listen).start()
    def socket_terminate(self):
        self.socket_live=False
        self.s.close()
        
    def listen (self):
        try:
            connection,client_address=self.s.accept()
            ProcID=struct.unpack("i",connection.recv(4))[0]
            MsgLen=struct.unpack("i",connection.recv(4))[0]
            MSG=connection.recv(MsgLen).decode('utf-8')
            connection.close()
            print (ProcID,MSG)
        except OSError:
            pass
        if self.socket_live:
            Timer(0.1,self.listen).start()
        else:
            pass
            
            
    def process(self, data):
        """
        Process each incoming data buffer.
        
        Parameters:
        data - N x M numpy array, where N = num_channles, M = num of samples in the buffer.
        """
        x=np.shape(data)
        
        nsmp=x[1]
        self.nsmp+=nsmp
        self.ntc.send(f"NSMP {self.nsmp}")
        self.data_buff[:,:-nsmp]=self.data_buff[:,nsmp:]
        self.data_buff[:,-nsmp:]=data
        try:
            #print (f"""[Python] smples since acq start: {self.cnt}""")\
            pass
        except:
            print ('[Python Error]')
            #pass
        
    def start_acquisition(self):
        """ Called at start of acquisition """
        self.socket_start()
        time.sleep(0.5)
        self.ntc.send("ACQ_START")
        
    
    def stop_acquisition(self):
        """ Called when acquisition is stopped """
        self.ntc.send("ACQ_STOP")
        time.sleep(0.5)
        self.socket_terminate()
        

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
        
        if state:
            
            if (channel[:3])=="PXI" and (line==12):
                with open('C:/npx_tempo/DEBUG/pxi.log','a') as log_pxi:
                    log_pxi.write (f'{sample_number}\n')
                self.ntc.send(f"SYNC {sample_number}")
            elif (channel[:3]=='Neu') and (line==0):
                with open('C:/npx_tempo/DEBUG/npx.log','a') as log_npx:
                    log_npx.write (f'{sample_number}\n')
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