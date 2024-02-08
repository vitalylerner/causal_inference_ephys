##!/usr/bin/env python

#This is the main process of real time analysis 
# for neuropixel - tempo

import socket,struct

ports={'TEMPO_CLIENT':10000,'OE_AP':10001,'OE_PXI':10002,'GUI':10003}
proc={'TEMPO_CLIENT':102,'OE_AP':103,'OE_PXI':104,'GUI':101}
TEMPOWAVE_TCPIP='128.151.171.161'

main_run=True

def msg_parse(ProcID:int,MSG:str):
    if ProcID==proc['GUI']:
        if MSG=='STOP':
            main_run=False
    
if __name__=="__main__":
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (TEMPOWAVE_TCPIP, 10000)
    s.bind(server_address)
    s.listen(1)
    while main_run:
        connection,client_address=s.accept()
        print (client_address)
        ProcID=struct.unpack("i",connection.recv(4))[0]
        MsgLen=struct.unpack("i",connection.recv(4))[0]
        MSG=str(connection.recv(MsgLen))
        msg_parse(ProcID,MSG)
        connection.close()
    s.close()
    print ('this is the end')