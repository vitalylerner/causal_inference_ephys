# -*- coding: utf-8 -*-
"""
This is a UI for 
npx-tempo real time analysis

"""
from npx_tempo_rt_client import npx_tempo_rt_client
from npx_tempo_rt_globals import npx_tempo_rt_processes,npx_tempo_rt_globals
from threading import Timer
import socket, struct, time

class npx_tempo_rt_gui(npx_tempo_rt_client):
    s=None
    STOP=False
    def __init__(self):
        npx_tempo_rt_client.__init__(self,npx_tempo_rt_processes.gui,npx_tempo_rt_processes.hub)
        self.s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (npx_tempo_rt_globals.tempowave_tcpip,
                          npx_tempo_rt_processes.gui) 
        self.s.bind(server_address)
        self.s.listen(1)
        self.STOP=False
        Timer(1,self.listen).start()
        
    def listen(self):
        try:
            connection,client_address=self.s.accept()
            ProcID=struct.unpack("i",connection.recv(4))[0]
            MsgLen=struct.unpack("i",connection.recv(4))[0]
            MSG=connection.recv(MsgLen).decode('utf-8')
            connection.close()
            print (ProcID,MSG)
        except OSError:
            pass
        if not self.STOP:
            Timer(0.1,self.listen).start()
        else:
            pass
            #self.terminate()
        
    
    def terminate(self):
        self.s.close()
        print ('GUI: socket closed')
        
    def stop(self):
        
        self.send("STOP")
        self.STOP=True
        self.terminate()
        
if __name__=="__main__":
    ntgui=npx_tempo_rt_gui()
    time.sleep(10)
    ntgui.stop()

