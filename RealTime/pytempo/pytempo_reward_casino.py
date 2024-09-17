#from threading import Timer
from datetime import datetime
import pandas as pd
import numpy as np
import json
#from bokeh.plotting import figure,save
#from tkinter import Tk,Label,Buton,Entry

class pytempo_reward_casino():
    flags={}
    files={}
    reward={'jackpot':0.15,'mean_':300,'std_':0.5,'min_':1.,'max_':3.,'drdn':0.8}
    last_trial=None
    folder=''
    def __init__(self,folder:str):
        self.folder=folder
        self.flags['stop']=False
        
        dtm=datetime.now()
        
        self.files['log']=self.folder+f'Reward_{(dtm.year-2000):02d}{dtm.month:02d}{dtm.day:02d}.csv'
        self.files['params']=self.folder+'reward.tpo'
        self.files['settings']=self.folder+'reward_settings.txt'

        
    def export_params(self,r):
        with open(self.files['params'],'w') as f:
            for k in list(r.keys()):
                P= f'{k} = {r[k]};\n'
                f.write(P)

    def adjust_reward(self,ntrials:int,tot_reward:int):
        with open(self.files['settings']) as jset:
            r=json.load(jset)
        for k in r.keys():
            r[k]=float(r[k])
        self.reward['mean']=int(r['mean_']+ntrials*r['drdn'])
        self.reward['std']=int(r['std_']*self.reward['mean'])
        self.reward['min']=int(r['min_']*self.reward['mean'])
        self.reward['max']=int(r['max_']*self.reward['mean'])
        self.reward['jackpot']=r['jackpot']
        

    def roll(self)->dict:
        bExists=True
        try:
            D=pd.read_csv(self.files['log'])
            D.columns=['hour','minute','second','tot_reward']
            d=D.iloc[-1]
        except FileNotFoundError:
            bExists=False
        except:
            bExists=False
        r={'reward_time_1':-1,'reward_time_2':-1,'reward_interval':-1,'reward_jackpot_start':-1}
        if bExists:
            
            dt_now=datetime.now()
            
            #print (D)
            
            dt_last=datetime(dt_now.year,dt_now.month,dt_now.day,d.hour,d.minute,d.second)
            dt_delta=dt_now-dt_last
            dt_delta=dt_delta.total_seconds()

            new_reward= not (dt_last==self.last_trial)
                
            if new_reward:
                self.adjust_reward(len(D),d.tot_reward)
                self.last_trial=dt_last
                r={}
                if np.random.rand()<self.reward['jackpot']:
                    r['reward_jackpot_start']=1
                    r['reward_time_1']=self.reward['mean']
                    r['reward_time_2']=0
                    r['reward_interval']=int(self.reward['mean']*0.5)
                else:
                    r['reward_jackpot_start']=0
                    r_t=np.random.randn()*self.reward['std']+self.reward['mean']
                    r_t=min([r_t,self.reward['max']])
                    r_t=max([r_t,self.reward['min']])
                    r_t=int(r_t)
                    r['reward_time_1']=r_t
                    r['reward_time_2']=0
                    r['reward_interval']=0
                self.export_params(r)
        return r
    
if __name__=="__main__":
    
    print ("don't run this file directly")

    
    
