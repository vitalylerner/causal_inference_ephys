class npx_tempo_rt_processes:
    hub     = 10000     # main hub of rt analysis,  TEMPOWAVE
    gui     = 10001     # GUI,                      TEMPOWAVE
    tempow  = 10002     # TempoW,                   TEMPOClient 
    oe_npx  = 10003     # OpenEphys:neuropixel,     TEMPOWAVE
    oe_nidaq= 10004     # OpenEphys:nidaqmx,        TEMPOWAVE
    
class npx_tempo_rt_globals:
    tempowave_tcpip='128.151.171.161'

    npx_contacts=384
    sampling_rate=30000
    bufferlength=5*sampling_rate
    
    
class npx_tempo_msg:
    STOP="STOP"
    