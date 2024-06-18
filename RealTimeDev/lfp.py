import numpy as np
from matplotlib.pyplot import*
import pandas

ms=10**-3
F=2500
C=384
basestart=1000 #in ms before stimuli
baseend=500 #ms before stimuli
steadystart=500 #ms after stimuli
steadyend=3500  #ms after stimuli
numtraces=30

a=np.fromfile("C:\\Users\\DeAngelis Lab\\Desktop\\Jessie\\LFP.dat",dtype=np.int16)
b=np.reshape(a,(int(len(a)/C),C)).T
stimuli=pandas.read_csv(r'C:\Users\DeAngelis Lab\Desktop\Jessie\Trials.csv')
stim=stimuli[stimuli['rec']==1]
fstim=pandas.Series.to_numpy(stim['lfp in stitch'])
pos=pandas.DataFrame.to_numpy(pandas.read_csv("C:\\Users\\DeAngelis Lab\\Desktop\\Jessie\\m42c539r1_trial_conditions.csv"))

_,unique=np.unique(pos,axis=0,return_index=True)
unique1=np.sort(unique)
pos1=[]
for i in unique1:
     mask=np.where((pos==pos[i]).all(axis=1))
     pos1.append(mask)

r=np.zeros((C,len(c)))
for j in range(C):
        r[j,:]=np.mean([b[j,int(fstim[i]-F*2):int(fstim[i]+F*3)]for i in pos1[0]],axis=0)      

c=range(-F*2,F*3)
y=np.zeros((C,len(c)))
fig,ax=matplotlib.pyplot.subplots()
for j in range(C):
        y[j,:]=np.mean([b[j,int(fstim[i]-F*2):int(fstim[i]+F*3)]for i in range(len(fstim))],axis=0)
z=np.mean(y,axis=0)
y=y-z
for j in range(C):  
    y[j,:]-=np.mean(y[j,:])
    y[j,:]-=np.std(y[j])
    ax.plot(c,y[j,:]+100*j,alpha=0.3,color='k')
matplotlib.pyplot.show()

