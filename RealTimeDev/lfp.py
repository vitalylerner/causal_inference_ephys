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

a=np.fromfile('LFP.dat',dtype=np.int16)
b=np.reshape(a,(int(len(a)/C),C)).T
stimuli=pandas.read_csv(r'C:\Users\DeAngelis Lab\Desktop\Jessie\Trials.csv')
stim=stimuli[stimuli['rec']==1]
fstim=pandas.Series.to_numpy(stim['lfp in stitch'])


c=range(-F*2,F*3)
y=np.zeros((C,len(c)))
fig,ax=matplotlib.pyplot.subplots()
for j in range(C):
        y[j,:]=np.mean([b[j,int(fstim[i]-F*2):int(fstim[i]+F*3)]for i in range(len(fstim))],axis=0)
z=np.mean(y,axis=0)
y=y-z
y-=np.mean(y,axis=1)
y/=np.std(y,axis=1)
for j in range(C):    
        ynorm[j]=y[j,:]-z
        ynorm[j]-=np.mean(ynorm)
        ynorm[j]/=np.std(ynorm)
ax.plot([c]*C,y+15*j,alpha=0.3,color='k')