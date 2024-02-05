#Vitaly Lerner 2024
# Neuropixel Real Time Analysis
# TEMPO module

import argparse
import socket,struct,sys


ACTIONS=['START_PARADIGM','START_TRIAL','END_PARADIGM','END_TRIAL','SET_PARAM']

parser=argparse.ArgumentParser(description='Real Time Analysis for TEMPO+Neuropixels')
parser.add_argument('--action',type=str,help=','.join(ACTIONS))
parser.add_argument('--paradigm',type=int,help='same numbers as in TEMPO')
parser.add_argument('--paramname',type=str,help='parameter name')
parser.add_argument('--paramvalue',type=str,help='parameter value')
parser.add_argument('--outcome',type=str,help='trial outcome')
for i in range(4):
    parser.add_argument(f'--var{i}',type=double,help('var{i} value')
                    
args=parser.parse_args()
action=args.action
if not action in ACTIONS:
    
    print (f'{action} is incorrect action, see help')

#if action=='START_PARADIGM':
    
                    


ports={'TEMPO_CLIENT':10000}
def build_msg(args):
    N=[-1 for i in range(16)]
    if args.action =='START_PARADIGM':
        N[0]=1
        N[1]=args.paradigm
    elif args.action == 'STOP_PARADIGM':
        N[0]=2
    elif args.action == 'START_TRIAL':
        N[0]=3
        for i in range(4):
            try:
                x=get(args,f"var{i}")
                
    elif args.action == 'STOP_TRIAL':
        N[0]=4
        N[1]=args.outcome
"""        
# Create a TCP/IP socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect the socket to the port where the server is listening
server_address = ('128.151.171.161', ports['TEMPO_CLIENT'])
print ('connecting to %s port %s' % server_address)
s.connect(server_address)

try:
    
    for i in range(16):
        s.sendall(struct.pack("i",i*4-12))
    response = s.recv(2)
    if response==b'OK':
        print("message sent successfully")
finally:
    print ('closing socket')
    s.close()
"""
